"""Tests for the Cloudinary Uploader service."""

from __future__ import annotations

from unittest.mock import patch

import cloudinary.exceptions
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cloudinary_uploader.const import (
    ATTR_FILE_PATH,
    ATTR_PUBLIC_ID,
    DOMAIN,
    SERVICE_UPLOAD_IMAGE,
)

from .conftest import MOCK_CONFIG


def _create_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Create and add a mock config entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=MOCK_CONFIG["cloud_name"],
        data=MOCK_CONFIG,
        unique_id=MOCK_CONFIG["cloud_name"],
    )
    entry.add_to_hass(hass)
    return entry


async def _setup_integration(hass: HomeAssistant) -> None:
    """Set up the integration with a mock config entry."""
    await async_setup_component(hass, "homeassistant", {})
    entry = _create_entry(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_upload_image_success(
    hass: HomeAssistant,
    mock_cloudinary_upload,
    mock_cloudinary_config,
) -> None:
    """Test a successful image upload."""
    await _setup_integration(hass)

    test_file = "/tmp/test_image.jpg"

    with (
        patch.object(hass.config, "is_allowed_path", return_value=True),
        patch("os.path.isfile", return_value=True),
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_UPLOAD_IMAGE,
            {ATTR_FILE_PATH: test_file, ATTR_PUBLIC_ID: "my_camera/snapshot"},
            blocking=True,
        )

    mock_cloudinary_config.assert_called_once_with(
        cloud_name=MOCK_CONFIG["cloud_name"],
        api_key=MOCK_CONFIG["api_key"],
        api_secret=MOCK_CONFIG["api_secret"],
    )
    mock_cloudinary_upload.assert_called_once_with(
        test_file,
        public_id="my_camera/snapshot",
        overwrite=True,
        resource_type="image",
    )


async def test_upload_path_not_allowed(
    hass: HomeAssistant,
    mock_cloudinary_upload,
    mock_cloudinary_config,
) -> None:
    """Test that upload is rejected when the path is not in the allowlist."""
    await _setup_integration(hass)

    with (
        patch.object(hass.config, "is_allowed_path", return_value=False),
        pytest.raises(ServiceValidationError, match="not in the allowlist"),
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_UPLOAD_IMAGE,
            {
                ATTR_FILE_PATH: "/etc/secret_file",
                ATTR_PUBLIC_ID: "test",
            },
            blocking=True,
        )

    mock_cloudinary_upload.assert_not_called()


async def test_upload_file_not_found(
    hass: HomeAssistant,
    mock_cloudinary_upload,
    mock_cloudinary_config,
) -> None:
    """Test that upload fails when the file does not exist."""
    await _setup_integration(hass)

    with (
        patch.object(hass.config, "is_allowed_path", return_value=True),
        patch("os.path.isfile", return_value=False),
        pytest.raises(ServiceValidationError, match="File not found"),
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_UPLOAD_IMAGE,
            {
                ATTR_FILE_PATH: "/tmp/nonexistent.jpg",
                ATTR_PUBLIC_ID: "test",
            },
            blocking=True,
        )

    mock_cloudinary_upload.assert_not_called()


async def test_upload_cloudinary_error(
    hass: HomeAssistant,
    mock_cloudinary_config,
) -> None:
    """Test that Cloudinary API errors are surfaced as HomeAssistantError."""
    await _setup_integration(hass)

    with (
        patch.object(hass.config, "is_allowed_path", return_value=True),
        patch("os.path.isfile", return_value=True),
        patch(
            "cloudinary.uploader.upload",
            side_effect=cloudinary.exceptions.Error("Upload failed: invalid image"),
        ),
        pytest.raises(HomeAssistantError, match="Cloudinary upload failed"),
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_UPLOAD_IMAGE,
            {
                ATTR_FILE_PATH: "/tmp/bad_image.jpg",
                ATTR_PUBLIC_ID: "test",
            },
            blocking=True,
        )


async def test_upload_os_error(
    hass: HomeAssistant,
    mock_cloudinary_config,
) -> None:
    """Test that OS errors during upload are surfaced as HomeAssistantError."""
    await _setup_integration(hass)

    with (
        patch.object(hass.config, "is_allowed_path", return_value=True),
        patch("os.path.isfile", return_value=True),
        patch(
            "cloudinary.uploader.upload",
            side_effect=OSError("Permission denied"),
        ),
        pytest.raises(HomeAssistantError, match="Failed to read file"),
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_UPLOAD_IMAGE,
            {
                ATTR_FILE_PATH: "/tmp/locked.jpg",
                ATTR_PUBLIC_ID: "test",
            },
            blocking=True,
        )


async def test_upload_passes_overwrite_flag(
    hass: HomeAssistant,
    mock_cloudinary_upload,
    mock_cloudinary_config,
) -> None:
    """Test that overwrite=True is always sent to Cloudinary."""
    await _setup_integration(hass)

    with (
        patch.object(hass.config, "is_allowed_path", return_value=True),
        patch("os.path.isfile", return_value=True),
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_UPLOAD_IMAGE,
            {ATTR_FILE_PATH: "/tmp/img.jpg", ATTR_PUBLIC_ID: "same_id"},
            blocking=True,
        )

    _, kwargs = mock_cloudinary_upload.call_args
    assert kwargs["overwrite"] is True
    assert kwargs["public_id"] == "same_id"
