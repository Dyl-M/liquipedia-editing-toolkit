"""Retry decorator with exponential backoff for API calls.

This module provides a decorator that automatically retries failed requests
with exponential backoff, suitable for handling transient API errors.
"""

# Standard library
import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

# Third-party
import requests

# Local
from lptk.exceptions import APIError

logger = logging.getLogger("lptk.api")

P = ParamSpec("P")
T = TypeVar("T")


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple[type[Exception], ...] = (requests.RequestException,),
    retryable_status_codes: tuple[int, ...] = (429, 500, 502, 503, 504),
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator that retries a function with exponential backoff.

    The decorator will retry the wrapped function when it raises a retryable
    exception or returns a response with a retryable status code.

    Args:
        max_retries: Maximum number of retry attempts (default: 3).
        initial_delay: Initial delay in seconds before first retry (default: 1.0).
        backoff_factor: Multiplier for delay between retries (default: 2.0).
        retryable_exceptions: Tuple of exception types that trigger a retry.
        retryable_status_codes: HTTP status codes that trigger a retry.

    Returns:
        A decorator function that wraps the target function with retry logic.

    Raises:
        APIError: When max retries are exhausted without success.
        Exception: The original exception if it's not retryable.

    Example:
        >>> @retry_with_backoff(max_retries=3, initial_delay=1.0)
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data")
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)

                    # Check if result is a Response with a retryable status code
                    if isinstance(result, requests.Response):
                        if result.status_code in retryable_status_codes:
                            if attempt < max_retries:
                                logger.warning(
                                    "Retryable status %d on attempt %d/%d, "
                                    "retrying in %.1fs...",
                                    result.status_code,
                                    attempt + 1,
                                    max_retries + 1,
                                    delay,
                                )
                                time.sleep(delay)
                                delay *= backoff_factor
                                continue
                            # Max retries exhausted
                            raise APIError(
                                f"Max retries ({max_retries}) exhausted",
                                status_code=result.status_code,
                                details={
                                    "url": result.url,
                                    "attempts": attempt + 1,
                                },
                            )

                    return result

                except retryable_exceptions as e:
                    if attempt < max_retries:
                        logger.warning(
                            "Retryable error on attempt %d/%d: %s, "
                            "retrying in %.1fs...",
                            attempt + 1,
                            max_retries + 1,
                            str(e),
                            delay,
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        # Max retries exhausted
                        raise APIError(
                            f"Max retries ({max_retries}) exhausted: {e}",
                            details={"attempts": attempt + 1, "last_error": str(e)},
                        ) from e

            raise APIError("Unexpected retry loop exit")

        return wrapper

    return decorator
