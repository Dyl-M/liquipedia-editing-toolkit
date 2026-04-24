# lptk.api

API clients for external services.

> **Liquipedia API access** is delegated to the [`liquipydia`](https://github.com/Dyl-M/liquipydia) library (v0.1.0+),
> which is a dedicated wrapper around the Liquipedia DB API v3. Install it alongside `lptk` and import clients/models
> directly from `liquipydia`.

## StartGGClient

Client for the start.gg GraphQL API.

### Basic Usage

```python
from lptk.api import StartGGClient

# Using context manager (recommended)
with StartGGClient() as client:
    # Get event ID from slug
    event_id, name = client.get_event_id("tournament/rlcs-2024/event/main")
    print(f"Event: {name} (ID: {event_id})")

    # Get top 16 standings
    teams = client.get_event_standings(event_id, top_n=16)
    for team in teams:
        print(f"#{team.placement} {team.team_name}")
```

### Available Methods

| Method                                                      | Description                              |
|-------------------------------------------------------------|------------------------------------------|
| `get_event_id(slug)`                                        | Get event ID and name from URL slug      |
| `get_event_standings(event_id, top_n)`                      | Get event-level standings                |
| `get_tournament_phases(event_id)`                           | Get all phases with metadata             |
| `get_phase_group_standings(phase_group_id)`                 | Get standings from a phase group         |
| `get_phase_group_seeds(phase_group_id)`                     | Get seeds from a phase group             |
| `get_set_details(set_id)`                                   | Get match details (scores, winner, etc.) |
| `get_entrant_last_elimination_set_id(event_id, entrant_id)` | Get elimination set ID                   |
| `has_incomplete_sets(event_id, entrant_id)`                 | Check if entrant is still playing        |

### Custom Token

```python
# Use explicit token instead of config
client = StartGGClient(token="your-api-token")
```

## Error Handling

```python
from lptk.api import StartGGClient
from lptk.exceptions import StartGGAPIError

try:
    with StartGGClient() as client:
        event_id, name = client.get_event_id("invalid-slug")
except StartGGAPIError as e:
    print(f"start.gg error: {e}")
    if e.status_code:
        print(f"HTTP status: {e.status_code}")
```

## Rate Limiting

- **StartGGClient**: `LPTK_RATE_LIMIT_DELAY` (default: 0.5s)

## Retry Logic

All API calls use exponential backoff retry on:

- Network errors
- HTTP 429 (Too Many Requests)
- HTTP 5xx (Server errors)

Default: 3 retries with 1s → 2s → 4s delays.
