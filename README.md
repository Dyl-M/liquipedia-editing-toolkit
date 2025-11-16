# Liquipedia Editing Toolkit

Toolkit facilitating Liquipedia pages editing.

## Features

### 1. Tournament Page Filler
Generate Liquipedia TeamCard wikitext from start.gg tournament results:
- Fetch top N teams with placement, player info, and country data
- Generate formatted TeamCards with tabs for different placement ranges
- Query Liquipedia for canonical player names

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

## Project Structure

```
src/
├── tournament_page_filler/  # Generate TeamCards from tournament results
│   ├── startgg_tools.py     # start.gg GraphQL API wrapper
│   └── liquipedia_tools.py  # Liquipedia wikitext generation
├── stream_filler/           # Insert stream links into brackets
│   └── insert_streams.py
└── prizepool_filler/        # Fill prize pool sections automatically
    ├── fill_prize_pool.py   # Main workflow and filling logic
    ├── get_phase_results.py # Handle ongoing tournaments
    └── example_usage.py     # Usage examples
```

