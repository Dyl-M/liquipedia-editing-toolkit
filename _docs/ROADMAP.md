# LPTK Restructuring Roadmap

This document outlines the complete plan for restructuring the Liquipedia Editing Toolkit from its current archived
state (`_archive/src/`) into a modern, maintainable Python package (`lptk/`).

---

## Executive Summary

### Vision

Transform the Liquipedia Editing Toolkit into a professional-grade CLI tool with clean architecture, comprehensive
testing, and excellent developer experience.

### Goals

- **Maintainability**: Clear separation of concerns with single-responsibility modules
- **Usability**: Intuitive CLI with flat command structure
- **Reliability**: 80% minimum test coverage from day one, targeting 90%+ at v1.0.0
- **Extensibility**: Easy to add new data sources or output formats

### Testing Philosophy

Testing is integrated from the first phase, not an afterthought. Every new module must ship with tests maintaining **80%
minimum coverage**. This ensures:

- Bugs are caught early when context is fresh
- Refactoring is safe throughout development
- Code quality remains consistent across phases

### Current State

```
_archive/src/
├── tournament_page_filler/   # Tightly coupled API + formatting logic
├── stream_filler/            # Regex-based wikitext manipulation
└── prize_pool_filler/        # Mixed concerns with duplicated API code
```

### Target State

```
lptk/
├── api/                      # Clean API abstraction layer
│   ├── startgg.py            # start.gg GraphQL client
│   └── liquipedia.py         # Liquipedia API client (reading)
├── wikitext/                 # Wikitext parsing and generation
│   ├── parser.py             # Parse templates from wikitext
│   ├── builder.py            # Build wikitext strings
│   └── templates/            # Template-specific implementations
├── tools/                    # Business logic modules
│   ├── participants.py       # Tournament participants generation
│   ├── prizepool.py          # Prize pool filling
│   └── streams.py            # Stream link insertion
├── cli/                      # Typer-based CLI
│   └── main.py               # Entry point with flat commands
├── models/                   # Pydantic data models
└── config.py                 # Centralized configuration
```

---

## Target Architecture

### Package Structure

```
liquipedia-editing-toolkit/
├── lptk/
│   ├── __init__.py           # Package exports, version
│   ├── config.py             # Settings, paths, constants
│   ├── exceptions.py         # Custom exception hierarchy
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── startgg.py        # StartGGClient class
│   │   └── liquipedia.py     # LiquipediaClient class
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── team.py           # Team, Player models
│   │   └── tournament.py     # Tournament, Phase, Set models
│   │
│   ├── wikitext/
│   │   ├── __init__.py
│   │   ├── parser.py         # Parse templates from wikitext
│   │   ├── builder.py        # Build wikitext strings
│   │   ├── utils.py          # Box/Tabs wrappers, common patterns
│   │   └── templates/        # Template-specific implementations
│   │       ├── __init__.py
│   │       ├── opponent.py   # {{Opponent|...}}
│   │       ├── slot.py       # {{Slot|...}}
│   │       ├── teamcard.py   # {{TeamCard|...}}
│   │       └── teamparticipants.py  # {{TeamParticipants|...}}
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── participants.py   # Tournament participants logic
│   │   ├── prizepool.py      # Prize pool filling logic
│   │   └── streams.py        # Stream insertion logic
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   └── main.py           # Typer app with all commands
│   │
│   └── utils/
│       ├── __init__.py
│       ├── countries.py      # Country code utilities
│       └── phase.py          # Phase ordering utilities
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Shared fixtures
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_wikitext.py
│   │   └── test_utils.py
│   └── integration/
│       ├── test_startgg_api.py
│       └── test_liquipedia_api.py
│
├── pyproject.toml            # Project config with CLI entry point
├── CLAUDE.md                 # Updated with new structure
├── ROADMAP.md                # This file
└── README.md                 # User documentation
```

### Module Responsibilities

