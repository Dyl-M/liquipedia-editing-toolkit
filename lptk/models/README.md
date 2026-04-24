# lptk.models

Pydantic models for tournament data from start.gg and Liquipedia.

## Models

### Team Models (`team.py`)

#### Player

Represents a tournament participant/player.

```python
from lptk.models import Player

player = Player(
    player_id=12345,
    player_tag="Jstn",
    player_country="us",  # ISO 3166-1 alpha-2 lowercase
)
```

#### Team

Represents a tournament team/entrant with placement and roster.

```python
from lptk.models import Player, Team

team = Team(
    placement=1,
    team_name="NRG Esports",
    members=[
        Player(player_tag="Jstn", player_country="us"),
        Player(player_tag="GarrettG", player_country="us"),
        Player(player_tag="Squishy", player_country="ca"),
    ],
    entrant_id=999,
    elimination_set_id=None,  # None = tournament winner
)

# Check if this is an empty placeholder
if team.is_placeholder:
    print("TBD")
```

### Tournament Models (`tournament.py`)

#### Phase

Represents a tournament phase (stage) containing phase groups.

```python
from lptk.models import Phase, PhaseGroup

phase = Phase(
    id=1,
    name="Day 2 - Playoffs",
    state=3,  # COMPLETED
    num_seeds=16,
    groups=[
        PhaseGroup(id=10, identifier="B1", state=3, num_seeds=8),
        PhaseGroup(id=11, identifier="B2", state=3, num_seeds=8),
    ],
)

if phase.is_completed:
    print("Phase finished")
```

#### SetDetails

Represents a completed match/set with scores.

```python
from lptk.models import SetDetails

details = SetDetails(
    set_id=999,
    identifier="B1 AL",
    winner_id=100,
    winner_name="NRG Esports",
    loser_name="G2 Esports",
    winner_score=4,
    loser_score=2,
)

# Extract bracket position
print(details.bracket_group)  # "B1"
print(details.match_id)  # "AL"

# Format score for display
print(details.format_score())  # "4-2"
```

## State Constants

Phase/PhaseGroup states:

- `1` or `"CREATED"` - Not started
- `2` or `"ACTIVE"` - In progress
- `3` or `"COMPLETED"` - Finished
