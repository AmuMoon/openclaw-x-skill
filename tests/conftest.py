"""Shared fixtures for openclaw-x tests."""

from __future__ import annotations

import pytest

from openclaw_x.auth import Credentials


@pytest.fixture
def creds():
    return Credentials(
        api_key="test_key",
        api_secret="test_secret",
        access_token="test_token",
        access_token_secret="test_token_secret",
        bearer_token="test_bearer",
    )
