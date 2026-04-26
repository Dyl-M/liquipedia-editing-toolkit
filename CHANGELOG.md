# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `lptk.api.StartGGClient` — start.gg GraphQL client with bearer-token auth, rate limiting, retries with
  exponential backoff, and context-manager support
- `lptk.models.team` — Pydantic models `Player` and `Team`
- `lptk.models.tournament` — Pydantic models `Phase`, `PhaseGroup`, `SetSlot`, `SetDetails`
- `lptk.api._retry` — retry decorator for transient HTTP failures (429/5xx)
- `liquipydia==0.1.0` runtime dependency for Liquipedia DB API v3 access
- `lptk.get_lpdb_token()` — reads the `lpdb` field of the local keys file for use with
  `liquipydia.LiquipediaClient`
- `lptk.config.LocalKeys` — Pydantic schema for the JSON keys file
- Unit tests for `StartGGClient`, retry logic, Pydantic models, and the new JSON credential flow
  (128 tests, 100% coverage)

### Changed

- Liquipedia DB access delegated to the external
  [`liquipydia`](https://github.com/Dyl-M/liquipydia) library instead of an in-repo client —
  the toolkit only owns the start.gg client and shared models
- Config, README, and ROADMAP updated to reflect the start.gg-only scope of `lptk.api`
- Credentials moved from flat text files under `_token/` to JSON files under `.token/`:
  `.token/local_keys.json` (runtime keys — `startgg`, `lpdb`) and `.token/repo_keys.json`
  (local tooling keys — `pat`; not loaded by `lptk`)
- `Settings.token_path` renamed to `Settings.local_keys_path`; env var `LPTK_TOKEN_PATH`
  renamed to `LPTK_LOCAL_KEYS_PATH` (**breaking**)
- `get_token()` now reads the `startgg` field of `.token/local_keys.json` instead of a plain
  text file

### Removed

- `lptk.api.liquipedia.LiquipediaClient` and its tests (replaced by `liquipydia`)
- `LiquipediaAPIError` exception class
- Liquipedia-specific settings: `liquipedia_token_path`, `liquipedia_api_url`, `liquipedia_wiki`,
  `liquipedia_rate_limit_delay`, `get_liquipedia_token`, `clear_liquipedia_token_cache`

## [0.0.1-alpha] - 2026-01-24

### Added

- New `lptk` package with foundation modules
  - `config.py`: Environment-based settings with pydantic-settings
  - `exceptions.py`: Custom exception hierarchy (LPTKError, APIError, ConfigurationError, etc.)
  - `py.typed`: PEP 561 marker for typed package distribution
- Test suite in `_tests/` with 100% coverage
  - Shared fixtures in `conftest.py`
  - Tests for config and exceptions modules
- Comprehensive restructuring plan in `_docs/ROADMAP.md`
- GitHub Actions workflows for CI/CD
- DeepSource and Dependabot configuration

### Changed

- Restructure project with modern tooling (`pyproject.toml`, `uv.lock`)
- Archive legacy code from `src/` to `_archive/src/`
- Use `@lru_cache` for token caching instead of global variable
- Revise versioning scheme and replace formatters with wikitext module plan

### Fixed

- Use `uv` instead of `pip` in CI and correct coverage module path

## [0.0.0-alpha] - 2025-12-13

### Added

- Initial project structure with three main modules:
  - Tournament Page Filler: Generate TeamCards/TeamParticipants from start.gg data
  - Stream Filler: Insert Twitch/YouTube stream links into Liquipedia brackets
  - Prize Pool Filler: Automated prize pool filling with bracket-aware sorting
- start.gg GraphQL API integration
  - Event and phase data fetching
  - Smart placement lock-in for ongoing tournaments
  - Phase group fallback mechanism
- Liquipedia wikitext generation
  - TeamCard and TeamParticipants format support
  - Box/Tabs formatting utilities
- Player information retrieval from Liquipedia API

### Fixed

- Prevent AttributeError in `_normalize_flag()` when country is None

[0.0.1-alpha]: https://github.com/Dyl-M/liquipedia-editing-toolkit/compare/v0.0.0-alpha...v0.0.1-alpha
[0.0.0-alpha]: https://github.com/Dyl-M/liquipedia-editing-toolkit/releases/tag/v0.0.0-alpha