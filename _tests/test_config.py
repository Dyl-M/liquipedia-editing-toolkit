"""Tests for the lptk.config module."""

# Standard library
import json
import logging
from pathlib import Path

# Third-party
import pytest

# Local
from _tests.conftest import env_override
from lptk.config import (
    LocalKeys,
    Settings,
    clear_token_cache,
    get_lpdb_token,
    get_settings,
    get_token,
    setup_logging,
)
from lptk.exceptions import ConfigurationError


class TestSettings:
    """Tests for the Settings class."""

    @staticmethod
    def test_default_values(reset_settings: None) -> None:
        """Test that Settings has sensible defaults."""
        settings = Settings()

        assert settings.log_level == "INFO"
        assert settings.rate_limit_delay == 0.5
        assert settings.startgg_api_url == "https://api.start.gg/gql/alpha"

    @staticmethod
    def test_local_keys_path_is_path_object(reset_settings: None) -> None:
        """Test that local_keys_path is a Path object."""
        settings = Settings()
        assert isinstance(settings.local_keys_path, Path)

    @staticmethod
    def test_data_dir_is_path_object(reset_settings: None) -> None:
        """Test that data_dir is a Path object."""
        settings = Settings()
        assert isinstance(settings.data_dir, Path)

    @staticmethod
    def test_env_override_log_level(reset_settings: None) -> None:
        """Test that LPTK_LOG_LEVEL environment variable overrides default."""
        with env_override(LPTK_LOG_LEVEL="DEBUG"):
            settings = Settings()
            assert settings.log_level == "DEBUG"

    @staticmethod
    def test_env_override_local_keys_path(
        reset_settings: None, tmp_path: Path
    ) -> None:
        """Test that LPTK_LOCAL_KEYS_PATH environment variable overrides default."""
        custom_path = tmp_path / "custom_keys.json"
        with env_override(LPTK_LOCAL_KEYS_PATH=str(custom_path)):
            settings = Settings()
            assert settings.local_keys_path == custom_path

    @staticmethod
    def test_env_override_rate_limit(reset_settings: None) -> None:
        """Test that LPTK_RATE_LIMIT_DELAY environment variable overrides default."""
        with env_override(LPTK_RATE_LIMIT_DELAY="1.5"):
            settings = Settings()
            assert settings.rate_limit_delay == 1.5

    @staticmethod
    def test_rate_limit_must_be_non_negative(reset_settings: None) -> None:
        """Test that rate_limit_delay cannot be negative."""
        with (env_override(LPTK_RATE_LIMIT_DELAY="-1"), pytest.raises(ValueError)):
            Settings()


class TestGetSettings:
    """Tests for the get_settings function."""

    @staticmethod
    def test_returns_settings_instance(reset_settings: None) -> None:
        """Test that get_settings returns a Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    @staticmethod
    def test_singleton_behavior(reset_settings: None) -> None:
        """Test that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    @staticmethod
    def test_cache_clear_creates_new_instance(reset_settings: None) -> None:
        """Test that clearing cache creates a new Settings instance."""
        settings1 = get_settings()
        get_settings.cache_clear()
        settings2 = get_settings()
        # They should be equal but not the same object
        assert settings1 == settings2
        assert settings1 is not settings2


class TestLocalKeysSchema:
    """Tests for the LocalKeys pydantic schema."""

    @staticmethod
    def test_both_fields_populated() -> None:
        keys = LocalKeys(startgg="abc", lpdb="xyz")
        assert keys.startgg == "abc"
        assert keys.lpdb == "xyz"

    @staticmethod
    def test_lpdb_is_optional() -> None:
        keys = LocalKeys(startgg="abc")
        assert keys.startgg == "abc"
        assert keys.lpdb is None

    @staticmethod
    def test_missing_startgg_raises() -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LocalKeys()  # type: ignore[call-arg]

    @staticmethod
    def test_empty_startgg_raises() -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            LocalKeys(startgg="")


