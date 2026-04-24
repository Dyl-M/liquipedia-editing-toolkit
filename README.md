# Liquipedia Editing Toolkit

![Python](https://img.shields.io/badge/python-3.12+-blue?logo=python&logoColor=white)
![License](https://img.shields.io/github/license/Dyl-M/liquipedia-editing-toolkit)
![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![DeepSource](https://app.deepsource.com/gh/Dyl-M/liquipedia-editing-toolkit.svg/?label=active+issues&show_trend=false&token=Jkf0lDe06vzL02w3tnFLV3yh)](https://app.deepsource.com/gh/Dyl-M/liquipedia-editing-toolkit/)
[![DeepSource](https://app.deepsource.com/gh/Dyl-M/liquipedia-editing-toolkit.svg/?label=code+coverage&show_trend=false&token=Jkf0lDe06vzL02w3tnFLV3yh)](https://app.deepsource.com/gh/Dyl-M/liquipedia-editing-toolkit/)

Toolkit for automating Liquipedia page editing with data from start.gg esports tournaments (Rocket League focus).

> **Status: v0.0.2-alpha** - API layer complete. The `lptk/` package now includes `StartGGClient` (start.gg GraphQL),
> Pydantic data models (`Team`, `Player`, `Phase`, `SetDetails`), retry logic with exponential backoff, and a test
> suite with 128 tests (100% coverage). Liquipedia DB API access is delegated to the
> [`liquipydia`](https://github.com/Dyl-M/liquipydia) library. Legacy code remains in `_archive/`.
> See [`_docs/ROADMAP.md`](_docs/ROADMAP.md) for the development plan and [`CHANGELOG.md`](CHANGELOG.md) for version history.

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
from lptk import StartGGClient, LPTKError

# Fetch tournament data from start.gg
with StartGGClient() as client:
    event_id, name = client.get_event_id("tournament/rlcs-2026/event/main")
    teams = client.get_event_standings(event_id, top_n=16)
    for team in teams:
        print(f"{team.placement}. {team.team_name}")

# Liquipedia DB access is provided by the liquipydia library
from liquipydia import LiquipediaClient

with LiquipediaClient() as lp:
    player = lp.get_player("Jstn")
    team = lp.get_team("Team Vitality")
```

Environment variables (all prefixed with `LPTK_`):

- `LPTK_LOCAL_KEYS_PATH` - Path to the local JSON keys file (default `.token/local_keys.json`)
- `LPTK_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `LPTK_STARTGG_API_URL` - start.gg GraphQL endpoint
- `LPTK_RATE_LIMIT_DELAY` - Delay between start.gg API calls (seconds)
- `LPTK_USER_AGENT` - Optional User-Agent for API requests

> Liquipedia DB API credentials and rate-limiting are configured via the `liquipydia` library — refer to its
> [documentation](https://github.com/Dyl-M/liquipydia) for details.

## Setup

### Requirements

- Python 3.12+
- Dependencies: `pydantic`, `pydantic-settings`, `requests`, `liquipydia`, `beautifulsoup4`, `pycountry`, `typer`

### Installation

Using [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv sync
```

Or with pip:

```bash
pip install -e .
```

### API Tokens

Credentials live under the `.token/` folder (gitignored, created manually) as two JSON files grouped by scope:

```
.token/
├── local_keys.json    # runtime keys loaded by lptk
└── repo_keys.json     # local-tooling keys (not loaded by lptk)
```

**`.token/local_keys.json`** — runtime keys:

```json
{
  "startgg": "<start.gg api token>",
  "lpdb":    "<liquipedia db api key>"
}
```

`startgg` is required; `lpdb` is optional and only needed when your code calls `get_lpdb_token()` (or passes
the key to `liquipydia.LiquipediaClient`).

**`.token/repo_keys.json`** — local tooling (CI uses GitHub secrets; `lptk` does not read this file):

```json
{
  "pat": "<github personal access token>"
}
```

Token sources:

- **start.gg**: Get your token from [start.gg Developer Settings](https://start.gg/admin/profile/developer).
- **Liquipedia DB**: Request an API key at [liquipedia.net/api](https://liquipedia.net/api). The key is consumed
  by the [`liquipydia`](https://github.com/Dyl-M/liquipydia) library.

Override the keys file path via the `LPTK_LOCAL_KEYS_PATH` environment variable if needed.

## Project Structure

```
liquipedia-editing-toolkit/
├── lptk/                             # Main package (v0.0.2-alpha)
│   ├── __init__.py                   # Package exports, version
│   ├── config.py                     # Settings management (pydantic-settings)
│   ├── exceptions.py                 # Custom exception hierarchy
│   ├── py.typed                      # PEP 561 marker
│   ├── api/                          # API clients
│   │   ├── startgg.py                # StartGGClient - start.gg GraphQL
│   │   └── _retry.py                 # Retry decorator with exponential backoff
│   └── models/                       # Pydantic data models
│       ├── team.py                   # Player, Team models
│       └── tournament.py             # Phase, PhaseGroup, SetDetails models
├── _tests/                           # Test suite (128 tests, 100% coverage)
├── _archive/                         # Legacy code (archived during restructure)
├── _docs/                            # Project documentation
├── _data/                            # Tournament JSON data (gitignored)
├── .token/                           # API keys as JSON (gitignored)
├── _drafts/                          # Work-in-progress files (gitignored)
├── pyproject.toml                    # Project configuration
├── .python-version                   # Python version (3.12)
├── CHANGELOG.md                      # Version history
└── README.md
```

### Target Architecture (v1.0.0)

```
lptk/
├── api/                      # start.gg client (Liquipedia via liquipydia library)
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
