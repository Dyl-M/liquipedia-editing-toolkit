# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.3-alpha] - 2026-04-30

### Added

- `CONTRIBUTING.md` — branch model (`main` + `dev` + short-lived feature branches), Conventional Commits
  guidance, merge strategy table, branch protection rules, branch-naming prefixes, dev-command quick
  reference (linting, type-check, tests, docs).
- `SECURITY.md` — vulnerability reporting policy (private email and GitHub Security Advisories), SLA
  (72 h acknowledgement, 7 d status update), coordinated-disclosure stance.
- `.github/pull_request_template.md` and `.github/ISSUE_TEMPLATE/{issue_report,feature_request}.yml` —
  structured PR and issue forms aligned with the
  [`liquipydia`](https://github.com/Dyl-M/liquipydia) playbook.
- README "Documentation" section with link to upcoming Sphinx site at
  `https://dyl-m.github.io/liquipedia-editing-toolkit/`.
- README "Data License" section covering start.gg developer terms and Liquipedia CC-BY-SA 3.0
  attribution requirements.

### Changed

- README restructured to mirror `liquipydia`'s top-level section list
  (About → Project Structure → API Access → Installation → Quick Start → Documentation → Development →
  License → Data License → Contributing → Security).
- `lptk/README.md` version banner bumped to `0.0.3-alpha`; project standards-alignment milestone called
  out explicitly.

### Fixed

- Documented credential path corrected to `.tokens/` (plural) across `README.md`, `lptk/README.md`,
  `CHANGELOG.md` and `_docs/ROADMAP.md` to match the actual default in `lptk/config.py` and the
  `.gitignore` entry.

## [0.0.2-alpha] - 2026-04-26

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
- Credentials moved from flat text files under `_token/` to JSON files under `.tokens/`:
  `.tokens/local_keys.json` (runtime keys — `startgg`, `lpdb`) and `.tokens/repo_keys.json`
  (local tooling keys — `pat`; not loaded by `lptk`)
- `Settings.token_path` renamed to `Settings.local_keys_path`; env var `LPTK_TOKEN_PATH`
  renamed to `LPTK_LOCAL_KEYS_PATH` (**breaking**)
- `get_token()` now reads the `startgg` field of `.tokens/local_keys.json` instead of a plain
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

[Unreleased]: https://github.com/Dyl-M/liquipedia-editing-toolkit/compare/v0.0.3-alpha...HEAD
[0.0.3-alpha]: https://github.com/Dyl-M/liquipedia-editing-toolkit/compare/v0.0.2-alpha...v0.0.3-alpha
[0.0.2-alpha]: https://github.com/Dyl-M/liquipedia-editing-toolkit/compare/v0.0.1-alpha...v0.0.2-alpha
[0.0.1-alpha]: https://github.com/Dyl-M/liquipedia-editing-toolkit/compare/v0.0.0-alpha...v0.0.1-alpha
[0.0.0-alpha]: https://github.com/Dyl-M/liquipedia-editing-toolkit/releases/tag/v0.0.0-alpha
