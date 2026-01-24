# `lptk`

Liquipedia Editing Toolkit - A Python package for integrating start.gg tournament data with Liquipedia wikitext.

## Overview

This package provides tools for:

- Fetching tournament data from start.gg via GraphQL API
- Generating Liquipedia-formatted wikitext (TeamCards, TeamParticipants, brackets)
- Inserting stream links into tournament pages
- Filling prize pool sections with placement data

## Current Status

**Version**: 0.0.1-alpha (Foundation phase)

Currently implemented:

- `config.py` - Environment-based settings with pydantic-settings
- `exceptions.py` - Custom exception hierarchy

See `_docs/ROADMAP.md` for the complete development plan.

## Public API

### Configuration

```python
from lptk import Settings, get_settings, get_token

# Get the settings singleton
settings = get_settings()
print(settings.log_level)  # "INFO"
print(settings.startgg_api_url)  # "https://api.start.gg/gql/alpha"

# Get the API token (loaded lazily from file)
token = get_token()
```

### Environment Variables

All settings can be overridden via environment variables with the `LPTK_` prefix:

| Variable                | Default                     | Description                                 |
|-------------------------|-----------------------------|---------------------------------------------|
| `LPTK_TOKEN_PATH`       | `_token/start.gg-token.txt` | Path to API token file                      |
| `LPTK_DATA_DIR`         | `_data/`                    | Output directory for JSON files             |
| `LPTK_LOG_LEVEL`        | `INFO`                      | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LPTK_RATE_LIMIT_DELAY` | `0.5`                       | Delay between API calls (seconds)           |

### Exceptions

```python
from lptk import (
    LPTKError,  # Base exception for all lptk errors
    ConfigurationError,  # Invalid or missing configuration
    APIError,  # Base for API-related errors
    StartGGAPIError,  # start.gg API failures
    LiquipediaAPIError,  # Liquipedia API failures
    WikitextParseError,  # Wikitext parsing failures
)

# All exceptions can be caught with LPTKError
try:
    token = get_token()
except LPTKError as e:
    print(f"Error: {e.message}")
    print(f"Details: {e.details}")
```

## Module Structure

```
lptk/
├── __init__.py      # Package exports, version, logging setup
├── config.py        # Settings management, token loading
├── exceptions.py    # Custom exception hierarchy
├── py.typed         # PEP 561 marker for type hints
└── README.md        # This file
```

## Planned Modules

The following modules will be added in future versions:

- `api/` - API clients for start.gg and Liquipedia
- `models/` - Pydantic data models
- `wikitext/` - Wikitext parsing and generation
- `tools/` - Business logic (participants, prizepool, streams)
- `cli/` - Command-line interface
- `utils/` - Utility functions

## Dependencies

- `pydantic` / `pydantic-settings` - Settings management and validation
- `requests` - HTTP client (planned)
- `beautifulsoup4` - HTML parsing (planned)
- `pycountry` - Country code utilities (planned)
- `typer` - CLI framework (planned)
