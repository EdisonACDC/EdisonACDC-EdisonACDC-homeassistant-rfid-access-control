"""RFID Access Control integration for Home Assistant."""
import logging
from pathlib import Path

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
    device_id = entry.data.get(CONF_DEVICE_ID)
    
    # Initialize database
    db = AccessDatabase()
    
    # Load persisted data if exists
    store_path = Path(hass.config.config_dir) / DOMAIN / f"{device_id}.json"
    if await hass.async_add_executor_job(store_path.exists):
        try:
            import json
            content = await hass.async_add_executor_job(store_path.read_text)
            data = json.loads(content)
            db.from_dict(data)
            _LOGGER.info(f"Loaded {len(db.users)} users from persistent storage")
        except Exception as e:
            _LOGGER.error(f"Failed to load persistent data: {e}")
    
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_COORDINATOR: device_id,
        DATA_USERS_DB: db,
        "store_path": store_path,
    }
    
    # Register services
    async def handle_add_user(call: ServiceCall) -> None:
        """Add a new user."""
        data = call.data
        
        # Validate inputs
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
    
    async def handle_remove_user(call: ServiceCall) -> None:
        """Remove a user."""
        user_id = call.data.get(ATTR_USER_ID)
        
        if db.remove_user(user_id):
            await _save_database(hass, store_path, db)
            hass.bus.async_fire(EVENT_USER_REMOVED, {
                ATTR_USER_ID: user_id,
            })
            _LOGGER.info(f"User removed: {user_id}")
        else:
            _LOGGER.error(f"User not found: {user_id}")
    
    async def handle_update_user(call: ServiceCall) -> None:
        """Update user information."""
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
    
    async def handle_add_action(call: ServiceCall) -> None:
        """Add an action to a user."""
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
    
    async def handle_remove_action(call: ServiceCall) -> None:
        """Remove an action from a user."""
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
    
    async def handle_validate_access(call: ServiceCall) -> None:
        """Validate user access and execute actions."""
        pin = call.data.get(ATTR_USER_PIN, "")
        rfid = call.data.get(ATTR_USER_RFID, "")
        
        user = db.find_user_by_credentials(pin=pin, rfid=rfid)
        
        if user:
            # Record access
            user.record_access()
            await _save_database(hass, store_path, db)
            
            # Fire access granted event
            hass.bus.async_fire(EVENT_ACCESS_GRANTED, {
                ATTR_USER_ID: user.user_id,
                ATTR_USER_NAME: user.user_name,
            })
            
            # Execute user actions
            for action in user.actions:
                try:
                    await hass.services.async_call(
                        action.service.split(".")[0],
                        action.service.split(".")[1],
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
            _LOGGER.warning(f"Access denied - Invalid credentials")
    
    # Register all services
    for service_name, handler in [
        (SERVICE_ADD_USER, handle_add_user),
        (SERVICE_REMOVE_USER, handle_remove_user),
        (SERVICE_UPDATE_USER, handle_update_user),
        (SERVICE_ADD_ACTION, handle_add_action),
        (SERVICE_REMOVE_ACTION, handle_remove_action),
        (SERVICE_VALIDATE_ACCESS, handle_validate_access),
    ]:
        hass.services.async_register(DOMAIN, service_name, handler)
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


async def _save_database(hass: HomeAssistant, store_path: Path, db: AccessDatabase):
    """Save database to file."""
    try:
        import json
        store_path.parent.mkdir(parents=True, exist_ok=True)
        
        def save():
            store_path.write_text(json.dumps(db.to_dict(), indent=2))
        
        await hass.async_add_executor_job(save)
    except Exception as e:
        _LOGGER.error(f"Failed to save database: {e}")
