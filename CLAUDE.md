# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project for data analysis and integration between start.gg (esports tournament platform) and Liquipedia (gaming wiki) for Rocket League competitions. The codebase provides tools to:

1. Fetch tournament data from start.gg via GraphQL API
2. Generate Liquipedia-formatted wikitext (TeamCards, brackets, etc.)
3. Insert stream links into Liquipedia tournament pages
4. Automatically fill prize pool sections with tournament placements and elimination details

## Setup

### Dependencies
Install required packages:
```bash
pip install -r requirements.txt
```

Required packages: `pycountry`, `requests`, `beautifulsoup4`

### API Token
The project requires a start.gg API token stored at `_token/start.gg-token.txt` (relative to project root). This file is gitignored and must be created manually. The token is read at module import time by `src/tournament_page_filler/startgg_tools.py`.

## Architecture

The codebase is organized into three main functional modules:

### 1. Tournament Page Filler (`src/tournament_page_filler/`)

**Purpose:** Retrieve tournament results from start.gg and generate Liquipedia wikitext in multiple formats.

- **`startgg_tools.py`**: Interacts with start.gg GraphQL API
  - `get_event_id(comp_slug)`: Resolves event slug to internal ID
  - `get_event_top_teams(event_slug, top_n, use_phase_fallback=True)`: Fetches top N teams with placement, team names, player info (id, tag, country)
    - **Enhanced:** Automatically detects ongoing tournaments and falls back to phase group standings when event standings are incomplete
    - Set `use_phase_fallback=False` to disable fallback behavior
  - `_get_phase_groups_with_standings(event_id)`: Internal helper to fetch standings from phase groups for ongoing tournaments
  - `country_iso2(country_str)`: Normalizes country names to ISO 3166-1 alpha-2 codes using pycountry
  - Internal helper `_get_entrant_last_elimination_set_id()`: Determines the set that eliminated each team

- **`liquipedia_tools.py`**: Generates Liquipedia wikitext templates
  - **Old TeamCard Format:**
    - `format_team_card_from_entry(entry)`: Converts a team dict to TeamCard template
    - `generate_team_cards_from_json(json_path)`: Batch generates TeamCards from JSON file
    - `generate_team_cards_tabs_from_json(json_path, segments)`: Creates tabbed sections (e.g., "Top 12", "Places 13-32") with boxed TeamCards
  - **New TeamParticipants Format:**
    - `format_team_participants_opponent_from_entry(entry)`: Converts a team dict to TeamParticipants Opponent format
    - `generate_team_participants_from_json(json_path)`: Batch generates TeamParticipants from JSON file
    - `generate_team_participants_tabs_from_json(json_path, segments)`: Creates tabbed sections using TeamParticipants format
  - **Utilities:**
    - `get_true_player_name(player_name_input)`: Queries Liquipedia to get canonical player page titles (handles redirects)

**Data Flow:**
1. Call `startgg_tools.get_event_top_teams()` with event slug and top_n
   - For ongoing tournaments: Automatically falls back to phase group standings
   - For completed tournaments: Uses event-level standings
2. Save results to `_data/{tournament-name}.json`
3. Use `liquipedia_tools.generate_team_cards_*()` or `generate_team_participants_*()` to convert JSON to wikitext
4. Copy wikitext to Liquipedia tournament pages

**Application Scripts:**
- **`src/generate_team_participants.py`**: Main application for generating TeamParticipants wikitext
  - `generate_team_participants_wikitext(event_slug, top_n, segments, output_file, save_json)`: Complete workflow from API to wikitext
  - `generate_from_existing_json(json_path, segments, output_file)`: Generate from cached JSON data
  - Handles UTF-8 encoding, file I/O, and progress reporting
  - Configurable via script variables or can be imported as a module
- **`src/test_team_participants.py`**: Test script demonstrating both old and new formats

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

### 3. Prize pool Filler (`src/prize_pool_filler/`)

**Purpose:** Automatically fill Liquipedia prize pool wikitext with tournament placement data from start.gg.

#### Core Modules

- **`fill_prize_pool.py`**: Main module for processing prize pool wikitext
  - `parse_placement_range(place_str)`: Parses placement strings like "65-72" into (65, 72) tuples
  - `extract_prize_pool_slots(wikitext)`: Extracts all slots containing opponent entries to be filled
  - `calculate_required_teams(slots)`: Calculates maximum teams needed from slot ranges
  - `get_teams_with_placements(event_slug, required_teams, phase_name, use_phase_fallback)`: Fetches teams with smart fallback to phase results for ongoing tournaments
  - `fill_prizepool_opponents(wikitext, teams_data)`: Fills opponent slots with team names and elimination details, **sorted by group (B1, B2, ...) then match identifier (AL, AM, ...)**
  - `process_prizepool_from_event(event_slug, wikitext_path, output_path, top_n, phase_name)`: Complete end-to-end workflow

- **`get_phase_results.py`**: Handles ongoing tournaments with incomplete event standings
  - `get_tournament_structure(event_slug)`: Analyzes phase and group structure
  - `get_completed_phase_results(event_slug, phase_name_filter, required_teams)`: Fetches results from completed phases
  - `calculate_cumulative_placements(phase_results)`: Converts group placements to overall standings
  - Optimizations: Skips phases with >512 participants to avoid API timeouts

