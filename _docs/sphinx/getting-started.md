# Getting started

This page walks through installing `liquipedia-editing-toolkit`, configuring credentials, and
making your first start.gg query.

## Installation

```bash
# With uv (recommended)
uv add liquipedia-editing-toolkit

# With pip
pip install liquipedia-editing-toolkit
```

`lptk` requires Python 3.12+.

## Credentials

Two API tokens are involved:

- **start.gg** — get yours from
  [start.gg Developer Settings](https://start.gg/admin/profile/developer).
- **Liquipedia DB** *(optional)* — request an API key at
  [liquipedia.net/api](https://liquipedia.net/api). The Liquipedia DB key is consumed by the
  external [`liquipydia`](https://github.com/Dyl-M/liquipydia) library, not by `lptk` directly.

Store credentials under `.tokens/` (gitignored) as JSON files grouped by scope:

```
.tokens/
├── local_keys.json    # runtime keys loaded by lptk
└── repo_keys.json     # local-tooling keys (not loaded by lptk)
```

`.tokens/local_keys.json`:

```json
{
  "startgg": "<start.gg api token>",
  "lpdb": "<liquipedia db api key>"
}
```

`startgg` is required. `lpdb` is optional and only read when your code calls
{py:func}`lptk.get_lpdb_token` (typically to pass through to
`liquipydia.LiquipediaClient`).

Override the keys file path via the `LPTK_LOCAL_KEYS_PATH` environment variable if you want it
elsewhere.

## Environment variables

All settings are prefixed with `LPTK_`:

| Variable                | Default                          | Description                                  |
|-------------------------|----------------------------------|----------------------------------------------|
| `LPTK_LOCAL_KEYS_PATH`  | `.tokens/local_keys.json`        | Path to the local JSON keys file             |
| `LPTK_LOG_LEVEL`        | `INFO`                           | Logging level (DEBUG, INFO, WARNING, ERROR)  |
| `LPTK_STARTGG_API_URL`  | `https://api.start.gg/gql/alpha` | start.gg GraphQL endpoint                    |
| `LPTK_RATE_LIMIT_DELAY` | `0.5`                            | Delay between start.gg API calls (seconds)   |
| `LPTK_USER_AGENT`       | _(unset)_                        | Optional User-Agent for API requests         |

## First query

```python
from lptk import StartGGClient

with StartGGClient() as client:
    event_id, event_name = client.get_event_id("tournament/rlcs-2026/event/main")
    print(event_id, event_name)

    teams = client.get_event_standings(event_id, top_n=8)
    for team in teams:
        print(f"{team.placement}. {team.team_name}")
        for player in team.members:
            print(f"   - {player}")
```

## Pairing with `liquipydia`

Liquipedia DB queries are delegated to the [`liquipydia`](https://github.com/Dyl-M/liquipydia)
library. Pass the `lpdb` field from your `.tokens/local_keys.json` directly:

```python
from lptk import get_lpdb_token
from liquipydia import LiquipediaClient

with LiquipediaClient("lptk", api_key=get_lpdb_token()) as lp:
    response = lp.players.list("rocketleague", pagename="Zen")
    for record in response.result:
        print(record)
```

## Next steps

- See [Examples](examples.md) for end-to-end recipes (tournament participants generation, prize
  pool filling, stream link insertion).
- See the [API reference](api/client.rst) for the full surface of `StartGGClient`, models and
  exceptions.