class TestGetToken:
    """Tests for the get_token function."""

    @staticmethod
    def test_loads_token_from_file(
        tmp_token_file: Path, reset_settings: None
    ) -> None:
        """Test that get_token loads the start.gg token from the JSON keys file."""
        with env_override(LPTK_LOCAL_KEYS_PATH=str(tmp_token_file)):
            get_settings.cache_clear()
            clear_token_cache()
            token = get_token()
            assert token == "test-api-token-12345"

    @staticmethod
    def test_caches_token(tmp_token_file: Path, reset_settings: None) -> None:
        """Test that the keys file is only read once (cache holds after mutation)."""
        with env_override(LPTK_LOCAL_KEYS_PATH=str(tmp_token_file)):
            get_settings.cache_clear()
            clear_token_cache()

            token1 = get_token()

            # Overwrite the keys file
            tmp_token_file.write_text(
                json.dumps({"startgg": "modified-token"}), encoding="utf-8"
            )

            # Should still return cached value
            token2 = get_token()
            assert token1 == token2 == "test-api-token-12345"

    @staticmethod
    def test_missing_token_file_raises_error(
        tmp_path: Path, reset_settings: None
    ) -> None:
        """Test that missing keys file raises ConfigurationError."""
        nonexistent = tmp_path / "missing_keys.json"
        with env_override(LPTK_LOCAL_KEYS_PATH=str(nonexistent)):
            get_settings.cache_clear()
            clear_token_cache()

            with pytest.raises(ConfigurationError) as exc_info:
                get_token()

            assert "not found" in str(exc_info.value).lower()
            assert "local_keys_path" in exc_info.value.details

    @staticmethod
    def test_empty_keys_file_raises_error(
        empty_token_file: Path, reset_settings: None
    ) -> None:
        """Test that a keys file missing ``startgg`` raises ConfigurationError."""
        with env_override(LPTK_LOCAL_KEYS_PATH=str(empty_token_file)):
            get_settings.cache_clear()
            clear_token_cache()

            with pytest.raises(ConfigurationError) as exc_info:
                get_token()

            assert "schema validation" in str(exc_info.value).lower()

    @staticmethod
    def test_malformed_json_raises_error(
        malformed_keys_file: Path, reset_settings: None
    ) -> None:
        """Test that a keys file with invalid JSON raises ConfigurationError."""
        with env_override(LPTK_LOCAL_KEYS_PATH=str(malformed_keys_file)):
            get_settings.cache_clear()
            clear_token_cache()

            with pytest.raises(ConfigurationError) as exc_info:
                get_token()

            assert "not valid json" in str(exc_info.value).lower()

    @staticmethod
    def test_clear_token_cache(
        tmp_token_file: Path, reset_settings: None
    ) -> None:
        """Test that clear_token_cache allows reloading the keys file."""
        with env_override(LPTK_LOCAL_KEYS_PATH=str(tmp_token_file)):
            get_settings.cache_clear()
            clear_token_cache()

            token1 = get_token()

            # Overwrite the keys file
            tmp_token_file.write_text(
                json.dumps({"startgg": "new-token", "lpdb": "new-lpdb"}),
                encoding="utf-8",
            )

            # Clear cache and reload
            clear_token_cache()
            token2 = get_token()
            lpdb2 = get_lpdb_token()

            assert token1 == "test-api-token-12345"
            assert token2 == "new-token"
            assert lpdb2 == "new-lpdb"

    @staticmethod
    def test_extra_keys_ignored(tmp_path: Path, reset_settings: None) -> None:
        """Unknown keys in the JSON file don't break parsing and aren't stored."""
        keys_file = tmp_path / "extra_keys.json"
        keys_file.write_text(
            json.dumps(
                {
                    "startgg": "my-token",
                    "lpdb": "my-lpdb",
                    "future_key": "ignored",
                }
            ),
            encoding="utf-8",
        )

        with env_override(LPTK_LOCAL_KEYS_PATH=str(keys_file)):
            clear_token_cache()

            assert get_token() == "my-token"
            assert get_lpdb_token() == "my-lpdb"

            # Validate LocalKeys directly to confirm the extra key is dropped
            payload = json.loads(keys_file.read_text(encoding="utf-8"))
            keys = LocalKeys.model_validate(payload)
            assert not hasattr(keys, "future_key")
            assert keys.model_fields_set == {"startgg", "lpdb"}


