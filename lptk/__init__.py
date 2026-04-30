"""Liquipedia Editing Toolkit - CLI for start.gg and Liquipedia integration.

This package provides tools for fetching tournament data from start.gg
and generating Liquipedia-formatted wikitext for Rocket League competitions.

Liquipedia API access is delegated to the `liquipydia` library.
"""

# Local
from lptk.api import StartGGClient
from lptk.config import (
    Settings,
    get_lpdb_token,
    get_settings,
    get_token,
    setup_logging,
)
from lptk.exceptions import (
    APIError,
    ConfigurationError,
    LPTKError,
    StartGGAPIError,
    WikitextParseError,
)
from lptk.models import (
    Phase,
    PhaseGroup,
    Player,
    SetDetails,
    SetSlot,
    Team,
)

__version__ = "0.0.3-alpha"
__all__ = [
    "__version__",
    # Config
    "Settings",
    "get_settings",
    "get_token",
    "get_lpdb_token",
    # Exceptions
    "LPTKError",
    "ConfigurationError",
    "APIError",
    "StartGGAPIError",
    "WikitextParseError",
    # API clients
    "StartGGClient",
    # Models
    "Player",
    "Team",
    "Phase",
    "PhaseGroup",
    "SetSlot",
    "SetDetails",
]

# Initialize logging on package import
setup_logging()
