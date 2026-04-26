# `lptk` Test Suite

This directory contains the test suite for the lptk package.

## Running Tests

```bash
# Install the test dependency group first
uv sync --group test

# Run all tests
uv run pytest

# Run with verbose output (already enabled by `addopts` in pyproject.toml)
uv run pytest -v

# Run with coverage (uses `coverage` directly, matching CI)
uv run coverage run -m pytest && uv run coverage report
uv run coverage xml                                  # XML report for DeepSource

# Run a specific test file
uv run pytest _tests/test_config.py

# Run a specific test class or method
uv run pytest _tests/test_config.py::TestSettings
uv run pytest _tests/test_config.py::TestSettings::test_default_values
```

## Test Organization

```
_tests/
├── __init__.py          # Package marker
├── conftest.py          # Shared fixtures
├── test_config.py       # Tests for lptk.config module
├── test_exceptions.py   # Tests for lptk.exceptions module
└── README.md            # This file
```

### Naming Convention

- Test files: `test_<module>.py`
- Test classes: `Test<ClassName>` (groups related tests)
- Test methods: `test_<behavior_description>`

## Available Fixtures

Defined in `conftest.py`:

| Fixture                  | Scope    | Description                                                 |
|--------------------------|----------|-------------------------------------------------------------|
| `tmp_token_file`         | function | Creates a temp `local_keys.json` with `startgg` + `lpdb`    |
| `empty_token_file`       | function | Creates a keys file containing `{}` (fails schema)          |
| `malformed_keys_file`    | function | Creates a keys file with invalid JSON content               |
| `startgg_only_keys_file` | function | Keys file with only `startgg` set (no `lpdb`)               |
| `clean_env`              | function | Removes all `LPTK_*` environment variables                  |
| `reset_settings`         | function | Clears settings and token caches after test                 |
| `mock_settings`          | function | Provides mock configuration values                          |

### Helper Functions

```python
from _tests.conftest import env_override

# Temporarily set environment variables
with env_override(LPTK_LOG_LEVEL="DEBUG"):
    # LPTK_LOG_LEVEL is "DEBUG" here
    pass
# Original value restored

# Unset a variable
with env_override(LPTK_LOCAL_KEYS_PATH=None):
    # LPTK_LOCAL_KEYS_PATH is unset
    pass
```

## Coverage Requirements

- **Minimum**: 80% coverage required for all phases
- **Target**: 90%+ coverage at v1.0.0

Current coverage can be checked with:

```bash
uv run pytest _tests/ --cov=lptk --cov-report=term-missing
```

## Writing Tests

### Guidelines

1. **Use `@staticmethod`** - Test methods don't use `self`, so mark them as static
2. **Use fixtures** - Prefer fixtures over setup/teardown for test isolation
3. **Reset caches** - Use `reset_settings` fixture when testing config
4. **Test error paths** - Include tests for exceptions and edge cases

### Example Test

```python
class TestMyFeature:
    """Tests for my feature."""

    @staticmethod
    def test_happy_path(reset_settings: None) -> None:
        """Test the expected behavior."""
        result = my_function()
        assert result == expected

    @staticmethod
    def test_error_case(reset_settings: None) -> None:
        """Test error handling."""
        with pytest.raises(LPTKError) as exc_info:
            my_function_that_fails()
        assert "expected message" in str(exc_info.value)
```

## Planned Test Structure

As the package grows, tests will be organized into:

```
_tests/
├── conftest.py
├── unit/                    # Fast, isolated unit tests
│   ├── test_config.py
│   ├── test_exceptions.py
│   ├── test_models.py
│   └── ...
├── integration/             # Tests with real API calls (marked slow)
│   ├── test_startgg_api.py
│   └── test_liquipedia_api.py
└── fixtures/                # Sample API responses
    └── ...
```

Integration tests will be marked with `@pytest.mark.slow` and can be skipped:

```bash
uv run pytest _tests/ -m "not slow"
```
