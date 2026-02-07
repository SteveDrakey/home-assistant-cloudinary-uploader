"""Tests for the Cloudinary Uploader config flow."""

from __future__ import annotations

from unittest.mock import patch

import cloudinary.exceptions
import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.cloudinary_uploader.const import (
    CONF_API_KEY,
    CONF_API_SECRET,
    CONF_CLOUD_NAME,
    DOMAIN,
)

from .conftest import MOCK_CONFIG


@pytest.fixture(autouse=True)
def _bypass_setup(mock_cloudinary_config, mock_cloudinary_upload):
    """Prevent actual setup during config flow tests."""


async def test_full_user_flow(
    hass: HomeAssistant,
    mock_cloudinary_ping,
) -> None:
    """Test a successful config flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_CONFIG,
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_CONFIG[CONF_CLOUD_NAME]
    assert result["data"] == MOCK_CONFIG


async def test_invalid_auth(
    hass: HomeAssistant,
) -> None:
    """Test config flow with invalid credentials."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "cloudinary.api.ping",
        side_effect=cloudinary.exceptions.AuthorizationRequired(
            "Invalid credentials"
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=MOCK_CONFIG,
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_cannot_connect(
    hass: HomeAssistant,
) -> None:
    """Test config flow when connection fails."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "cloudinary.api.ping",
        side_effect=Exception("Network error"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=MOCK_CONFIG,
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_duplicate_entry(
    hass: HomeAssistant,
    mock_cloudinary_ping,
) -> None:
    """Test that duplicate cloud names are rejected."""
    # Create the first entry.
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_CONFIG,
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY

    # Try to create a duplicate entry.
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_CONFIG,
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"
