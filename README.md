# Liquipedia Editing Toolkit

Toolkit facilitating Liquipedia pages editing.

## Features

### 1. Tournament Page Filler
Generate Liquipedia wikitext from start.gg tournament results:
- **Ongoing Tournament Support:** Fetch data from live tournaments using phase group fallback
- **Smart Placement Lock-in:** Intelligently includes teams with confirmed placements while using empty placeholders for ongoing matches
- **Pool Group Integration:** Enriches team data with pool group and placement information for accurate bracket positioning
- **Two Format Options:**
  - Legacy TeamCard format for older pages
  - Modern TeamParticipants format for newer tournament pages
- Fetch top N teams with placement, player info, and country data
- Generate formatted output with tabs for different placement ranges
- Query Liquipedia for canonical player names
- Automatic detection of completed vs. ongoing tournaments
- Bracket-aware sorting by pool placement and bracket position

### 2. Stream Filler
Insert Twitch/YouTube stream links into Liquipedia match brackets:
- Regex-based wikitext manipulation
- Batch processing for multiple teams
- Support for both Twitch and YouTube

### 3. Prize Pool Filler
**Automatically fill Liquipedia prize pool sections with tournament results:**
- Smart fallback: Uses event standings for completed tournaments, phase results for ongoing ones
- Bracket-aware sorting: Teams ordered by group (B1, B2, ...) then match identifier (AL, AM, ...)
- Elimination tracking: Populates "lastvs" (opponent) and "lastvsscore" (match score) fields
- Forfeit handling: Automatically formats forfeit scores as "FF-W"
- Phase optimization: Skips large phases (>512 teams) to avoid API timeouts

**Quick Start:**

```python
from src.prize_pool_filler.fill_prize_pool import process_prizepool_from_event

process_prizepool_from_event(
    event_slug="tournament/rlcs-2026-europe-open-1/event/3v3-bracket",
    wikitext_path="src/prize_pool_filler/wikitext_input.txt",
    output_path="src/prize_pool_filler/wikitext_output.txt"
)
```

## Setup

### Dependencies
```bash
pip install -r requirements.txt
```

Required packages: `pycountry`, `requests`, `beautifulsoup4`

### API Token
Create a start.gg API token and save it to:
```
_token/start.gg-token.txt
```

This file is gitignored and must be created manually.

## Documentation

See [CLAUDE.md](CLAUDE.md) for detailed architecture, API documentation, and development workflow.

## Quick Start Examples

### Generate TeamParticipants Wikitext

For ongoing or completed tournaments:

```bash
python src/generate_team_participants.py
```

Edit the script to configure your tournament:
```python
EVENT_SLUG = "tournament/your-tournament/event/3v3-bracket"
TOP_N = 32
SEGMENTS = [12, 32]  # Creates "Top 12" and "Places 13-32" tabs
```

See `src/tournament_page_filler/README_TEAM_PARTICIPANTS.md` for detailed documentation.

## Project Structure

```
src/
├── tournament_page_filler/           # Generate TeamCards/TeamParticipants from results
│   ├── startgg_tools.py              # start.gg GraphQL API wrapper
│   ├── liquipedia_tools.py           # Liquipedia wikitext generation
│   └── README_TEAM_PARTICIPANTS.md   # TeamParticipants format guide
├── stream_filler/                    # Insert stream links into brackets
│   └── insert_streams.py
├── prize_pool_filler/                # Fill prize pool sections automatically
│   ├── fill_prize_pool.py            # Main workflow and filling logic
│   ├── get_phase_results.py          # Handle ongoing tournaments
│   └── run_fill.py                   # Quick script to run the filler
├── generate_team_participants.py     # Main script for TeamParticipants generation
├── test_team_participants.py         # Test/demo for both formats
└── check_*.py, debug_*.py            # Debugging utilities for start.gg API
```

