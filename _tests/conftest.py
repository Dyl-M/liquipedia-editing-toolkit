"""Shared pytest fixtures for lptk tests."""

# Standard library
import json
import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

# Third-party
import pytest
import requests


@pytest.fixture
def tmp_token_file(tmp_path: Path) -> Path:
    """Create a temporary local-keys JSON file for testing.

    Args:
        tmp_path: pytest's built-in temporary directory fixture.

    Returns:
        Path to a JSON keys file populated with start.gg and lpdb test tokens.
    """
    keys_file = tmp_path / "local_keys.json"
    keys_file.write_text(
        json.dumps({"startgg": "test-api-token-12345", "lpdb": "test-lpdb-token-67890"}),
        encoding="utf-8",
    )
    return keys_file


@pytest.fixture
def empty_token_file(tmp_path: Path) -> Path:
    """Create a keys file missing the required ``startgg`` field.

    Args:
        tmp_path: pytest's built-in temporary directory fixture.

    Returns:
        Path to a JSON file containing ``{}`` (no keys).
    """
    keys_file = tmp_path / "empty_keys.json"
    keys_file.write_text("{}", encoding="utf-8")
    return keys_file


@pytest.fixture
def malformed_keys_file(tmp_path: Path) -> Path:
    """Create a keys file with invalid JSON content.

    Args:
        tmp_path: pytest's built-in temporary directory fixture.

    Returns:
        Path to a file whose contents do not parse as JSON.
    """
    keys_file = tmp_path / "malformed_keys.json"
    keys_file.write_text("not json at all {", encoding="utf-8")
    return keys_file


@pytest.fixture
def startgg_only_keys_file(tmp_path: Path) -> Path:
    """Create a keys file with only the ``startgg`` field populated.

    Args:
        tmp_path: pytest's built-in temporary directory fixture.

    Returns:
        Path to a JSON keys file with ``{"startgg": "..."}`` (no ``lpdb``).
    """
    keys_file = tmp_path / "startgg_only_keys.json"
    keys_file.write_text(
        json.dumps({"startgg": "test-api-token-12345"}),
        encoding="utf-8",
    )
    return keys_file


