"""Configuration management for the lptk package.

Settings are loaded from environment variables with the LPTK_ prefix.
The token is loaded lazily when first accessed via get_token().
"""

# Standard library
import logging
import sys
from functools import lru_cache
from pathlib import Path
from typing import Literal

# Third-party
from pydantic import Field
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


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables with the LPTK_ prefix.
    For example, LPTK_LOG_LEVEL=DEBUG will set log_level to "DEBUG".

    Attributes:
        token_path: Path to the start.gg API token file.
        data_dir: Directory for storing JSON output files.
        log_level: Logging verbosity level.
        startgg_api_url: start.gg GraphQL API endpoint.
        liquipedia_api_url: Liquipedia MediaWiki API endpoint.
        rate_limit_delay: Delay between API calls in seconds.
    """

    model_config = SettingsConfigDict(
        env_prefix="LPTK_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    token_path: Path = Field(
        default=PROJECT_ROOT / "_token" / "start.gg-token.txt",
        description="Path to the start.gg API token file",
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
    liquipedia_api_url: str = Field(
        default="https://liquipedia.net/rocketleague/api.php",
        description="Liquipedia MediaWiki API endpoint",
    )
    rate_limit_delay: float = Field(
        default=0.5,
        ge=0.0,
        description="Delay between API calls in seconds",
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


# Token cache (None = not loaded, str = loaded value)
_token_cache: str | None = None


def get_token() -> str:
    """Get the start.gg API token.

    The token is loaded lazily from the configured token_path on first access
    and cached for subsequent calls.

    Returns:
        The API token string.

    Raises:
        ConfigurationError: If the token file is missing or empty.
    """
    global _token_cache

    if _token_cache is not None:
        return _token_cache

    settings = get_settings()
    token_path = settings.token_path

    if not token_path.exists():
        raise ConfigurationError(
            f"Token file not found: {token_path}",
            details={"token_path": str(token_path)},
        )

    token = token_path.read_text(encoding="utf-8").strip()

    if not token:
        raise ConfigurationError(
            f"Token file is empty: {token_path}",
            details={"token_path": str(token_path)},
        )

    _token_cache = token
    return _token_cache


def clear_token_cache() -> None:
    """Clear the cached token.

    Use this to force reloading the token from disk on the next get_token() call.
    """
    global _token_cache
    _token_cache = None


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
