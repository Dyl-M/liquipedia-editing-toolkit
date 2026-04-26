"""API clients for external services.

This module provides a client class for interacting with the start.gg
GraphQL API. Liquipedia API access is handled by the `liquipydia`
library (https://github.com/Dyl-M/liquipydia).
"""

# Local
from lptk.api.startgg import StartGGClient

__all__ = [
    "StartGGClient",
]
