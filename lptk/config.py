"""Configuration management for the lptk package.

Settings are loaded from environment variables with the LPTK_ prefix.
Tokens are read lazily from a JSON keys file (default ``.tokens/local_keys.json``),
with the shape ``{"startgg": "...", "lpdb": "..."}``.
"""

# Standard library
from functools import lru_cache
import json
import logging
from pathlib import Path
import sys
from typing import Literal

# Third-party
from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

# Local
from lptk.exceptions import ConfigurationError


def _get_project_root() -> Path:
    """Find the project root directory.

    Walks up from the current file location to find the directory
    containing pyproject.toml.

    Returns:
        Path to the project root directory.
    """
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    # Fallback to lptk parent directory
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = _get_project_root()


class LocalKeys(BaseModel):
    """Schema of ``.tokens/local_keys.json``.

    Attributes:
        startgg: start.gg API token (required).
        lpdb: Liquipedia DB API key (optional; required only when
            ``get_lpdb_token()`` is called).
    """

    startgg: str = Field(min_length=1, description="start.gg API token")
    lpdb: str | None = Field(default=None, description="Liquipedia DB API key")


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables with the LPTK_ prefix.
    For example, LPTK_LOG_LEVEL=DEBUG will set log_level to "DEBUG".

    Attributes:
        local_keys_path: Path to the JSON file holding local API keys.
        data_dir: Directory for storing JSON output files.
        log_level: Logging verbosity level.
        startgg_api_url: start.gg GraphQL API endpoint.
        rate_limit_delay: Delay between API calls in seconds.
        user_agent: Optional User-Agent header for API requests.
    """

    model_config = SettingsConfigDict(
        env_prefix="LPTK_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    local_keys_path: Path = Field(
        default=PROJECT_ROOT / ".tokens" / "local_keys.json",
        description="Path to the JSON file holding local API keys (startgg, lpdb)",
    )
    data_dir: Path = Field(
        default=PROJECT_ROOT / "_data",
        description="Directory for JSON output files",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging verbosity level",
    )
    startgg_api_url: str = Field(
        default="https://api.start.gg/gql/alpha",
        description="start.gg GraphQL API endpoint",
    )
    rate_limit_delay: float = Field(
        default=0.5,
        ge=0.0,
        description="Delay between start.gg API calls in seconds",
    )
    user_agent: str | None = Field(
        default=None,
        description="User-Agent header for API requests",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get the application settings singleton.

    Settings are cached after the first call. To reload settings,
    call get_settings.cache_clear() first.

    Returns:
        The Settings instance.
    """
    return Settings()


@lru_cache(maxsize=1)
def _load_local_keys() -> LocalKeys:
    """Read and validate ``local_keys.json`` once, then cache it.

    Raises:
        ConfigurationError: If the file is missing, not valid JSON, or
            fails schema validation (e.g. missing required ``startgg`` key).
    """
    settings = get_settings()
    keys_path = settings.local_keys_path

    if not keys_path.exists():
        raise ConfigurationError(
            f"Local keys file not found: {keys_path}",
            details={"local_keys_path": str(keys_path)},
        )

    raw = keys_path.read_text(encoding="utf-8")

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"Local keys file is not valid JSON: {keys_path}",
            details={"local_keys_path": str(keys_path), "error": str(exc)},
        ) from exc

    try:
        return LocalKeys.model_validate(payload)
    except ValidationError as exc:
        raise ConfigurationError(
            f"Local keys file failed schema validation: {keys_path}",
            details={"local_keys_path": str(keys_path), "errors": exc.errors()},
        ) from exc


def get_token() -> str:
    """Get the start.gg API token.

    Reads ``local_keys.json`` on first call and returns the ``startgg`` field.

    Returns:
        The start.gg API token string.

    Raises:
        ConfigurationError: If the keys file is missing, malformed, or the
            ``startgg`` field is missing or empty.
    """
    return _load_local_keys().startgg


def get_lpdb_token() -> str:
    """Get the Liquipedia DB API key.

    Reads ``local_keys.json`` on first call and returns the ``lpdb`` field.

    Returns:
        The Liquipedia DB API key.

    Raises:
        ConfigurationError: If the keys file is missing or malformed, or the
            ``lpdb`` field is absent / empty.
    """
    keys = _load_local_keys()
    if not keys.lpdb:
        raise ConfigurationError(
            "Liquipedia DB key (lpdb) missing from local keys file",
            details={"local_keys_path": str(get_settings().local_keys_path)},
        )
    return keys.lpdb


def clear_token_cache() -> None:
    """Clear the cached local keys and settings.

    Forces the next ``get_token()`` / ``get_lpdb_token()`` call to re-read
    the JSON file from disk, including any change to ``LPTK_LOCAL_KEYS_PATH``.
    """
    _load_local_keys.cache_clear()
    get_settings.cache_clear()


def setup_logging() -> None:
    """Configure logging based on settings.

    Sets up a stderr handler with the configured log level.
    This is called automatically when the lptk package is imported.
    """
    settings = get_settings()

    # Configure the lptk logger
    logger = logging.getLogger("lptk")
    logger.setLevel(settings.log_level)

    # Avoid adding duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(settings.log_level)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