**Data Flow:**
1. Parse wikitext to identify slots with placement ranges (e.g., `{{Slot|place=65-72|...`)
2. Calculate required teams from maximum placement in slots
3. Fetch tournament data:
   - **Strategy 1:** Try event-level standings first (fastest for completed events)
   - **Strategy 2:** Fall back to phase results if event incomplete (ongoing tournaments)
   - Enrich with elimination_set_id for each team
4. For each team in placement slots, retrieve elimination details:
   - Use `get_set_details()` to fetch the set where they were eliminated
   - Extract opponent name (winner), match score, group name, and match identifier
5. **Sort teams by bracket position:** Group first (B1, B2, B3...), then match identifier (AL, AM, AN...) within each group
6. Replace `{{Opponent|tbd|lastvs=|lastvsscore=}}` with actual data
7. Output updated wikitext with filled opponent information

**Enhanced start.gg Tools:**
- `get_set_details(set_id)`: Fetches match details including participants, scores, and bracket position
  - Returns: `{"winner_name": str, "loser_name": str, "winner_score": int, "loser_score": int, "identifier": str}`
  - The `identifier` field contains the match ID (e.g., "AL", "AM") for bracket position sorting
  - Used to populate "lastvs" (last versus), "lastvsscore" fields, and for sorting

**Key Features:**
- **Smart Fallback:** Automatically detects ongoing tournaments and falls back to phase results
- **Phase Optimization:** Skips large phases (>512 teams) to avoid API timeouts
- **Bracket Sorting:** Teams sorted by group then match ID for correct Liquipedia ordering
- **Forfeit Handling:** Automatically formats forfeit scores as "FF-W" or "W-FF"
- **Rate Limiting:** Built-in 0.5s delays between API calls to avoid overwhelming start.gg

**Usage Pattern:**

```python
from src.prize_pool_filler.fill_prize_pool import process_prizepool_from_event

# Complete workflow - auto-detects phase and calculates required teams
process_prizepool_from_event(
    event_slug="tournament/rlcs-2026-europe-open-1/event/3v3-bracket",
    wikitext_path="src/prize_pool_filler/wikitext_input.txt",
    output_path="src/prize_pool_filler/wikitext_output.txt",
    top_n=None,  # Auto-calculate from wikitext (or specify manually)
    phase_name=None  # Auto-detect best phase (or specify "Day 2")
)
```

**Example Files:**
- `example_usage.py`: Demonstrates complete workflow, phase specification, and mock data testing
- `test_phase_2.py`: Tests for placement ordering, forfeit handling, and slot extraction
- `run_fill.py`: Quick script to run the filler on your wikitext files

## Development Workflow

### Debugging Utilities

The project includes several debugging scripts for exploring start.gg API responses:

- **`src/check_event_standings.py`**: Check if event-level standings are available (used to determine if a tournament is complete)
- **`src/check_active_teams.py`**: Check for incomplete/ongoing sets in an event
- **`src/check_groups.py`**: Display phase group structure and standings
- **`src/debug_phases.py`**: Show detailed phase structure including state, seeds, and bracket types

These scripts are useful for understanding tournament state and troubleshooting data fetching issues.

### Testing/Sandbox
Use `src/_sandbox.py` for experimentation. Current example:
```python
# Fetch top 32 teams from an event
event_slug = "tournament/3v3-sam-champions-road-2025/event/3v3-bracket"
top_teams = sgg_t.get_event_top_teams(event_slug, top_n=32)

# Save to JSON
with open(f'../_data/{event_slug.split('/')[1]}.json', 'w', encoding='utf-8') as json_file:
    json.dump(top_teams, json_file, indent=4, ensure_ascii=False)

# Generate wikitext with tabs
print(lp_t.generate_team_cards_tabs_from_json("../_data/3v3-sam-champions-road-2025.json", [12, 32]))
```

### Data Storage
- Tournament JSON data: `_data/{tournament-name}.json`
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
- Country flags use lowercase ISO-2 codes (e.g., "fr", "us")
- Box/Tabs formatting uses `{{box|start}}`, `{{box|break}}`, `{{box|end}}` and `{{Tabs dynamic}}`

#### Template Formats

**Old TeamCard Format:**
- Structure: team name, 3 starters (p1-p3), 1 substitute (s4), 1 coach (c)
- Syntax: `{{TeamCard|team=...|p1=...|p1flag=...|p2=...|p2flag=...}}`
- Wrapped in box templates for visual grouping
- Still supported and used in many tournament pages

**New TeamParticipants Format:**
- More structured format using nested templates
- Syntax: `{{TeamParticipants|{{Opponent|TeamName|players={{Persons|{{Person|PlayerName|flag=xx}}}}}}}`
- Supports variable number of players per team
- Used in newer tournament pages (e.g., Monthly Cash Cups)
- No box wrappers needed - handled by the template itself

### Path Conventions
- Token file: `../../_token/start.gg-token.txt` (relative to `src/tournament_page_filler/startgg_tools.py`)
- Data files: `../_data/` (relative to `src/_sandbox.py`)
- Module imports use `from src.tournament_page_filler import ...` (project root expected in sys.path)

### Code Style
- Encoding: UTF-8 declared in file headers (`# -*- coding: utf-8 -*-`)
- Type hints used in newer code (e.g., `liquipedia_tools.py`)
- Comprehensive docstrings with Args/Returns/Raises sections
- Defensive programming: null checks, graceful degradation on API errors