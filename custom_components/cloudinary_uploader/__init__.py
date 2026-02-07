"""The Cloudinary Uploader integration."""

from __future__ import annotations

import logging
import os
from functools import partial
from typing import Any

import cloudinary
import cloudinary.uploader
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
import homeassistant.helpers.config_validation as cv

from .const import (
    ATTR_FILE_PATH,
    ATTR_PUBLIC_ID,
    CONF_API_KEY,
    CONF_API_SECRET,
    CONF_CLOUD_NAME,
    DOMAIN,
    SERVICE_UPLOAD_IMAGE,
)

_LOGGER = logging.getLogger(__name__)

UPLOAD_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_FILE_PATH): cv.string,
        vol.Required(ATTR_PUBLIC_ID): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Cloudinary Uploader from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        CONF_CLOUD_NAME: entry.data[CONF_CLOUD_NAME],
        CONF_API_KEY: entry.data[CONF_API_KEY],
        CONF_API_SECRET: entry.data[CONF_API_SECRET],
    }

    async def async_handle_upload(call: ServiceCall) -> None:
        """Handle the upload_image service call."""
        file_path: str = call.data[ATTR_FILE_PATH]
        public_id: str = call.data[ATTR_PUBLIC_ID]

        if not hass.config.is_allowed_path(file_path):
            raise ServiceValidationError(
                f"Path '{file_path}' is not in the allowlist. "
                "Add it to 'allowlist_external_dirs' in configuration.yaml.",
                translation_domain=DOMAIN,
                translation_key="path_not_allowed",
                translation_placeholders={"file_path": file_path},
            )

        if not os.path.isfile(file_path):
            raise ServiceValidationError(
                f"File not found: {file_path}",
                translation_domain=DOMAIN,
                translation_key="file_not_found",
                translation_placeholders={"file_path": file_path},
            )

        config = hass.data[DOMAIN][entry.entry_id]

        try:
            result: dict[str, Any] = await hass.async_add_executor_job(
                partial(
                    _upload_to_cloudinary,
                    cloud_name=config[CONF_CLOUD_NAME],
                    api_key=config[CONF_API_KEY],
                    api_secret=config[CONF_API_SECRET],
                    file_path=file_path,
                    public_id=public_id,
                )
            )
        except cloudinary.exceptions.Error as err:
            raise HomeAssistantError(
                f"Cloudinary upload failed: {err}"
            ) from err
        except OSError as err:
            raise HomeAssistantError(
                f"Failed to read file '{file_path}': {err}"
            ) from err

        _LOGGER.debug(
            "Uploaded '%s' to Cloudinary as '%s' (url: %s)",
            file_path,
            public_id,
            result.get("secure_url"),
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_UPLOAD_IMAGE,
        async_handle_upload,
        schema=UPLOAD_SCHEMA,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.services.async_remove(DOMAIN, SERVICE_UPLOAD_IMAGE)
    hass.data[DOMAIN].pop(entry.entry_id)
    return True


def _upload_to_cloudinary(
    *,
    cloud_name: str,
    api_key: str,
    api_secret: str,
    file_path: str,
    public_id: str,
) -> dict[str, Any]:
    """Upload a file to Cloudinary (runs in executor)."""
    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
    )
    return cloudinary.uploader.upload(
        file_path,
        public_id=public_id,
        overwrite=True,
        resource_type="image",
    )
