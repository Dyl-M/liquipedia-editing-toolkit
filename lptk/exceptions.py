"""Custom exception hierarchy for the lptk package.

All exceptions inherit from LPTKError to allow catching all package-specific
errors with a single except clause.
"""

# Standard library
from typing import Any


class LPTKError(Exception):
    """Base exception for all lptk errors.

    Args:
        message: Human-readable error description.
        details: Optional dictionary with additional context.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        if self.details:
            detail_str = ", ".join(f"{k}={v!r}" for k, v in self.details.items())
            return f"{self.message} ({detail_str})"
        return self.message


class ConfigurationError(LPTKError):
    """Raised when configuration is invalid or missing.

    Examples:
        - Missing API token file
        - Invalid environment variable values
        - Missing required settings
    """


class APIError(LPTKError):
    """Base exception for API-related errors.

    Args:
        message: Human-readable error description.
        status_code: HTTP status code if applicable.
        details: Optional dictionary with additional context.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        super().__init__(message, details)

    def __str__(self) -> str:
        base = super().__str__()
        if self.status_code is not None:
            return f"[HTTP {self.status_code}] {base}"
        return base


class StartGGAPIError(APIError):
    """Raised when start.gg API requests fail.

    Examples:
        - HTTP errors from the GraphQL endpoint
        - GraphQL query errors
        - Rate limiting responses
    """


class WikitextParseError(LPTKError):
    """Raised when wikitext parsing fails.

    Examples:
        - Malformed template syntax
        - Unexpected wikitext structure
        - Missing required template parameters
    """
