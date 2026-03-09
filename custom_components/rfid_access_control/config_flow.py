"""Config flow for RFID Access Control."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, CONF_DEVICE_ID, SUPPORTED_MODELS

_LOGGER = logging.getLogger(__name__)


async def async_get_available_keypads(hass: HomeAssistant) -> dict:
    """Get available Zigbee keypad devices."""
    try:
        dev_reg = dr.async_get(hass)
        keypads = {}
        
        for device in dev_reg.devices.values():
            if not device:
                continue
            
            # Check if device matches supported models
            try:
                if device.identifiers:
                    for _, identifier in device.identifiers:
                        for model in SUPPORTED_MODELS.keys():
                            if model in identifier:
                                device_name = device.name or device.model or "Unknown Keypad"
                                keypads[device.id] = {
                                    "name": device_name,
                                    "model": device.model or model,
                                    "manufacturer": device.manufacturer,
                                }
                                break
            except (AttributeError, TypeError):
                continue
        
        return keypads
    except Exception as e:
        _LOGGER.error(f"Error getting keypads: {e}")
        return {}


class RFIDAccessControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RFID Access Control."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                # Validate device exists
                device_id = user_input.get(CONF_DEVICE_ID)
                if device_id:
                    await self.async_set_unique_id(device_id)
                    self._abort_if_unique_id_configured()
                    
                    return self.async_create_entry(
                        title=f"RFID Access Control - {device_id[:8]}",
                        data=user_input,
                    )
            except Exception as e:
                _LOGGER.error(f"Error creating entry: {e}")
                errors["base"] = "unknown"

        # Get available keypads
        try:
            keypads = await async_get_available_keypads(self.hass)
        except Exception as e:
            _LOGGER.error(f"Error getting keypads: {e}")
            keypads = {}

        if not keypads:
            return self.async_abort(reason="no_devices")

        # Build form schema
        try:
            schema = vol.Schema({
                vol.Required(CONF_DEVICE_ID): vol.In({
                    device_id: f"{info['name']} ({info.get('model', 'Unknown')})"
                    for device_id, info in keypads.items()
                }),
            })
        except Exception as e:
            _LOGGER.error(f"Error building schema: {e}")
            return self.async_abort(reason="unknown_error")

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "num_devices": str(len(keypads)),
            },
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_data)
