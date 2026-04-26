"""Tests for lptk.api._retry module."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from lptk.api._retry import retry_with_backoff
from lptk.exceptions import APIError


class TestRetryWithBackoff:
    """Tests for the retry_with_backoff decorator."""

    @staticmethod
    def test_successful_call_no_retry() -> None:
        """Test that successful calls don't trigger retries."""
        call_count = 0

        @retry_with_backoff(max_retries=3)
        def successful_func() -> str:
            """Return successfully on the first attempt without raising."""
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()
        assert result == "success"
        assert call_count == 1

    @patch("lptk.api._retry.time.sleep")
    def test_retries_on_request_exception(self, mock_sleep: MagicMock) -> None:
        """Test retries on RequestException."""
        call_count = 0

        @retry_with_backoff(max_retries=2, initial_delay=1.0, backoff_factor=2.0)
        def failing_func() -> str:
            """Raise RequestException on the first two calls, then succeed."""
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise requests.RequestException("Connection error")
            return "success"

        result = failing_func()
        assert result == "success"
        assert call_count == 3
        # Check sleep was called with correct delays (1.0, 2.0)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1.0)
        mock_sleep.assert_any_call(2.0)

    @patch("lptk.api._retry.time.sleep")
    def test_max_retries_exceeded_raises_api_error(self, mock_sleep: MagicMock) -> None:
        """Test that max retries exceeded raises APIError."""
        call_count = 0

        @retry_with_backoff(max_retries=2)
        def always_failing_func() -> str:
            """Always raise a retryable RequestException."""
            nonlocal call_count
            call_count += 1
            raise requests.RequestException("Always fails")

        with pytest.raises(APIError) as exc_info:
            always_failing_func()

        assert "Max retries (2) exhausted" in str(exc_info.value)
        assert call_count == 3  # Initial + 2 retries

    @patch("lptk.api._retry.time.sleep")
    def test_retries_on_retryable_status_code(self, mock_sleep: MagicMock) -> None:
        """Test retries on 429 status code."""
        call_count = 0

        @retry_with_backoff(max_retries=2)
        def rate_limited_func() -> requests.Response:
            """Return a 429 response twice, then a 200 response."""
            nonlocal call_count
            call_count += 1
            response = MagicMock(spec=requests.Response)
            if call_count < 3:
                response.status_code = 429
            else:
                response.status_code = 200
            return response

        result = rate_limited_func()
        assert result.status_code == 200
        assert call_count == 3

    @patch("lptk.api._retry.time.sleep")
    @pytest.mark.parametrize("status_code", [500, 502, 503, 504])
    def test_retries_on_5xx_status_codes(self, mock_sleep: MagicMock, status_code: int) -> None:
        """Test retries on 5xx status codes."""
        call_count = 0

        @retry_with_backoff(max_retries=1)
        def server_error_func() -> requests.Response:
            """Return the parametrised 5xx status on the first call, then 200."""
            nonlocal call_count
            call_count += 1
            response = MagicMock(spec=requests.Response)
            response.status_code = status_code if call_count == 1 else 200
            return response

        result = server_error_func()
        assert result.status_code == 200, f"Failed for status {status_code}"

    @staticmethod
    def test_no_retry_on_non_retryable_exception() -> None:
        """Test that non-retryable exceptions are raised immediately."""

        @retry_with_backoff(max_retries=3)
        def value_error_func() -> str:
            """Raise a non-retryable ValueError."""
            raise ValueError("Not retryable")

        with pytest.raises(ValueError, match="Not retryable"):
            value_error_func()

    @patch("lptk.api._retry.time.sleep")
    def test_custom_retryable_exceptions(self, mock_sleep: MagicMock) -> None:
        """Test custom retryable exceptions."""
        call_count = 0

        @retry_with_backoff(
            max_retries=2,
            retryable_exceptions=(ValueError,),
        )
        def custom_retryable_func() -> str:
            """Raise the custom-retryable ValueError twice, then succeed."""
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Custom retryable")
            return "success"

        result = custom_retryable_func()
        assert result == "success"
        assert call_count == 3

    @staticmethod
    def test_no_retry_on_non_retryable_status_code() -> None:
        """Test that non-retryable status codes don't trigger retries."""
        call_count = 0

        @retry_with_backoff(max_retries=3)
        def bad_request_func() -> requests.Response:
            """Return a 400 response that should not trigger retries."""
            nonlocal call_count
            call_count += 1
            response = MagicMock(spec=requests.Response)
            response.status_code = 400  # Not retryable
            return response

        result = bad_request_func()
        assert result.status_code == 400
        assert call_count == 1  # No retries

    @patch("lptk.api._retry.time.sleep")
    def test_exponential_backoff_delays(self, mock_sleep: MagicMock) -> None:
        """Test that delays follow exponential backoff pattern."""
        call_count = 0

        @retry_with_backoff(
            max_retries=3,
            initial_delay=0.5,
            backoff_factor=3.0,
        )
        def failing_func() -> str:
            """Raise RequestException on the first three calls, then succeed."""
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise requests.RequestException("Fail")
            return "success"

        result = failing_func()
        assert result == "success"

        # Check delays: 0.5, 1.5, 4.5
        calls = mock_sleep.call_args_list
        assert calls[0][0][0] == 0.5
        assert calls[1][0][0] == 1.5
        assert calls[2][0][0] == 4.5

    @patch("lptk.api._retry.time.sleep")
    def test_max_retries_with_status_code(self, mock_sleep: MagicMock) -> None:
        """Test max retries exceeded with retryable status code."""

        @retry_with_backoff(max_retries=2)
        def always_rate_limited() -> requests.Response:
            """Always return a 429 response so retries exhaust."""
            response = MagicMock(spec=requests.Response)
            response.status_code = 429
            response.url = "https://api.example.com"
            return response

        with pytest.raises(APIError) as exc_info:
            always_rate_limited()

        assert exc_info.value.status_code == 429
        assert "Max retries (2) exhausted" in str(exc_info.value)

    @staticmethod
    def test_negative_max_retries_raises_api_error() -> None:
        """Degenerate max_retries < 0 skips the loop entirely."""

        @retry_with_backoff(max_retries=-1)
        def never_runs() -> str:
            """Return a sentinel string the retry loop should never reach."""
            return "never"

        with pytest.raises(APIError) as exc_info:
            never_runs()

        assert "Unexpected retry loop exit" in str(exc_info.value)