| Module                  | Responsibility                                                            |
|-------------------------|---------------------------------------------------------------------------|
| `api/startgg.py`        | All start.gg GraphQL queries, authentication, rate limiting               |
| `api/liquipedia.py`     | Liquipedia API queries, redirect resolution                               |
| `models/`               | Pydantic models for type safety and validation                            |
| `wikitext/parser.py`    | Parse existing wikitext, extract template parameters                      |
| `wikitext/builder.py`   | Build wikitext strings from models                                        |
| `wikitext/templates/`   | Template-specific parsing and generation (Opponent, Slot, TeamCard, etc.) |
| `tools/participants.py` | Fetch teams, orchestrate participant wikitext generation                  |
| `tools/prizepool.py`    | Parse slots, fill prize pool entries                                      |
| `tools/streams.py`      | Insert stream links into bracket wikitext                                 |
| `cli/main.py`           | User-facing commands, argument parsing                                    |
| `config.py`             | Token paths, API URLs, rate limits                                        |

### Dependency Graph

```
cli/main.py
    │
    ├── tools/participants.py ──┬── api/startgg.py
    │                           ├── api/liquipedia.py
    │                           └── wikitext/templates/teamcard.py
    │                           └── wikitext/templates/teamparticipants.py
    │
    ├── tools/prizepool.py ─────┬── api/startgg.py
    │                           ├── wikitext/parser.py
    │                           └── wikitext/templates/opponent.py
    │
    └── tools/streams.py ───────┬── wikitext/parser.py
                                └── wikitext/builder.py
```

---

## Version Milestones

### v0.0.0-alpha - Project Setup (Complete)

**Goal**: Establish project structure and development infrastructure

- [x] Archive legacy code to `_archive/src/`
- [x] Create empty `lptk/` package directory
- [x] Configure `pyproject.toml` with modern tooling
- [x] Set up GitHub Actions CI/CD workflows
- [x] Write comprehensive restructuring roadmap
- [x] Update `CLAUDE.md` with project context

**Deliverables**: Restructured repository ready for development

---

### v0.0.1-alpha - Foundation (Current)

**Goal**: Establish package structure and core infrastructure

- [x] Create `lptk/` package skeleton
- [x] Implement `config.py` with environment-based settings
- [x] Define custom exception hierarchy in `exceptions.py`
- [x] Set up logging configuration
- [x] Update `pyproject.toml` with dependencies and entry points
- [x] Set up `_tests/` structure with pytest and coverage
- [x] Write tests for config and exceptions (100% coverage achieved)
- [x] Create `lptk/README.md` (package overview)
- [x] Create `_tests/README.md` (test suite documentation)

**Deliverables**: Importable package with configuration system and test infrastructure

---

### v0.0.2-alpha - API Layer

**Goal**: Clean, reusable API clients

- [ ] Implement `StartGGClient` class with all GraphQL queries
- [ ] Implement `LiquipediaClient` class with API methods
- [ ] Create Pydantic models for API responses
- [ ] Add rate limiting and retry logic
- [ ] Write unit tests with mocked responses (80%+ coverage for new code)
- [ ] Create `lptk/api/README.md` (API clients documentation)
- [ ] Create `lptk/models/README.md` (data models documentation)

**Deliverables**: Fully functional API layer maintaining 80%+ overall coverage

---

### v0.1.0 - Tools Migration

**Goal**: Port business logic from archived code

- [ ] Implement `wikitext/` module for shared wikitext operations
- [ ] Migrate `tournament_page_filler` to `tools/participants.py`
- [ ] Migrate `prize_pool_filler` to `tools/prizepool.py`
- [ ] Migrate `stream_filler` to `tools/streams.py`
- [ ] Remove code duplication between modules
- [ ] Write tests for tools and wikitext modules (80%+ coverage for new code)
- [ ] Create `lptk/wikitext/README.md` (wikitext parsing and generation documentation)
- [ ] Create `lptk/tools/README.md` (business logic tools documentation)
- [ ] Create `lptk/utils/README.md` (utility functions documentation)

**Deliverables**: All three tools working with new architecture, maintaining 80%+ overall coverage

---