class TestGetLpdbToken:
    """Tests for the get_lpdb_token function."""

    @staticmethod
    def test_loads_lpdb_token(
        tmp_token_file: Path, reset_settings: None
    ) -> None:
        """Test that get_lpdb_token loads the lpdb key from the JSON keys file."""
        with env_override(LPTK_LOCAL_KEYS_PATH=str(tmp_token_file)):
            get_settings.cache_clear()
            clear_token_cache()
            assert get_lpdb_token() == "test-lpdb-token-67890"

    @staticmethod
    def test_missing_lpdb_raises_error(
        startgg_only_keys_file: Path, reset_settings: None
    ) -> None:
        """Test that get_lpdb_token raises when lpdb key is absent."""
        with env_override(LPTK_LOCAL_KEYS_PATH=str(startgg_only_keys_file)):
            get_settings.cache_clear()
            clear_token_cache()

            # get_token works (startgg is present)
            assert get_token() == "test-api-token-12345"

            # get_lpdb_token does not
            with pytest.raises(ConfigurationError) as exc_info:
                get_lpdb_token()

            assert "lpdb" in str(exc_info.value).lower()
            assert "local_keys_path" in exc_info.value.details


class TestSetupLogging:
    """Tests for the setup_logging function."""

    @staticmethod
    def test_creates_lptk_logger(reset_settings: None) -> None:
        """Test that setup_logging creates the lptk logger."""
        # Clear existing handlers first
        logger = logging.getLogger("lptk")
        logger.handlers.clear()

        setup_logging()

        assert len(logger.handlers) >= 1

    @staticmethod
    def test_respects_log_level(reset_settings: None) -> None:
        """Test that setup_logging respects the configured log level."""
        with env_override(LPTK_LOG_LEVEL="WARNING"):
            get_settings.cache_clear()

            logger = logging.getLogger("lptk")
            logger.handlers.clear()

            setup_logging()

            assert logger.level == logging.WARNING

    @staticmethod
    def test_does_not_add_duplicate_handlers(reset_settings: None) -> None:
        """Test that setup_logging doesn't add duplicate handlers."""
        logger = logging.getLogger("lptk")
        logger.handlers.clear()

        setup_logging()
        initial_count = len(logger.handlers)

        setup_logging()
        assert len(logger.handlers) == initial_count


class TestProjectRoot:
    """Tests for project root detection."""

    @staticmethod
    def test_project_root_contains_pyproject(reset_settings: None) -> None:
        """Test that PROJECT_ROOT points to directory with pyproject.toml."""
        from lptk.config import PROJECT_ROOT

        assert (PROJECT_ROOT / "pyproject.toml").exists()

    @staticmethod
    def test_default_paths_relative_to_project_root(reset_settings: None) -> None:
        """Test that default paths are relative to PROJECT_ROOT."""
        from lptk.config import PROJECT_ROOT

        settings = Settings()

        # Keys path should be under PROJECT_ROOT
        assert str(settings.local_keys_path).startswith(str(PROJECT_ROOT))

        # Data dir should be under PROJECT_ROOT
        assert str(settings.data_dir).startswith(str(PROJECT_ROOT))

    @staticmethod
    def test_project_root_fallback_when_no_pyproject(
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test fallback when pyproject.toml is not found in any parent."""
        from lptk.config import _get_project_root

        # Mock Path.exists to always return False for pyproject.toml
        original_exists = Path.exists

        def fake_exists(path: Path) -> bool:
            """Return False for pyproject.toml, otherwise use original exists."""
            if path.name == "pyproject.toml":
                return False
            return original_exists(path)

        monkeypatch.setattr(Path, "exists", fake_exists)

        # Call the function directly to test the fallback
        result = _get_project_root()

        # Should return the parent of the lptk package directory
        assert result.name != "lptk"
        assert (result / "lptk").exists()
