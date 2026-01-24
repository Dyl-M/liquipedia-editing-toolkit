"""Liquipedia Editing Toolkit - CLI for start.gg and Liquipedia integration.

This package provides tools for fetching tournament data from start.gg
and generating Liquipedia-formatted wikitext for Rocket League competitions.
"""

# Local
from lptk.config import Settings, get_settings, get_token, setup_logging
from lptk.exceptions import (
    APIError,
    ConfigurationError,
    LiquipediaAPIError,
    LPTKError,
    StartGGAPIError,
    WikitextParseError,
)

__version__ = "0.0.1-alpha"
__all__ = [
    "__version__",
    # Config
    "Settings",
    "get_settings",
    "get_token",
    # Exceptions
    "LPTKError",
    "ConfigurationError",
    "APIError",
    "StartGGAPIError",
    "LiquipediaAPIError",
    "WikitextParseError",
]

# Initialize logging on package import
setup_logging()
