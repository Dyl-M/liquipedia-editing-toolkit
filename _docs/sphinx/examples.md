# Examples

End-to-end recipes for common workflows. The `tools/` package planned for v0.1.0 will fold these
patterns into reusable functions; until then, the examples below show how to compose the
v0.0.3-alpha API directly.

## Fetch top teams from a tournament event

```python
from lptk import StartGGClient

EVENT_SLUG = "tournament/rlcs-2026-europe-open-1/event/3v3-bracket"

with StartGGClient() as client:
    event_id, name = client.get_event_id(EVENT_SLUG)
    teams = client.get_event_standings(event_id, top_n=16)

for team in teams:
    print(f"#{team.placement} — {team.team_name}")
    for player in team.members:
        print(f"   {player}")
```

## Inspect tournament phases

```python
from lptk import StartGGClient

with StartGGClient() as client:
    event_id, _ = client.get_event_id("tournament/<slug>/event/<event-slug>")
    phases = client.get_tournament_phases(event_id)

for phase in phases:
    state = phase.state or "UNKNOWN"
    print(f"{phase.name}: {state}, {phase.num_seeds} seeds, {len(phase.groups)} groups")
```

## Get the set that eliminated a team

```python
from lptk import StartGGClient

EVENT_ID = 123456
ENTRANT_ID = 987654

with StartGGClient() as client:
    set_id = client.get_entrant_last_elimination_set_id(EVENT_ID, ENTRANT_ID)
    if set_id is None:
        print("Team has no completed elimination set yet (still ongoing).")
    else:
        details = client.get_set_details(set_id)
        print(details)
```

## Combine `lptk` with `liquipydia`

Pull tournament results from start.gg and enrich them with player data from the Liquipedia
Database:

```python
from lptk import StartGGClient, get_lpdb_token
from liquipydia import LiquipediaClient

with StartGGClient() as sg, LiquipediaClient("lptk", api_key=get_lpdb_token()) as lp:
    event_id, _ = sg.get_event_id("tournament/<slug>/event/<event-slug>")
    teams = sg.get_event_standings(event_id, top_n=8)

    for team in teams:
        for player in team.members:
            response = lp.players.list("rocketleague", pagename=player.player_tag)
            if response.result:
                print(player.player_tag, "→", response.result[0])
```