### v0.1.1 - CLI Implementation

**Goal**: User-friendly command-line interface

- [ ] Set up Typer application in `cli/main.py`
- [ ] Implement `lptk participants` command
- [ ] Implement `lptk prizepool` command
- [ ] Implement `lptk streams` command
- [ ] Add `--help` documentation for all commands
- [ ] Add `--version` flag
- [ ] Create shell completion scripts
- [ ] Write CLI tests (80%+ coverage for new code)
- [ ] Create `lptk/cli/README.md` (CLI commands documentation)

**Deliverables**: Fully functional CLI tool maintaining 80%+ overall coverage

---

### v0.1.2 - Test Suite Expansion

**Goal**: Expand coverage from 80% to 90%+ and add integration tests

- [ ] Expand unit test coverage to 90%+
- [ ] Add integration tests for API clients (real API, marked slow)
- [ ] Create fixtures with real API response samples
- [ ] Add edge case and error path tests
- [ ] Add CI workflow for automated testing

**Deliverables**: 90%+ coverage with integration tests and CI pipeline

---

### v1.0.0 - Production Ready

**Goal**: Polish and documentation

- [ ] Update README.md with usage examples
- [ ] Update CLAUDE.md with new architecture
- [ ] Add type hints throughout codebase
- [ ] Run mypy for type checking
- [ ] Add pre-commit hooks (ruff, mypy)
- [ ] Remove `_archive/` directory
- [ ] Tag release and publish to PyPI (optional)

**Deliverables**: Production-ready package

---

## Detailed Phases

### Phase 1: Foundation (v0.0.1-alpha) - Complete

#### Tasks

- [x] Create directory structure under `lptk/`
- [x] Create `__init__.py` with version and public exports
- [x] Implement `config.py`:
    - Token path resolution (env var or default)
    - API URLs as constants
    - Rate limit settings
    - Output directory configuration
- [x] Implement `exceptions.py`:
    - `LPTKError` (base)
    - `APIError` (for HTTP/GraphQL errors)
    - `ConfigurationError` (missing token, invalid settings)
    - `WikitextParseError` (malformed input)
- [x] Configure logging with `logging` module
- [x] Update `pyproject.toml`:
    - Add dependencies: `pycountry`, `requests`, `beautifulsoup4`, `pydantic`, `typer`
    - Add dev dependencies: `pytest`, `pytest-cov`, `ruff`, `mypy`
    - Add `[project.scripts]` entry point
- [x] Set up test infrastructure:
    - Create `_tests/` directory structure
    - Create `conftest.py` with basic fixtures
    - Configure pytest in `pyproject.toml`
- [x] Write tests for `config.py` and `exceptions.py`
- [x] Create `lptk/README.md` with package overview
- [x] Create `_tests/README.md` with test suite documentation

#### Dependencies

None (first phase)

#### Acceptance Criteria

- [x] `import lptk` works without errors
- [x] `lptk.config.get_token()` returns token or raises `ConfigurationError`
- [x] Logging outputs to stderr with configurable level
- [x] `uv sync` installs all dependencies
- [x] `pytest --cov=lptk` shows 80%+ coverage (achieved: 100%)
- [x] All tests pass (44 tests)

#### Files Created

```
lptk/__init__.py
lptk/config.py
lptk/exceptions.py
lptk/py.typed
lptk/README.md
_tests/__init__.py
_tests/conftest.py
_tests/test_config.py
_tests/test_exceptions.py
_tests/README.md
```

---

### Phase 2: API Layer (v0.0.2-alpha)

#### Tasks

- [ ] Create `api/__init__.py` with client exports
- [ ] Implement `StartGGClient`:
  ```python
  class StartGGClient:
      def __init__(self, token: str | None = None)
      def get_event_id(self, slug: str) -> tuple[int, str]
      def get_event_standings(self, event_id: int, top_n: int) -> list[Team]
      def get_phase_groups(self, event_id: int) -> list[PhaseGroup]
      def get_phase_group_standings(self, pg_id: int) -> list[Team]
      def get_set_details(self, set_id: int) -> SetDetails
      def get_entrant_sets(self, event_id: int, entrant_id: int) -> list[Set]
  ```
