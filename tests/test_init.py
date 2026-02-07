"""Tests for the Cloudinary Uploader integration setup."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.cloudinary_uploader.const import DOMAIN, SERVICE_UPLOAD_IMAGE

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


async def test_setup_entry(hass: HomeAssistant) -> None:
    """Test successful setup of a config entry."""
    entry = _create_entry(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert hass.services.has_service(DOMAIN, SERVICE_UPLOAD_IMAGE)


async def test_unload_entry(hass: HomeAssistant) -> None:
    """Test unloading a config entry removes the service."""
    entry = _create_entry(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.services.has_service(DOMAIN, SERVICE_UPLOAD_IMAGE)

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
    assert not hass.services.has_service(DOMAIN, SERVICE_UPLOAD_IMAGE)
