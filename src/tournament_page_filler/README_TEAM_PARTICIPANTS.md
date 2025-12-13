# TeamParticipants Format - Quick Start Guide

This guide explains how to use the new TeamParticipants format generator for Liquipedia tournament pages.

## What's New

### New TeamParticipants Format Support
- Modern Liquipedia template format using nested `{{Opponent}}` and `{{Persons}}` templates
- Supports variable number of players per team
- Automatically generates tabbed sections (e.g., "Top 12", "Places 13-32")
- Works alongside the existing TeamCard format

### Ongoing Tournament Support
- **NEW:** Fetches data from ongoing tournaments using phase group fallback
- Automatically detects when event standings are not yet available
- Falls back to phase group standings for ongoing competitions
- Properly orders teams from multiple phase groups

## Quick Start

### Option 1: Generate from start.gg (Recommended)

Use the `generate_team_participants.py` script:

```bash
python src/generate_team_participants.py
```

**Configuration** (edit the script):

```python
# Set your tournament
EVENT_SLUG = "tournament/3v3-december-mena-monthly-cash-cup/event/3v3-bracket"

# How many teams to fetch
TOP_N = 32

# Tab breakpoints (e.g., [12, 32] creates "Top 12" and "Places 13-32" tabs)
SEGMENTS = [12, 32]

# Output file
OUTPUT_FILE = "_data/output_team_participants.txt"
```

### Option 2: Generate from Existing JSON

If you already have tournament data saved:

```python
# In generate_team_participants.py
USE_EXISTING_JSON = True
JSON_PATH = "_data/your-tournament.json"
SEGMENTS = [16]
```

## Output Format

The script generates Liquipedia wikitext like this:

```wikitext
{{TeamCardToggleButton}}
{{Team card columns start|cols=4}}
{{Tabs dynamic
|name1=Top 12
|name2=Places 13-32
|content1=
{{TeamParticipants
|{{Opponent|Team Name
  |players={{Persons
    |{{Person|PlayerName|flag=xx}}
    |{{Person|PlayerName|flag=xx}}
    |{{Person|PlayerName|flag=xx}}
  }}
}}
...
}}
|content2=
{{TeamParticipants
...
}}
}}
```

## Use Cases

### 1. Ongoing Tournaments
Perfect for Monthly Cash Cups and other live tournaments:
- Automatically fetches current standings from active phase groups
- Updates as pools complete
- No need to wait for the event to finish

### 2. Completed Tournaments
Works seamlessly with finished events:
- Fetches final event standings
- Includes all placement data

### 3. Custom Tab Configurations

```python
# Single tab - Top 16
SEGMENTS = [16]

# Two tabs - Top 12 and Places 13-32
SEGMENTS = [12, 32]

# Three tabs - Top 8, 9-16, 17-32
SEGMENTS = [8, 16, 32]

# No tabs - all teams in one section
SEGMENTS = None
```

## Functions Available

### In `liquipedia_tools.py`

#### TeamParticipants Format (NEW)
- `format_team_participants_opponent_from_entry(entry, remove_empty_optional=False)`
  - Formats a single team as an Opponent entry

- `generate_team_participants_from_json(json_path, remove_empty_optional=False)`
  - Generates TeamParticipants block from JSON

- `generate_team_participants_tabs_from_json(json_path, segments, remove_empty_optional=False)`
  - Generates TeamParticipants with tabs

#### TeamCard Format (Legacy)
- `format_team_card_from_entry(entry, remove_empty_optional=False)`
- `generate_team_cards_from_json(json_path, include_box_wrappers=True)`
- `generate_team_cards_tabs_from_json(json_path, segments, remove_empty_optional=False)`

### In `startgg_tools.py`

- `get_event_top_teams(event_slug, top_n, use_phase_fallback=True)`
  - **Enhanced:** Now supports ongoing tournaments via phase group fallback
  - Set `use_phase_fallback=False` to disable this behavior

## Example: Monthly Cash Cup MENA

```python
from src.tournament_page_filler import liquipedia_tools as lp_t, startgg_tools as sgg_t

# Fetch top 32 teams (works even if tournament is ongoing!)
event_slug = "tournament/3v3-december-mena-monthly-cash-cup/event/3v3-bracket"
teams = sgg_t.get_event_top_teams(event_slug, top_n=32)

# Save to JSON
import json
with open('_data/mena-cup.json', 'w', encoding='utf-8') as f:
    json.dump(teams, f, indent=4, ensure_ascii=False)

# Generate wikitext with tabs
wikitext = lp_t.generate_team_participants_tabs_from_json(
    '_data/mena-cup.json',
    segments=[12, 32],
    remove_empty_optional=True
)

print(wikitext)
```

## Files

- **`src/generate_team_participants.py`** - Main application script
- **`src/test_team_participants.py`** - Test/demo script
- **`output_team_participants.txt`** - Generated wikitext output
- **`_data/*.json`** - Cached tournament data

## Tips

1. **For ongoing tournaments:** The script automatically uses phase group fallback. Just run it normally!

2. **For completed tournaments:** Works the same way - event standings are used when available.

3. **Empty flags:** If a player's country is not set on start.gg, the flag parameter will be empty (`flag=`). This is normal.

4. **Updating data:** Re-run the script to fetch the latest standings from an ongoing tournament.

5. **Custom configurations:** Edit `generate_team_participants.py` to change the event slug, number of teams, or tab structure.

## Troubleshooting

### "No teams fetched"
- Check the event slug is correct
- Verify your start.gg API token exists at `_token/start.gg-token.txt`
- For very early tournaments, phases may not have started yet

### "Skipping phase (too large)"
- Phases with >512 participants are skipped to avoid API timeouts
- This is normal for very large open qualifiers

### Encoding issues on Windows
- The script uses UTF-8 encoding automatically
- Output is saved to file to avoid console encoding issues

## Support

For questions or issues, refer to:
- `CLAUDE.md` - Complete project documentation
- `src/_sandbox.py` - Example usage patterns