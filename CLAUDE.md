# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project for data analysis and integration between start.gg (esports tournament platform) and Liquipedia (gaming wiki) for Rocket League competitions. The codebase provides tools to:

1. Fetch tournament data from start.gg via GraphQL API
2. Generate Liquipedia-formatted wikitext (TeamCards, brackets, etc.)
3. Insert stream links into Liquipedia tournament pages

## Setup

### Dependencies
Install required packages:
```bash
pip install -r requirements.txt
```

Required packages: `pycountry`, `requests`, `beautifulsoup4`

### API Token
The project requires a start.gg API token stored at `token/start.gg-token.txt` (relative to project root). This file is gitignored and must be created manually. The token is read at module import time by `src/tournament_page_filler/startgg_tools.py`.

## Architecture

The codebase is organized into two main functional modules:

### 1. Tournament Page Filler (`src/tournament_page_filler/`)

**Purpose:** Retrieve tournament results from start.gg and generate Liquipedia TeamCard wikitext.

- **`startgg_tools.py`**: Interacts with start.gg GraphQL API
  - `get_event_id(comp_slug)`: Resolves event slug to internal ID
  - `get_event_top_teams(event_slug, top_n)`: Fetches top N teams with placement, team names, player info (id, tag, country)
  - `country_iso2(country_str)`: Normalizes country names to ISO 3166-1 alpha-2 codes using pycountry
  - Internal helper `_get_entrant_last_elimination_set_id()`: Determines the set that eliminated each team

- **`liquipedia_tools.py`**: Generates Liquipedia wikitext templates
  - `format_team_card_from_entry(entry)`: Converts a team dict to TeamCard template
  - `generate_team_cards_from_json(json_path)`: Batch generates TeamCards from JSON file
  - `generate_team_cards_tabs_from_json(json_path, segments)`: Creates tabbed sections (e.g., "Top 12", "Places 13-32") with boxed TeamCards
  - `get_true_player_name(player_name_input)`: Queries Liquipedia to get canonical player page titles (handles redirects)

**Data Flow:**
1. Call `startgg_tools.get_event_top_teams()` with event slug and top_n
2. Save results to `data/{tournament-name}.json`
3. Use `liquipedia_tools.generate_team_cards_*()` to convert JSON to wikitext
4. Copy wikitext to Liquipedia tournament pages

### 2. Stream Filler (`src/stream_filler/`)

**Purpose:** Insert Twitch/YouTube stream links into Liquipedia match brackets.

- **`insert_streams.py`**: Regex-based wikitext manipulation
  - `add_stream_channel(wikitext, team_name, channel_name, stream_type)`: Adds stream link for a specific team
  - `process_multiple_teams(wikitext, stream_configs_list)`: Batch processes multiple teams
  - `StreamConfig` class: Configuration for team streaming channels
  - `StreamType` enum: TWITCH or YOUTUBE

**Usage Pattern:**
1. Read existing wikitext from file (e.g., `wikitext_input.txt`)
2. Create list of `StreamConfig` objects
3. Call `process_multiple_teams()` to modify wikitext
4. Save to `wikitext_updated.txt`

## Development Workflow

### Testing/Sandbox
Use `src/_sandbox.py` for experimentation. Current example:
```python
# Fetch top 32 teams from an event
event_slug = "tournament/3v3-sam-champions-road-2025/event/3v3-bracket"
top_teams = sgg_t.get_event_top_teams(event_slug, top_n=32)

# Save to JSON
with open(f'../data/{event_slug.split('/')[1]}.json', 'w', encoding='utf-8') as json_file:
    json.dump(top_teams, json_file, indent=4, ensure_ascii=False)

# Generate wikitext with tabs
print(lp_t.generate_team_cards_tabs_from_json("../data/3v3-sam-champions-road-2025.json", [12, 32]))
```

### Data Storage
- Tournament JSON data: `data/{tournament-name}.json`
- Wikitext files: `src/stream_filler/wikitext_*.txt` (gitignored)

## Important Notes

### start.gg API
- All GraphQL requests use bearer token authentication via `QUERIES_HEADER`
- API endpoint: `https://api.start.gg/gql/alpha`
- Token is read once at import time; module must be reloaded if token changes
- Queries use pagination (typically 50 items per page) for large result sets
- Error handling: HTTP errors and GraphQL errors raise exceptions with detailed messages

### Liquipedia Integration
- User-Agent header required: Set `DEFAULT_USER_AGENT` in `liquipedia_tools.py` with contact info
- Wikitext templates follow Liquipedia Rocket League conventions
- TeamCard structure: team name, 3 starters (p1-p3), 1 substitute (s4), 1 coach (c)
- Country flags use lowercase ISO-2 codes (e.g., "fr", "us")
- Box/Tabs formatting uses `{{box|start}}`, `{{box|break}}`, `{{box|end}}` and `{{Tabs dynamic}}`

### Path Conventions
- Token file: `../../token/start.gg-token.txt` (relative to `src/tournament_page_filler/startgg_tools.py`)
- Data files: `../data/` (relative to `src/_sandbox.py`)
- Module imports use `from src.tournament_page_filler import ...` (project root expected in sys.path)

### Code Style
- Encoding: UTF-8 declared in file headers (`# -*- coding: utf-8 -*-`)
- Type hints used in newer code (e.g., `liquipedia_tools.py`)
- Comprehensive docstrings with Args/Returns/Raises sections
- Defensive programming: null checks, graceful degradation on API errors