- [ ] Implement `LiquipediaClient`:
  ```python
  class LiquipediaClient:
      def __init__(self, user_agent: str)
      def get_redirect_target(self, title: str) -> str
      def query_page(self, title: str) -> dict
  ```
- [ ] Create Pydantic models in `models/`:
    - `Team`, `Player` in `team.py`
    - `Tournament`, `Phase`, `PhaseGroup`, `Set`, `SetDetails` in `tournament.py`
- [ ] Add rate limiting decorator/mixin
- [ ] Implement retry logic with exponential backoff
- [ ] Write unit tests with mocked API responses
- [ ] Create `lptk/api/README.md` with API clients documentation
- [ ] Create `lptk/models/README.md` with data models documentation

#### Dependencies

- Phase 1 (config, exceptions, test infrastructure)

#### Acceptance Criteria

- [ ] `StartGGClient().get_event_id("tournament/slug/event/main")` returns valid tuple
- [ ] All API methods return typed Pydantic models
- [ ] Rate limiting prevents 429 errors
- [ ] Invalid token raises `ConfigurationError`
- [ ] API errors raise `APIError` with details
- [ ] `pytest --cov=lptk` shows 80%+ coverage
- [ ] All tests pass

#### Files to Create

```
lptk/api/__init__.py
lptk/api/startgg.py
lptk/api/liquipedia.py
lptk/api/README.md
lptk/models/__init__.py
lptk/models/team.py
lptk/models/tournament.py
lptk/models/README.md
tests/test_api_startgg.py
tests/test_api_liquipedia.py
tests/test_models.py
```

---

### Phase 3: Tools Migration (v0.1.0)

#### Tasks

- [ ] Create `wikitext/` module:
    - `wikitext/parser.py` - parse templates from existing wikitext
    - `wikitext/builder.py` - build wikitext strings
    - `wikitext/utils.py` - Box/Tabs wrappers, common regex patterns
    - `wikitext/templates/opponent.py` - {{Opponent|...}} template
    - `wikitext/templates/slot.py` - {{Slot|...}} template
    - `wikitext/templates/teamcard.py` - {{TeamCard|...}} template
    - `wikitext/templates/teamparticipants.py` - {{TeamParticipants|...}} template
- [ ] Create `tools/__init__.py`
- [ ] Migrate participants logic:
    - Port `get_event_top_teams()` cascade algorithm
    - Port smart placement lock-in logic
    - Port pool/bracket enrichment
- [ ] Migrate prizepool logic:
    - Port slot parsing (using `wikitext/parser.py`)
    - Port opponent filling algorithm
    - Port score formatting (including forfeits)
- [ ] Migrate streams logic:
    - Port `add_stream_channel()` regex patterns
    - Port `process_multiple_teams()` batch processing
- [ ] Port utilities:
    - `utils/countries.py` - ISO code normalization
    - `utils/phase.py` - phase ordering logic
- [ ] Write tests for tools, wikitext, and utilities
- [ ] Create `lptk/wikitext/README.md` with wikitext module documentation
- [ ] Create `lptk/tools/README.md` with tools module documentation
- [ ] Create `lptk/utils/README.md` with utilities documentation

#### Dependencies

- Phase 2 (API clients, models)

#### Acceptance Criteria

- [ ] `tools.participants.get_top_teams(slug, 32)` returns same data as archived code
- [ ] `tools.prizepool.fill_prizepool(wikitext, teams)` produces valid output
- [ ] `tools.streams.insert_streams(wikitext, configs)` matches archived behavior
- [ ] No code duplication between tools (shared via api/wikitext/utils)
- [ ] All wikitext templates produce valid Liquipedia wikitext
- [ ] `wikitext.parser` correctly extracts template parameters
- [ ] `pytest --cov=lptk` shows 80%+ coverage
- [ ] All tests pass

#### Files to Create

