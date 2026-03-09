"""RFID Access Control integration for Home Assistant."""
import logging
from pathlib import Path
import json

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    SERVICE_ADD_USER,
    SERVICE_REMOVE_USER,
    SERVICE_UPDATE_USER,
    SERVICE_ADD_ACTION,
    SERVICE_REMOVE_ACTION,
    SERVICE_VALIDATE_ACCESS,
    SERVICE_LIST_USERS,
    ATTR_USER_ID,
    ATTR_USER_NAME,
    ATTR_USER_PIN,
    ATTR_USER_RFID,
    ATTR_USER_ACTIONS,
    ATTR_ACTION_ENTITY,
    ATTR_ACTION_SERVICE,
    ATTR_ACTION_DATA,
    EVENT_ACCESS_GRANTED,
    EVENT_ACCESS_DENIED,
    EVENT_USER_ADDED,
    EVENT_USER_REMOVED,
    DATA_COORDINATOR,
    DATA_USERS_DB,
    MIN_PIN_LENGTH,
    MAX_PIN_LENGTH,
    MIN_RFID_LENGTH,
)
from .models import AccessUser, AccessAction, AccessDatabase

_LOGGER = logging.getLogger(__name__)

PLATFORMS = []

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({})
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up RFID Access Control component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RFID Access Control from a config entry."""
    try:
        device_id = entry.data.get(CONF_DEVICE_ID)
        
        if not device_id:
            _LOGGER.error("No device_id provided in config entry")
            return False
        
        # Initialize database
        db = AccessDatabase()
        
        # Create config directory
        config_dir = Path(hass.config.config_dir) / DOMAIN
        
        def create_dir():
            config_dir.mkdir(parents=True, exist_ok=True)
        
        await hass.async_add_executor_job(create_dir)
        
        # Load persisted data if exists
        store_path = config_dir / f"{device_id}.json"
        
        def load_db():
            if store_path.exists():
                try:
                    content = store_path.read_text()
                    data = json.loads(content)
                    db.from_dict(data)
                    return len(db.users)
                except Exception as e:
                    _LOGGER.warning(f"Failed to load database: {e}")
                    return 0
            return 0
        
        user_count = await hass.async_add_executor_job(load_db)
        if user_count > 0:
            _LOGGER.info(f"Loaded {user_count} users from persistent storage")
        
        # Store data
        hass.data[DOMAIN][entry.entry_id] = {
            DATA_COORDINATOR: device_id,
            DATA_USERS_DB: db,
            "store_path": store_path,
        }
        
        # Register services
        async def handle_add_user(call: ServiceCall) -> None:
            """Add a new user."""
            try:
                data = call.data
                pin = data.get(ATTR_USER_PIN, "")
                rfid = data.get(ATTR_USER_RFID, "")
                
                if pin and (len(pin) < MIN_PIN_LENGTH or len(pin) > MAX_PIN_LENGTH):
                    _LOGGER.error(f"PIN length must be between {MIN_PIN_LENGTH} and {MAX_PIN_LENGTH}")
                    return
                
                if rfid and len(rfid) < MIN_RFID_LENGTH:
                    _LOGGER.error(f"RFID must be at least {MIN_RFID_LENGTH} characters")
                    return
                
                user = AccessUser(
                    user_id=data.get(ATTR_USER_ID, ""),
                    user_name=data.get(ATTR_USER_NAME, ""),
                    pin=pin,
                    rfid=rfid,
                )
                
                if db.add_user(user):
                    await _save_database(hass, store_path, db)
                    hass.bus.async_fire(EVENT_USER_ADDED, {
                        ATTR_USER_ID: user.user_id,
                        ATTR_USER_NAME: user.user_name,
                    })
                    _LOGGER.info(f"User added: {user.user_name}")
                else:
                    _LOGGER.error(f"Failed to add user: {user.user_id} already exists")
            except Exception as e:
                _LOGGER.error(f"Error in add_user: {e}")
        
        async def handle_remove_user(call: ServiceCall) -> None:
            """Remove a user."""
            try:
                user_id = call.data.get(ATTR_USER_ID)
                
                if db.remove_user(user_id):
                    await _save_database(hass, store_path, db)
                    hass.bus.async_fire(EVENT_USER_REMOVED, {
                        ATTR_USER_ID: user_id,
                    })
                    _LOGGER.info(f"User removed: {user_id}")
                else:
                    _LOGGER.error(f"User not found: {user_id}")
            except Exception as e:
                _LOGGER.error(f"Error in remove_user: {e}")
        
        async def handle_update_user(call: ServiceCall) -> None:
            """Update user information."""
            try:
                user_id = call.data.get(ATTR_USER_ID)
                user_data = {
                    k: v for k, v in call.data.items()
                    if k in ["user_name", "pin", "rfid", "enabled"]
                }
                
                if db.update_user(user_id, user_data):
                    await _save_database(hass, store_path, db)
                    _LOGGER.info(f"User updated: {user_id}")
                else:
                    _LOGGER.error(f"User not found: {user_id}")
            except Exception as e:
                _LOGGER.error(f"Error in update_user: {e}")
        
        async def handle_add_action(call: ServiceCall) -> None:
            """Add an action to a user."""
            try:
                user_id = call.data.get(ATTR_USER_ID)
                user = db.get_user(user_id)
                
                if not user:
                    _LOGGER.error(f"User not found: {user_id}")
                    return
                
                action = AccessAction(
                    entity_id=call.data.get(ATTR_ACTION_ENTITY, ""),
                    service=call.data.get(ATTR_ACTION_SERVICE, ""),
                    service_data=call.data.get(ATTR_ACTION_DATA, {}),
                    action_name=call.data.get("action_name", ""),
                )
                
                user.actions.append(action)
                await _save_database(hass, store_path, db)
                _LOGGER.info(f"Action added to user: {user_id}")
            except Exception as e:
                _LOGGER.error(f"Error in add_action: {e}")
        
        async def handle_remove_action(call: ServiceCall) -> None:
            """Remove an action from a user."""
            try:
                user_id = call.data.get(ATTR_USER_ID)
                action_name = call.data.get("action_name", "")
                
                user = db.get_user(user_id)
                if not user:
                    _LOGGER.error(f"User not found: {user_id}")
                    return
                
                original_count = len(user.actions)
                user.actions = [a for a in user.actions if a.action_name != action_name]
                
                if len(user.actions) < original_count:
                    await _save_database(hass, store_path, db)
                    _LOGGER.info(f"Action removed from user: {user_id}")
                else:
                    _LOGGER.error(f"Action not found: {action_name}")
            except Exception as e:
                _LOGGER.error(f"Error in remove_action: {e}")
        
        async def handle_validate_access(call: ServiceCall) -> None:
            """Validate user access and execute actions."""
            try:
                pin = call.data.get(ATTR_USER_PIN, "")
                rfid = call.data.get(ATTR_USER_RFID, "")
                
                user = db.find_user_by_credentials(pin=pin, rfid=rfid)
                
                if user:
                    user.record_access()
                    await _save_database(hass, store_path, db)
                    
                    hass.bus.async_fire(EVENT_ACCESS_GRANTED, {
                        ATTR_USER_ID: user.user_id,
                        ATTR_USER_NAME: user.user_name,
                    })
                    
                    for action in user.actions:
                        try:
                            service_parts = action.service.split(".")
                            if len(service_parts) == 2:
                                await hass.services.async_call(
                                    service_parts[0],
                                    service_parts[1],
                                    action.service_data,
                                )
                                _LOGGER.info(f"Action executed for {user.user_name}: {action.action_name}")
                        except Exception as e:
                            _LOGGER.error(f"Failed to execute action: {e}")
                    
                    _LOGGER.info(f"Access granted: {user.user_name}")
                else:
                    hass.bus.async_fire(EVENT_ACCESS_DENIED, {
                        "pin": "***" if pin else "",
                        "rfid": rfid[-4:] if rfid else "",
                    })
                    _LOGGER.warning("Access denied - Invalid credentials")
            except Exception as e:
                _LOGGER.error(f"Error in validate_access: {e}")
        
        def handle_list_users(call: ServiceCall) -> None:
            """Return list of all users."""
            users_data = [user.to_dict() for user in db.get_all_users()]
            _LOGGER.info(f"Listed {len(users_data)} users")
            hass.data[DOMAIN][entry.entry_id]["last_users"] = users_data
        
        # Register all services
        for service_name, handler in [
            (SERVICE_ADD_USER, handle_add_user),
            (SERVICE_REMOVE_USER, handle_remove_user),
            (SERVICE_UPDATE_USER, handle_update_user),
            (SERVICE_ADD_ACTION, handle_add_action),
            (SERVICE_REMOVE_ACTION, handle_remove_action),
            (SERVICE_VALIDATE_ACCESS, handle_validate_access),
            (SERVICE_LIST_USERS, handle_list_users),
        ]:
            hass.services.async_register(DOMAIN, service_name, handler)
        
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        
        _LOGGER.info(f"RFID Access Control set up for device: {device_id}")
        return True
        
    except Exception as e:
        _LOGGER.error(f"Error setting up RFID Access Control: {e}", exc_info=True)
        return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    try:
        if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
            hass.data[DOMAIN].pop(entry.entry_id)
        return unload_ok
    except Exception as e:
        _LOGGER.error(f"Error unloading entry: {e}")
        return False


async def _save_database(hass: HomeAssistant, store_path: Path, db: AccessDatabase):
    """Save database to file."""
    try:
        def save():
            store_path.parent.mkdir(parents=True, exist_ok=True)
            store_path.write_text(json.dumps(db.to_dict(), indent=2))
        
        await hass.async_add_executor_job(save)
    except Exception as e:
        _LOGGER.error(f"Failed to save database: {e}")
