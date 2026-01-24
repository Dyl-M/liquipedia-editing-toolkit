# Liquipedia Editing Toolkit

![Python](https://img.shields.io/badge/python-3.12+-blue?logo=python&logoColor=white)
![License](https://img.shields.io/github/license/Dyl-M/liquipedia-editing-toolkit)
![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Toolkit for automating Liquipedia page editing with data from start.gg esports tournaments (Rocket League focus).

> **Status: v0.0.1-alpha** - Foundation phase complete. The `lptk/` package now includes configuration management,
> custom exceptions, and a test suite with 100% coverage. Legacy code remains in `_archive/`.
> See [`_docs/ROADMAP.md`](_docs/ROADMAP.md) for the development plan.

## Features

### Tournament Page Filler

Generate Liquipedia wikitext from start.gg tournament results:

- **Cascading Phase Analysis:** Collects teams from most advanced phase (Finals) backwards to earlier phases (Playoffs →
  Swiss → Pools)
- **Ongoing Tournament Support:** Fetch data from live tournaments using phase group fallback
- **Smart Placement Lock-in:** Includes teams with confirmed placements; uses placeholders for ongoing matches
- **Pool Group Integration:** Enriches team data with pool group and placement for accurate bracket positioning
- **Two Format Options:**
    - Legacy TeamCard format for older pages
    - Modern TeamParticipants format for newer tournament pages
- Fetch top N teams with placement, player info, and country data
- Generate formatted output with tabs for different placement ranges
- Query Liquipedia for canonical player names (handles redirects)
- Automatic detection of completed vs. ongoing tournaments
- Bracket-aware sorting by pool placement and bracket position

### Stream Filler

Insert Twitch/YouTube stream links into Liquipedia match brackets:

- Regex-based wikitext manipulation
- Batch processing for multiple teams
- Support for both Twitch and YouTube

### Prize Pool Filler

Automatically fill Liquipedia prize pool sections with tournament results:

- Smart fallback: Uses event standings for completed tournaments, phase results for ongoing ones
- Bracket-aware sorting: Teams ordered by group (B1, B2, ...) then match identifier (AL, AM, ...)
- Elimination tracking: Populates "lastvs" (opponent) and "lastvsscore" (match score) fields
- Forfeit handling: Automatically formats forfeit scores as "FF-W" or "W-FF"
- Phase optimization: Skips large phases (>512 teams) to avoid API timeouts

## Quick Start (New `lptk` Package)

```python
from lptk import get_settings, get_token, LPTKError

# Access configuration
settings = get_settings()
print(settings.startgg_api_url)  # https://api.start.gg/gql/alpha

# Get API token (requires _token/start.gg-token.txt)
try:
    token = get_token()
except LPTKError as e:
    print(f"Configuration error: {e}")
```

Environment variables (all prefixed with `LPTK_`):
- `LPTK_TOKEN_PATH` - Path to API token file
- `LPTK_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `LPTK_RATE_LIMIT_DELAY` - Delay between API calls (seconds)

## Setup

### Requirements

- Python 3.12+
- Dependencies: `pydantic`, `pydantic-settings`, `requests`, `beautifulsoup4`, `pycountry`, `typer`

### Installation

Using [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv sync
```

Or with pip:

```bash
pip install -e .
```

### API Token

Create a start.gg API token and save it to:

```
_token/start.gg-token.txt
```

This file is gitignored and must be created manually.

## Project Structure

```
liquipedia-editing-toolkit/
├── lptk/                             # New package (v0.0.1-alpha)
│   ├── __init__.py                   # Package exports, version
│   ├── config.py                     # Settings management (pydantic-settings)
│   ├── exceptions.py                 # Custom exception hierarchy
│   ├── py.typed                      # PEP 561 marker
│   └── README.md                     # Package documentation
├── _tests/                           # Test suite (100% coverage)
│   ├── conftest.py                   # Shared fixtures
│   ├── test_config.py                # Config module tests
│   ├── test_exceptions.py            # Exception tests
│   └── README.md                     # Test documentation
├── _archive/                         # Legacy code (archived during restructure)
│   └── src/                          # Original source modules
│       ├── tournament_page_filler/   # Generate TeamCards/TeamParticipants
│       ├── stream_filler/            # Insert stream links into brackets
│       └── prize_pool_filler/        # Fill prize pool sections
├── _docs/                            # Project documentation
│   └── ROADMAP.md                    # Development roadmap and architecture
├── _data/                            # Tournament JSON data (gitignored)
├── _token/                           # API tokens (gitignored)
├── pyproject.toml                    # Project configuration
├── .python-version                   # Python version (3.12)
└── README.md
```

### Target Architecture (v1.0.0)

```
lptk/
├── api/                      # API clients (start.gg, Liquipedia)
├── wikitext/                 # Wikitext parsing and generation
│   ├── parser.py             # Parse templates from wikitext
│   ├── builder.py            # Build wikitext strings
│   └── templates/            # Template implementations (Opponent, Slot, TeamCard, etc.)
├── tools/                    # Business logic (participants, prizepool, streams)
├── cli/                      # Typer-based CLI
├── models/                   # Pydantic data models
└── utils/                    # Shared utilities
```

## Usage Examples

### Fetch Tournament Data and Generate Wikitext

```python
from _archive.src.tournament_page_filler import startgg_tools as sgg_t
from _archive.src.tournament_page_filler import liquipedia_tools as lp_t
import json

# Fetch top 32 teams from a tournament
event_slug = "tournament/rlcs-2026-europe-open-1/event/3v3-bracket"
teams = sgg_t.get_event_top_teams(event_slug, top_n=32)

# Save to JSON
with open('_data/tournament.json', 'w', encoding='utf-8') as f:
    json.dump(teams, f, indent=4, ensure_ascii=False)

# Generate wikitext with tabs (Top 12, Places 13-32)
wikitext = lp_t.generate_team_participants_tabs_from_json(
    '_data/tournament.json',
    segments=[12, 32]
)
print(wikitext)
```

### Fill Prize Pool Section

```python
from _archive.src.prize_pool_filler.fill_prize_pool import process_prizepool_from_event

process_prizepool_from_event(
    event_slug="tournament/rlcs-2026-europe-open-1/event/3v3-bracket",
    wikitext_path="wikitext_input.txt",
    output_path="wikitext_output.txt",
    top_n=None,  # Auto-calculate from wikitext
    phase_name=None  # Auto-detect best phase
)
```

## License

MIT License - see [LICENSE](LICENSE) for details.
