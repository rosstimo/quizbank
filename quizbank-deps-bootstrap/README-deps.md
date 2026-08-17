# QuizBank: sane dependency management

You switched machines and the gremlins stole half your tooling. This kills the vibe.
Here's a clean, reproducible setup that doesn't rely on mystery global packages.

## TL;DR

```bash
# optional but recommended
direnv allow  # if you use direnv

# one-time bootstrap
./scripts/bootstrap.sh

# add your real deps as you go
make add-pyyaml
make add-dev-pytest
make lock

# checks
make check

# build (wire this to your real pipeline)
make build
```

## What this does

- **Python env pinned with `uv`**: fast resolver, creates `.venv`, writes `uv.lock`.
  Use `uv sync --frozen` in CI for deterministic installs.
- **`pyproject.toml`**: single source of truth for runtime and dev deps.
- **Pre-commit hooks**: black, ruff, yamllint, codespell, prettier for MD/JSON.
- **Makefile**: boring, explicit targets for setup, lock, lint, build.
- **System tool checks**: `scripts/check_system_deps.sh` fails loudly if `typst`, `pandoc`, etc. are missing.
- **Nix (optional)**: `flake.nix` gives you a pinned dev shell on any machine.
- **direnv (optional)**: `.envrc` auto-activates the venv and loads `.env`.

## CI suggestion (GitHub Actions)

```yaml
name: ci
on:
  push:
  pull_request:

jobs:
  lint-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --frozen
      - run: pip install pre-commit mypy
      - run: pre-commit run --all-files
      - run: mypy . || true
      - run: make build
```

## Adding non-Python tools

If your pipeline uses Typst, Pandoc, LaTeX, Graphviz, ImageMagick, etc., either:
- install them via your package manager, or
- enter the pinned **Nix dev shell**: `nix develop` then `uv sync`

## Migration notes

1. Move any ad-hoc `pip install ...` you remember into `make add-<pkg>` calls.
2. If you used Poetry before, run `uv export` or just `uv add` to re-create `dependencies`.
3. Put real build steps in `make build`. The current one is a stub.
4. Commit everything except `.venv/` and `uv.lock`:
   - Commit `uv.lock` if you want exact reproducibility across machines.
   - Or gitignore `uv.lock` if you prefer resolver freedom per clone.
