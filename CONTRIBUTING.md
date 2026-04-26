# Contributing to `liquipedia-editing-toolkit`

Thanks for your interest in contributing to **`liquipedia-editing-toolkit`** (the `lptk` package)! Here are a
few guidelines to help things go smoothly.

## Getting Started

1. Fork the repository and clone your fork.
2. Create a new branch from `dev` for your work:

   ```bash
   git checkout -b your-branch-name dev
   ```

3. Install all development dependencies:

   ```bash
   uv sync --group dev
   ```

4. Make your changes, then push to your fork and open a pull request targeting `dev`.

## Development Commands

```bash
# Lint & format
uv run ruff check .              # lint
uv run ruff format --check .     # format check
uv run ruff check --fix .        # auto-fix lint issues
uv run ruff format .             # auto-format

# Type check
uv run mypy lptk

# Tests
uv run pytest                                            # full test suite
uv run coverage run -m pytest && uv run coverage report  # with coverage

# Documentation
uv sync --group docs                                               # install docs dependencies
uv run sphinx-build -b html _docs/sphinx _docs/sphinx/_build/html  # one-off build
uv run sphinx-autobuild _docs/sphinx _docs/sphinx/_build/html      # live preview with hot reload
```

## Branch Strategy

The repository has two long-lived branches:

- `main` — always releasable, tagged for releases
- `dev` — integration branch for ongoing work

All work happens on short-lived branches created from `dev`. When `dev` is stable and ready for release, it is
merged into `main` via a pull request.

```
feat-xyz  ──► dev  ──► main
fix-abc   ──►     (PR + merge)
```

### Merge Strategy

| Target | Allowed merge methods | Notes                                           |
|--------|-----------------------|-------------------------------------------------|
| `main` | **Squash only**       | One commit per release, linear history enforced |
| `dev`  | **Squash or rebase**  | Linear history enforced, no merge commits       |

All commit messages (including squash commits) must follow
[Conventional Commits](https://www.conventionalcommits.org/) format so that semantic release can determine
version bumps automatically.

Examples: `feat: add wikitext parser`, `fix: handle 429 rate limit`, `docs: update contributing guide`.

### Branch Protection

Both `main` and `dev` are protected by rulesets:

- **No direct pushes to `main`** — all changes require a PR
- **Direct pushes to `dev`** are allowed for repository maintainers only (e.g., changelog updates, quick fixes)
- **Required status checks** on both branches: `Lint & Format`, `Type Check`, `Tests`
- **`main` requires checks to be up to date** with the target branch before merging
- **No force pushes or branch deletion** on either branch
- **Stale reviews are dismissed** on push to `main`
- **All review conversations must be resolved** before merging to `main`

### Branch Naming

Use descriptive prefixes:

- `feat-*` for new features
- `fix-*` for bug fixes
- `docs-*` for documentation changes

## Pull Requests

- Keep PRs focused on a single change.
- Fill in the PR template when opening your pull request.
- Make sure CI checks pass before requesting review.

## Reporting Bugs & Requesting Features

- Use the [issue templates](https://github.com/Dyl-M/liquipedia-editing-toolkit/issues/new/choose) provided in
  the repository.
- For security vulnerabilities, follow the process described in
  [SECURITY.md](https://github.com/Dyl-M/liquipedia-editing-toolkit/blob/main/SECURITY.md).

## Code of Conduct

Be respectful and constructive. Harassment or abusive behavior will not be tolerated.

## License

By contributing, you agree that your contributions will be licensed under the
[MIT License](https://github.com/Dyl-M/liquipedia-editing-toolkit/blob/main/LICENSE).
