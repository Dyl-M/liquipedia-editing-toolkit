# LPTK | Automate Liquipedia editing from start.gg tournament data

![Python](https://img.shields.io/badge/python-3.12+-blue?logo=python&logoColor=white)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![License](https://img.shields.io/github/license/Dyl-M/liquipedia-editing-toolkit)

![Status](https://img.shields.io/badge/status-alpha-orange?style=flat-square)
[![Lint & Test](https://img.shields.io/github/actions/workflow/status/Dyl-M/liquipedia-editing-toolkit/lint-and-test.yml?label=Lint%20%26%20Test&style=flat-square&logo=github-actions&logoColor=white)](https://github.com/Dyl-M/liquipedia-editing-toolkit/actions/workflows/lint-and-test.yml)
[![DeepSource](https://app.deepsource.com/gh/Dyl-M/liquipedia-editing-toolkit.svg/?label=active+issues&show_trend=false&token=Jkf0lDe06vzL02w3tnFLV3yh)](https://app.deepsource.com/gh/Dyl-M/liquipedia-editing-toolkit/)
[![DeepSource](https://app.deepsource.com/gh/Dyl-M/liquipedia-editing-toolkit.svg/?label=code+coverage&show_trend=false&token=Jkf0lDe06vzL02w3tnFLV3yh)](https://app.deepsource.com/gh/Dyl-M/liquipedia-editing-toolkit/)

## About

**`liquipedia-editing-toolkit`** (the `lptk` package) automates Liquipedia page editing for esports — initially
focused on Rocket League — using tournament data fetched from [start.gg](https://start.gg). The toolkit pairs
a typed start.gg GraphQL client with wikitext generators that produce TeamCards, TeamParticipants,
brackets, and prize pool sections ready to paste into Liquipedia.

Built with [`requests`](https://requests.readthedocs.io/), [`pydantic`](https://docs.pydantic.dev/), and
[`liquipydia`](https://github.com/Dyl-M/liquipydia) (for Liquipedia DB API v3 access).

> **Status:** Alpha — see the [Roadmap](_docs/ROADMAP.md) for progress and the
> [Changelog](CHANGELOG.md) for version history.

## Project Structure

```
lptk/
├── __init__.py       # Package exports, version
├── config.py         # Settings management (pydantic-settings)
├── exceptions.py     # Exception hierarchy (LPTKError, APIError, ...)
├── api/              # API clients
│   ├── startgg.py    # StartGGClient — start.gg GraphQL
│   └── _retry.py     # Retry decorator with exponential backoff
├── models/           # Pydantic data models
│   ├── team.py       # Player, Team
│   └── tournament.py # Phase, PhaseGroup, SetSlot, SetDetails
└── py.typed          # PEP 561 type marker
```

Liquipedia DB access is delegated to the external [`liquipydia`](https://github.com/Dyl-M/liquipydia) library.
Legacy code (TeamCard/TeamParticipants generators, stream filler, prize pool filler) lives under `_archive/`
pending migration to `lptk/tools/` in v0.1.0.

## API Access

Two API tokens are required:

- **start.gg** — get yours from [start.gg Developer Settings](https://start.gg/admin/profile/developer).
- **Liquipedia DB** — request an API key at [liquipedia.net/api](https://liquipedia.net/api). Access is **not
  self-service** and is consumed by the [`liquipydia`](https://github.com/Dyl-M/liquipydia) library; free
  access is available for educational, non-commercial open-source, and community projects.

Credentials live under `.tokens/` (gitignored, created manually) as two JSON files grouped by scope:

```
.tokens/
├── local_keys.json    # runtime keys loaded by lptk
└── repo_keys.json     # local-tooling keys (not loaded by lptk)
```

**`.tokens/local_keys.json`** — runtime keys:

```json
{
  "startgg": "<start.gg api token>",
  "lpdb": "<liquipedia db api key>"
}
```

`startgg` is required; `lpdb` is optional and only needed when your code calls `get_lpdb_token()` (or passes
the key to `liquipydia.LiquipediaClient`).

**`.tokens/repo_keys.json`** — local tooling (CI uses GitHub secrets; `lptk` does not read this file):

```json
{
  "pat": "<github personal access token>"
}
```

Override the keys file path via the `LPTK_LOCAL_KEYS_PATH` environment variable if needed.

## Installation

```bash
# With uv (recommended)
uv add liquipedia-editing-toolkit

# With pip
pip install liquipedia-editing-toolkit
```

Or install from source:

```bash
# With uv
uv add git+https://github.com/Dyl-M/liquipedia-editing-toolkit.git

# With pip
pip install git+https://github.com/Dyl-M/liquipedia-editing-toolkit.git
```

## Quick Start

```python
from lptk import StartGGClient

# Fetch tournament data from start.gg
with StartGGClient() as client:
    event_id, name = client.get_event_id("tournament/rlcs-2026/event/main")
    teams = client.get_event_standings(event_id, top_n=16)
    for team in teams:
        print(f"{team.placement}. {team.team_name}")

# Liquipedia DB access is provided by the liquipydia library
from liquipydia import LiquipediaClient

with LiquipediaClient("my-app", api_key="your-api-key") as lp:
    response = lp.players.list("rocketleague", pagename="Zen")
    for record in response.result:
        print(record)
```

### Environment Variables

All variables are prefixed with `LPTK_`:

| Variable                | Default                          | Description                                 |
|-------------------------|----------------------------------|---------------------------------------------|
| `LPTK_LOCAL_KEYS_PATH`  | `.tokens/local_keys.json`        | Path to the local JSON keys file            |
| `LPTK_LOG_LEVEL`        | `INFO`                           | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LPTK_STARTGG_API_URL`  | `https://api.start.gg/gql/alpha` | start.gg GraphQL endpoint                   |
| `LPTK_RATE_LIMIT_DELAY` | `0.5`                            | Delay between start.gg API calls (seconds)  |
| `LPTK_USER_AGENT`       | _(unset)_                        | Optional User-Agent for API requests        |

> Liquipedia DB API credentials and rate-limiting are configured via the `liquipydia` library — refer to its
> [documentation](https://github.com/Dyl-M/liquipydia) for details.

## Documentation

Full documentation (getting started, examples, API reference) is available at
**[dyl-m.github.io/liquipedia-editing-toolkit](https://dyl-m.github.io/liquipedia-editing-toolkit/)**.

## Development

```bash
# Clone the repository
git clone https://github.com/Dyl-M/liquipedia-editing-toolkit.git
cd liquipedia-editing-toolkit

# Install dependencies (requires uv)
uv sync --group dev

# Run linting
uv run ruff check .
uv run ruff format --check .

# Run type checking
uv run mypy lptk

# Run tests
uv run pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full branch model, merge strategy, and PR workflow.

## License

Code is licensed under the [MIT License](LICENSE).

## Data License

Data returned by the start.gg and Liquipedia APIs is subject to the respective platform terms.

- **start.gg:** see
  the [start.gg APIs Terms of Use](https://www.start.gg/about/apitos).
- **Liquipedia:** data returned by the Liquipedia API is subject to
  [CC-BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) as required by Liquipedia's
  [API Terms of Use](https://liquipedia.net/api-terms-of-use). If you redistribute or display data obtained
  through `liquipydia`, you must comply with the CC-BY-SA 3.0 attribution requirements.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.