```
lptk/wikitext/__init__.py
lptk/wikitext/parser.py
lptk/wikitext/builder.py
lptk/wikitext/utils.py
lptk/wikitext/README.md
lptk/wikitext/templates/__init__.py
lptk/wikitext/templates/opponent.py
lptk/wikitext/templates/slot.py
lptk/wikitext/templates/teamcard.py
lptk/wikitext/templates/teamparticipants.py
lptk/tools/__init__.py
lptk/tools/participants.py
lptk/tools/prizepool.py
lptk/tools/streams.py
lptk/tools/README.md
lptk/utils/__init__.py
lptk/utils/countries.py
lptk/utils/phase.py
lptk/utils/README.md
tests/test_wikitext_parser.py
tests/test_wikitext_builder.py
tests/test_wikitext_templates.py
tests/test_tools_participants.py
tests/test_tools_prizepool.py
tests/test_tools_streams.py
tests/test_utils.py
```

---

### Phase 4: CLI Implementation (v0.1.1)

#### Tasks

- [ ] Create `cli/__init__.py`
- [ ] Implement `cli/main.py` with Typer app:
  ```python
  import typer
  app = typer.Typer()

  @app.command()
  def participants(
      event_slug: str,
      top_n: int = 32,
      format: str = "teamparticipants",
      output: Path | None = None,
      segments: list[int] | None = None,
  ): ...

  @app.command()
  def prizepool(
      event_slug: str,
      input_file: Path,
      output_file: Path | None = None,
      phase: str | None = None,
  ): ...

  @app.command()
  def streams(
      input_file: Path,
      output_file: Path | None = None,
      team: list[str] = [],
      channel: list[str] = [],
      type: list[str] = [],
  ): ...
  ```
- [ ] Add `--verbose` / `-v` flag for debug logging
- [ ] Add `--dry-run` flag where applicable
- [ ] Add rich output formatting (tables, colors)
- [ ] Generate shell completion scripts
- [ ] Write CLI tests using Typer's CliRunner
- [ ] Create `lptk/cli/README.md` with CLI commands documentation

#### Dependencies

- Phase 3 (tools modules)

#### Files to Create

```
lptk/cli/__init__.py
lptk/cli/main.py
lptk/cli/README.md
tests/test_cli.py
```

#### Files to Modify

```
pyproject.toml  # Add [project.scripts] entry point
```

#### Acceptance Criteria

- [ ] `lptk --help` shows all commands
- [ ] `lptk participants --help` shows all options
- [ ] `lptk participants "tournament/slug/event/main" --top-n 16` produces output
- [ ] Exit codes: 0 success, 1 user error, 2 API error
- [ ] Output to stdout by default, file with `--output`
- [ ] `pytest --cov=lptk` shows 80%+ coverage
- [ ] All tests pass

---

### Phase 5: Test Suite Expansion (v0.1.2)

#### Tasks

- [ ] Expand test coverage from 80% to 90%+
- [ ] Add edge case tests for all modules
- [ ] Add error path and exception tests
- [ ] Add integration tests with real API calls:
    - `test_integration_startgg.py` - real API (marked slow)
    - `test_integration_liquipedia.py` - real API (marked slow)
- [ ] Create fixtures with real API response samples
- [ ] Add GitHub Actions workflow for CI
- [ ] Configure coverage thresholds in CI (fail if < 80%)

#### Dependencies

- Phase 4 (complete implementation with 80%+ coverage)

#### Acceptance Criteria

- [ ] `pytest` runs all tests successfully
- [ ] `pytest --cov=lptk` shows 90%+ coverage
- [ ] `pytest -m "not slow"` skips integration tests
- [ ] CI runs tests on every push/PR
- [ ] CI fails if coverage drops below 80%
- [ ] Coverage report uploaded to CI artifacts

#### Files to Create

```
tests/integration/__init__.py
tests/integration/test_integration_startgg.py
tests/integration/test_integration_liquipedia.py
tests/fixtures/                    # Real API response samples
.github/workflows/test.yml
```

