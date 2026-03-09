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


class RFIDAccessControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for RFID Access Control."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            device_id = user_input.get(CONF_DEVICE_ID, "").strip()
            
            if not device_id:
                errors["base"] = "invalid_device"
            else:
                try:
                    await self.async_set_unique_id(device_id)
                    self._abort_if_unique_id_configured()
                    
                    return self.async_create_entry(
                        title=f"RFID Access Control - {device_id[:20]}",
                        data={"device_id": device_id},
                    )
                except self._abort_if_unique_id_configured.__class__:
                    return self.async_abort(reason="already_configured")
                except Exception as e:
                    _LOGGER.error(f"Unexpected error: {e}")
                    errors["base"] = "unknown"

        # Try to get ZHA devices
        try:
            dev_reg = dr.async_get(self.hass)
            zha_devices = {}
            
            for device in dev_reg.devices.values():
                if device and device.identifiers:
                    for _, identifier in device.identifiers:
                        for model in SUPPORTED_MODELS.keys():
                            if model in str(identifier):
                                device_name = device.name or device.model or "Unknown"
                                zha_devices[device.id] = f"{device_name} ({device.model or 'Device'})"
                                break
            
            # If ZHA devices found, show them
            if zha_devices:
                return self.async_show_form(
                    step_id="user",
                    data_schema=vol.Schema({
                        vol.Required(CONF_DEVICE_ID): vol.In(zha_devices),
                    }),
                    errors=errors,
                    description_placeholders={"info": "Select your KEPZB-110 device"},
                )
        except Exception as e:
            _LOGGER.warning(f"Could not get ZHA devices: {e}")

        # If no ZHA devices, show manual entry
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICE_ID): cv.string,
            }),
            errors=errors,
            description_placeholders={
                "info": "No ZHA devices found. Enter device ID (e.g., 'portoncino' for Zigbee2MQTT)",
            },
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_data)
