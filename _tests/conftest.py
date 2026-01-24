"""Shared pytest fixtures for lptk tests."""

# Standard library
import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

# Third-party
import pytest


@pytest.fixture
def tmp_token_file(tmp_path: Path) -> Path:
    """Create a temporary token file for testing.

    Args:
        tmp_path: pytest's built-in temporary directory fixture.

    Returns:
        Path to the temporary token file containing a test token.
    """
    token_file = tmp_path / "test-token.txt"
    token_file.write_text("test-api-token-12345", encoding="utf-8")
    return token_file


@pytest.fixture
def empty_token_file(tmp_path: Path) -> Path:
    """Create an empty token file for testing error handling.

    Args:
        tmp_path: pytest's built-in temporary directory fixture.

    Returns:
        Path to an empty token file.
    """
    token_file = tmp_path / "empty-token.txt"
    token_file.write_text("", encoding="utf-8")
    return token_file


@contextmanager
def env_override(**kwargs: str | None) -> Generator[None, None, None]:
    """Context manager for temporarily setting environment variables.

    Args:
        **kwargs: Environment variable names and values. Use None to unset.

    Yields:
        None - environment variables are modified for the duration of the context.

    Example:
        with env_override(LPTK_LOG_LEVEL="DEBUG", LPTK_TOKEN_PATH=None):
            # LPTK_LOG_LEVEL is set to "DEBUG"
            # LPTK_TOKEN_PATH is unset
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
    from lptk.config import clear_token_cache, get_settings

    get_settings.cache_clear()
    clear_token_cache()


@pytest.fixture
def mock_settings(tmp_path: Path, reset_settings: Any) -> dict[str, Any]:
    """Create mock settings values for testing.

    Args:
        tmp_path: pytest's built-in temporary directory fixture.
        reset_settings: Ensures settings are reset after the test.

    Returns:
        Dictionary with test configuration values.
    """
    token_file = tmp_path / "token.txt"
    token_file.write_text("mock-token", encoding="utf-8")
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    return {
        "token_path": token_file,
        "data_dir": data_dir,
        "log_level": "DEBUG",
    }
