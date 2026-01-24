"""Tests for the lptk.exceptions module."""

# Third-party
import pytest

# Local
from lptk.exceptions import (
    APIError,
    ConfigurationError,
    LiquipediaAPIError,
    LPTKError,
    StartGGAPIError,
    WikitextParseError,
)


class TestLPTKError:
    """Tests for the base LPTKError class."""

    @staticmethod
    def test_message_only() -> None:
        """Test creating an error with just a message."""
        error = LPTKError("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.details == {}
        assert str(error) == "Something went wrong"

    @staticmethod
    def test_message_with_details() -> None:
        """Test creating an error with message and details."""
        error = LPTKError("Failed to process", details={"file": "test.txt", "line": 42})
        assert error.message == "Failed to process"
        assert error.details == {"file": "test.txt", "line": 42}
        assert "file='test.txt'" in str(error)
        assert "line=42" in str(error)

    @staticmethod
    def test_exception_args() -> None:
        """Test that the exception can be raised and caught."""
        with pytest.raises(LPTKError) as exc_info:
            raise LPTKError("Test error")
        assert str(exc_info.value) == "Test error"

    @staticmethod
    def test_empty_details_not_shown() -> None:
        """Test that empty details don't appear in string representation."""
        error = LPTKError("Error message", details={})
        assert str(error) == "Error message"
        assert "(" not in str(error)


class TestConfigurationError:
    """Tests for ConfigurationError."""

    @staticmethod
    def test_inheritance() -> None:
        """Test that ConfigurationError inherits from LPTKError."""
        error = ConfigurationError("Config error")
        assert isinstance(error, LPTKError)
        assert isinstance(error, Exception)

    @staticmethod
    def test_can_be_caught_as_lptk_error() -> None:
        """Test that ConfigurationError can be caught as LPTKError."""
        with pytest.raises(LPTKError):
            raise ConfigurationError("Missing token")

    @staticmethod
    def test_with_details() -> None:
        """Test ConfigurationError with details."""
        error = ConfigurationError(
            "Token file not found",
            details={"path": "/path/to/token.txt"},
        )
        assert "path='/path/to/token.txt'" in str(error)


class TestAPIError:
    """Tests for APIError and its subclasses."""

    @staticmethod
    def test_without_status_code() -> None:
        """Test APIError without HTTP status code."""
        error = APIError("Request failed")
        assert error.status_code is None
        assert str(error) == "Request failed"

    @staticmethod
    def test_with_status_code() -> None:
        """Test APIError with HTTP status code."""
        error = APIError("Not found", status_code=404)
        assert error.status_code == 404
        assert str(error) == "[HTTP 404] Not found"

    @staticmethod
    def test_with_status_code_and_details() -> None:
        """Test APIError with status code and details."""
        error = APIError(
            "Rate limited",
            status_code=429,
            details={"retry_after": 60},
        )
        assert "[HTTP 429]" in str(error)
        assert "retry_after=60" in str(error)

    @staticmethod
    def test_inheritance() -> None:
        """Test that APIError inherits from LPTKError."""
        error = APIError("API error")
        assert isinstance(error, LPTKError)


class TestStartGGAPIError:
    """Tests for StartGGAPIError."""

    @staticmethod
    def test_inheritance() -> None:
        """Test inheritance chain."""
        error = StartGGAPIError("GraphQL error")
        assert isinstance(error, APIError)
        assert isinstance(error, LPTKError)

    @staticmethod
    def test_with_status_code() -> None:
        """Test with HTTP status code."""
        error = StartGGAPIError("Unauthorized", status_code=401)
        assert "[HTTP 401]" in str(error)

    @staticmethod
    def test_can_be_caught_as_api_error() -> None:
        """Test that StartGGAPIError can be caught as APIError."""
        with pytest.raises(APIError):
            raise StartGGAPIError("start.gg error")


class TestLiquipediaAPIError:
    """Tests for LiquipediaAPIError."""

    @staticmethod
    def test_inheritance() -> None:
        """Test inheritance chain."""
        error = LiquipediaAPIError("MediaWiki error")
        assert isinstance(error, APIError)
        assert isinstance(error, LPTKError)

    @staticmethod
    def test_with_details() -> None:
        """Test with details."""
        error = LiquipediaAPIError(
            "Page not found",
            status_code=404,
            details={"page": "Tournament/Invalid"},
        )
        assert "[HTTP 404]" in str(error)
        assert "page='Tournament/Invalid'" in str(error)


class TestWikitextParseError:
    """Tests for WikitextParseError."""

    @staticmethod
    def test_inheritance() -> None:
        """Test that WikitextParseError inherits from LPTKError."""
        error = WikitextParseError("Parse error")
        assert isinstance(error, LPTKError)

    @staticmethod
    def test_with_details() -> None:
        """Test with parsing context details."""
        error = WikitextParseError(
            "Unclosed template",
            details={"template": "TeamCard", "position": 150},
        )
        assert "template='TeamCard'" in str(error)
        assert "position=150" in str(error)

    @staticmethod
    def test_can_be_caught_as_lptk_error() -> None:
        """Test that WikitextParseError can be caught as LPTKError."""
        with pytest.raises(LPTKError):
            raise WikitextParseError("Invalid syntax")


class TestExceptionHierarchy:
    """Tests for the overall exception hierarchy."""

    @staticmethod
    def test_catch_all_with_lptk_error() -> None:
        """Test that all custom exceptions can be caught with LPTKError."""
        exceptions = [
            LPTKError("base"),
            ConfigurationError("config"),
            APIError("api"),
            StartGGAPIError("startgg"),
            LiquipediaAPIError("liquipedia"),
            WikitextParseError("wikitext"),
        ]

        for exc in exceptions:
            with pytest.raises(LPTKError):
                raise exc

    @staticmethod
    def test_catch_api_errors_with_api_error() -> None:
        """Test that API-related exceptions can be caught with APIError."""
        api_exceptions = [
            APIError("api"),
            StartGGAPIError("startgg"),
            LiquipediaAPIError("liquipedia"),
        ]

        for exc in api_exceptions:
            with pytest.raises(APIError):
                raise exc

    @staticmethod
    def test_specific_exceptions_not_caught_by_siblings() -> None:
        """Test that sibling exceptions are not caught by each other."""
        # ConfigurationError should not catch WikitextParseError
        with pytest.raises(WikitextParseError):
            try:
                raise WikitextParseError("parse error")
            except ConfigurationError:
                pytest.fail("WikitextParseError should not be caught by ConfigurationError")

        # StartGGAPIError should not catch LiquipediaAPIError
        with pytest.raises(LiquipediaAPIError):
            try:
                raise LiquipediaAPIError("liquipedia error")
            except StartGGAPIError:
                pytest.fail("LiquipediaAPIError should not be caught by StartGGAPIError")