@contextmanager
def env_override(**kwargs: str | None) -> Generator[None, None, None]:
    """Context manager for temporarily setting environment variables.

    Args:
        **kwargs: Environment variable names and values. Use None to unset.

    Yields:
        None - environment variables are modified for the duration of the context.

    Example:
        with env_override(LPTK_LOG_LEVEL="DEBUG", LPTK_LOCAL_KEYS_PATH=None):
            # LPTK_LOG_LEVEL is set to "DEBUG"
            # LPTK_LOCAL_KEYS_PATH is unset
            pass
        # Original values are restored
    """
    original_values: dict[str, str | None] = {}

    # Store original values and set new ones
    for key, value in kwargs.items():
        original_values[key] = os.environ.get(key)
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

    try:
        yield
    finally:
        # Restore original values
        for key, original in original_values.items():
            if original is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Fixture that removes all LPTK_ environment variables.

    Yields:
        None - all LPTK_ env vars are unset for the duration of the test.
    """
    # Find all LPTK_ environment variables
    lptk_vars = {k: v for k, v in os.environ.items() if k.startswith("LPTK_")}

    # Remove them
    for key in lptk_vars:
        del os.environ[key]

    try:
        yield
    finally:
        # Restore them
        os.environ.update(lptk_vars)


@pytest.fixture
def reset_settings() -> Generator[None, None, None]:
    """Fixture that resets the settings cache after each test.

    This ensures tests don't affect each other through cached settings.

    Yields:
        None - settings cache is cleared after the test.
    """
    yield
    # Clear the settings cache after the test
    from lptk.config import (
        clear_token_cache,
        get_settings,
    )

    get_settings.cache_clear()
    clear_token_cache()


@pytest.fixture
def mock_session() -> MagicMock:
    """Create a mock requests session for API client tests."""
    session = MagicMock(spec=requests.Session)
    session.headers = {}
    return session


@pytest.fixture
def mock_settings(tmp_path: Path, reset_settings: Any) -> dict[str, Any]:
    """Create mock settings values for testing.

    Args:
        tmp_path: pytest's built-in temporary directory fixture.
        reset_settings: Ensures settings are reset after the test.

    Returns:
        Dictionary with test configuration values.
    """
    keys_file = tmp_path / "local_keys.json"
    keys_file.write_text(
        json.dumps({"startgg": "mock-token", "lpdb": "mock-lpdb"}),
        encoding="utf-8",
    )
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    return {
        "local_keys_path": keys_file,
        "data_dir": data_dir,
        "log_level": "DEBUG",
    }


# API Response Fixtures


@pytest.fixture
def startgg_event_response() -> dict[str, Any]:
    """Sample start.gg event query response."""
    return {
        "data": {
            "event": {
                "id": 12345,
                "name": "Test Tournament - Main Event",
            }
        }
    }


@pytest.fixture
def startgg_standings_response() -> dict[str, Any]:
    """Sample start.gg standings query response."""
    return {
        "data": {
            "event": {
                "standings": {
                    "nodes": [
                        {
                            "placement": 1,
                            "entrant": {
                                "id": 100,
                                "name": "Champions",
                                "participants": [
                                    {
                                        "id": 1001,
                                        "gamerTag": "Player1",
                                        "user": {
                                            "location": {"country": "France"}
                                        },
                                    },
                                    {
                                        "id": 1002,
                                        "gamerTag": "Player2",
                                        "user": {
                                            "location": {"country": "Germany"}
                                        },
                                    },
                                    {
                                        "id": 1003,
                                        "gamerTag": "Player3",
                                        "user": {
                                            "location": {"country": "Spain"}
                                        },
                                    },
                                ],
                            },
                        },
                        {
                            "placement": 2,
                            "entrant": {
                                "id": 101,
                                "name": "Runners-up",
                                "participants": [
                                    {
                                        "id": 1004,
                                        "gamerTag": "Player4",
                                        "user": {"location": None},
                                    },
                                ],
                            },
                        },
                    ]
                }
            }
        }
    }


@pytest.fixture
def startgg_phases_response() -> dict[str, Any]:
    """Sample start.gg phases query response."""
    return {
        "data": {
            "event": {
                "phases": [
                    {
                        "id": 1,
                        "name": "Day 1 - Swiss",
                        "state": 3,
                        "numSeeds": 64,
                        "phaseGroups": {
                            "nodes": [
                                {
                                    "id": 10,
                                    "displayIdentifier": "1",
                                    "state": 3,
                                    "seeds": {"pageInfo": {"total": 64}},
                                }
                            ]
                        },
                    },
                    {
                        "id": 2,
                        "name": "Day 2 - Playoffs",
                        "state": 3,
                        "numSeeds": 16,
                        "phaseGroups": {
                            "nodes": [
                                {
                                    "id": 20,
                                    "displayIdentifier": "B1",
                                    "state": 3,
                                    "seeds": {"pageInfo": {"total": 8}},
                                },
                                {
                                    "id": 21,
                                    "displayIdentifier": "B2",
                                    "state": 3,
                                    "seeds": {"pageInfo": {"total": 8}},
                                },
                            ]
                        },
                    },
                ]
            }
        }
    }


@pytest.fixture
def startgg_set_details_response() -> dict[str, Any]:
    """Sample start.gg set details query response."""
    return {
        "data": {
            "set": {
                "id": 999,
                "identifier": "B1 AL",
                "winnerId": 100,
                "slots": [
                    {
                        "entrant": {"id": 100, "name": "Winner Team"},
                        "standing": {"stats": {"score": {"value": 3}}},
                    },
                    {
                        "entrant": {"id": 101, "name": "Loser Team"},
                        "standing": {"stats": {"score": {"value": 2}}},
                    },
                ],
            }
        }
    }