---

### Phase 6: Production Ready (v1.0.0)

#### Tasks

- [ ] Update `README.md`:
    - Installation instructions
    - Quick start guide
    - Command reference
    - Examples with real tournament slugs
- [ ] Update `CLAUDE.md`:
    - Remove archived code references
    - Document new architecture
    - Update code examples
- [ ] Add comprehensive type hints
- [ ] Run `mypy --strict` and fix issues
- [ ] Ensure `py.typed` marker file exists (PEP 561 compliance for typed package distribution)
- [ ] Set up pre-commit hooks:
    - ruff (linting + formatting)
    - mypy (type checking)
    - pytest (quick tests)
- [ ] Remove `_archive/` directory
- [ ] Create git tag `v1.0.0`
- [ ] (Optional) Publish to PyPI

#### Dependencies

- Phase 5 (tests passing)

#### Acceptance Criteria

- [ ] `mypy lptk --strict` passes
- [ ] `ruff check lptk` passes
- [ ] `pre-commit run --all-files` passes
- [ ] README contains working examples
- [ ] No references to `_archive/` remain
- [ ] Package installable via `pip install .`

#### Files to Modify

```
README.md
CLAUDE.md
pyproject.toml
.pre-commit-config.yaml (create)
```

#### Files to Delete

```
_archive/  (entire directory)
```

---

## Future Features

The following features are not part of the initial restructuring but could be added in future versions:

### Multi-Game Support

- Abstract game-specific logic (player counts, template formats)
- Add support for other Liquipedia wikis (Dota 2, CS2, LoL)
- Configuration-based game selection

### GUI Wrapper

- Web-based interface using FastAPI + htmx
- Desktop app using textual or PyQt
- Visual bracket preview

### Liquipedia Direct Editing

- OAuth authentication with Liquipedia
- Direct page editing via MediaWiki API
- Edit preview and diff view
- Watchlist integration

### Tournament Templates Library

- Pre-built templates for common tournament formats
- Template validation and linting
- Community template sharing

### Batch Processing

- Process multiple tournaments from a list
- Scheduled updates for ongoing events
- Queue system for rate limiting

### Advanced Features

- Historical data tracking and comparison
- Tournament statistics generation
- Team roster change detection
- Automatic flag updates from player pages

### Developer Experience

- Plugin system for custom formatters
- API response caching with TTL
- Offline mode with cached data
- Debug mode with raw API logging

---

## Technical Debt to Address

During migration, the following issues from the archived code should be fixed:

1. **Hardcoded paths**: Replace `../../_token/` with config-based resolution
2. **Duplicated API calls**: Centralize in `StartGGClient`
3. **Mixed concerns**: Separate API calls from wikitext formatting
4. **No error recovery**: Add retry logic for transient failures
5. **Global state**: Remove module-level token loading
6. **Missing types**: Add Pydantic models for all data structures
7. **No tests**: Maintain 80%+ coverage from day one, target 90%+ at v1.0.0
8. **Inconsistent logging**: Standardize with `logging` module

---

## Documentation Convention

Each module and submodule must have its own `README.md` file explaining:

- Purpose and responsibility of the module
- Public API / exported functions and classes
- Usage examples
- Dependencies on other modules

```
lptk/
├── README.md              # Package overview
├── api/
│   └── README.md          # API clients documentation
├── models/
│   └── README.md          # Data models documentation
├── wikitext/
│   └── README.md          # Wikitext parsing and generation documentation
├── tools/
│   └── README.md          # Business logic tools documentation
├── cli/
│   └── README.md          # CLI commands documentation
└── utils/
    └── README.md          # Utility functions documentation
```

---

## Notes

- Preserve backward compatibility with existing `_data/` JSON format
- Maintain support for both TeamCard and TeamParticipants formats
- Keep rate limiting delays to avoid API bans
- Test with real tournament data before removing archived code
- **Testing requirement**: Every phase must maintain 80%+ code coverage before merging
- **Documentation requirement**: Each module must include a README.md before phase completion
