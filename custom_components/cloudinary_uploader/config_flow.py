"""Config flow for Cloudinary Uploader."""

from __future__ import annotations

import logging
from functools import partial
from typing import Any

import cloudinary
import cloudinary.api
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_API_KEY, CONF_API_SECRET, CONF_CLOUD_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CLOUD_NAME): str,
        vol.Required(CONF_API_KEY): str,
        vol.Required(CONF_API_SECRET): str,
    }
)


def _validate_credentials(
    cloud_name: str, api_key: str, api_secret: str
) -> None:
    """Validate Cloudinary credentials by calling the API (runs in executor)."""
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
    )
    cloudinary.api.ping()


class CloudinaryUploaderConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cloudinary Uploader."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Prevent duplicate entries for the same cloud name.
            await self.async_set_unique_id(user_input[CONF_CLOUD_NAME])
            self._abort_if_unique_id_configured()

            try:
                await self.hass.async_add_executor_job(
                    partial(
                        _validate_credentials,
                        cloud_name=user_input[CONF_CLOUD_NAME],
                        api_key=user_input[CONF_API_KEY],
                        api_secret=user_input[CONF_API_SECRET],
                    )
                )
            except cloudinary.exceptions.AuthorizationRequired:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during credential validation")
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_CLOUD_NAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )
