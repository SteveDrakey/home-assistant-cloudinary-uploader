"""Fixtures for Cloudinary Uploader tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.cloudinary_uploader.const import (
    CONF_API_KEY,
    CONF_API_SECRET,
    CONF_CLOUD_NAME,
    DOMAIN,
)

MOCK_CONFIG = {
    CONF_CLOUD_NAME: "test_cloud",
    CONF_API_KEY: "test_api_key_123",
    CONF_API_SECRET: "test_api_secret_456",
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_cloudinary_upload() -> Generator[None]:
    """Mock cloudinary.uploader.upload."""
    with patch(
        "cloudinary.uploader.upload",
        return_value={
            "public_id": "test_id",
            "secure_url": "https://res.cloudinary.com/test_cloud/image/upload/test_id.jpg",
            "version": 1234567890,
        },
    ) as mock_upload:
        yield mock_upload


@pytest.fixture
def mock_cloudinary_ping() -> Generator[None]:
    """Mock cloudinary.api.ping."""
    with patch(
        "cloudinary.api.ping",
        return_value={"status": "ok"},
    ) as mock_ping:
        yield mock_ping


@pytest.fixture
def mock_cloudinary_config() -> Generator[None]:
    """Mock cloudinary.config."""
    with patch(
        "cloudinary.config",
    ) as mock_cfg:
        yield mock_cfg


@pytest.fixture
async def setup_hass(hass: HomeAssistant) -> HomeAssistant:
    """Set up a Home Assistant instance for testing."""
    await async_setup_component(hass, "homeassistant", {})
    return hass
