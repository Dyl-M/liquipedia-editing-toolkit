# `lptk`

Liquipedia Editing Toolkit - A Python package for integrating start.gg tournament data with Liquipedia wikitext.

## Overview

This package provides tools for:

- Fetching tournament data from start.gg via GraphQL API
- Generating Liquipedia-formatted wikitext (TeamCards, TeamParticipants, brackets)
- Inserting stream links into tournament pages
- Filling prize pool sections with placement data

Liquipedia DB API access is delegated to the [`liquipydia`](https://github.com/Dyl-M/liquipydia) library.

## Current Status

**Version**: 0.0.2-alpha (API layer - start.gg)

Currently implemented:

- `config.py` - Environment-based settings with pydantic-settings
- `exceptions.py` - Custom exception hierarchy
- `api/` - `StartGGClient` for start.gg GraphQL API
- `models/` - Pydantic data models (`Team`, `Player`, `Phase`, `PhaseGroup`, `SetDetails`)

See `_docs/ROADMAP.md` for the complete development plan.

## Public API

### Configuration

```python
from lptk import Settings, get_lpdb_token, get_settings, get_token

# Get the settings singleton
settings = get_settings()
print(settings.log_level)  # "INFO"
print(settings.startgg_api_url)  # "https://api.start.gg/gql/alpha"

# Read the local keys file (default: .tokens/local_keys.json)
token = get_token()            # start.gg token (required)
lpdb_key = get_lpdb_token()    # Liquipedia DB key (optional, raises if absent)
```

Keys file schema (`.token/local_keys.json`):

```json
{
  "startgg": "<start.gg api token>",
  "lpdb":    "<liquipedia db api key>"
}
```

### Environment Variables

All settings can be overridden via environment variables with the `LPTK_` prefix:

| Variable                 | Default                          | Description                                 |
|--------------------------|----------------------------------|---------------------------------------------|
| `LPTK_LOCAL_KEYS_PATH`   | `.token/local_keys.json`         | Path to the local JSON keys file            |
| `LPTK_DATA_DIR`          | `_data/`                         | Output directory for JSON files             |
| `LPTK_LOG_LEVEL`         | `INFO`                           | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LPTK_STARTGG_API_URL`   | `https://api.start.gg/gql/alpha` | start.gg GraphQL endpoint                   |
| `LPTK_RATE_LIMIT_DELAY`  | `0.5`                            | Delay between API calls (seconds)           |
| `LPTK_USER_AGENT`        | `None`                           | Optional User-Agent for requests            |

### Exceptions

```python
from lptk import (
    LPTKError,  # Base exception for all lptk errors
    ConfigurationError,  # Invalid or missing configuration
    APIError,  # Base for API-related errors
    StartGGAPIError,  # start.gg API failures
    WikitextParseError,  # Wikitext parsing failures
)

# All exceptions can be caught with LPTKError
try:
    token = get_token()
except LPTKError as e:
    print(f"Error: {e.message}")
    print(f"Details: {e.details}")
```

### Clients & Models

```python
from lptk import StartGGClient, Team, Phase, SetDetails

with StartGGClient() as client:
    event_id, name = client.get_event_id("tournament/rlcs-2026/event/main")
    teams: list[Team] = client.get_event_standings(event_id, top_n=16)
```

## Module Structure

```
lptk/
├── __init__.py      # Package exports, version, logging setup
├── config.py        # Settings management, token loading
├── exceptions.py    # Custom exception hierarchy
├── api/             # API clients (StartGGClient)
├── models/          # Pydantic data models
├── py.typed         # PEP 561 marker for type hints
└── README.md        # This file
```

## Planned Modules

The following modules will be added in future versions (see `_docs/ROADMAP.md`):

- `wikitext/` - Wikitext parsing and generation
- `tools/` - Business logic (participants, prizepool, streams)
- `cli/` - Command-line interface
- `utils/` - Utility functions

## Dependencies

- `pydantic` / `pydantic-settings` - Settings management and validation
- `requests` - HTTP client
- `liquipydia` - Liquipedia DB API v3 wrapper
- `beautifulsoup4` - HTML parsing
- `pycountry` - Country code utilities
- `typer` - CLI framework (planned)
