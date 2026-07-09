# AGENTS.md

Conventions for coding agents (and human contributors) working in this repository. This
complements [CONTRIBUTING.md](./CONTRIBUTING.md) and [DEVELOPMENT.md](./DEVELOPMENT.md), which
cover the full contribution workflow and local environment setup.

## Test markers

Tests are organized with `pytest` markers declared in `pyproject.toml` under
`[tool.pytest.ini_options]`. The two markers that matter most for scoping a run are:

* `unit` — a unit test. These have no external dependencies and should run fast.
* `integration` — an integration test, typically exercising a real backend or an end-to-end
  code path.

Other markers of note:

* `slow` — a test that takes longer than 1 second.
* Backend-specific markers identify tests that depend on a particular execution engine or
  external service, for example `postgresql`, `mysql`, `sql_server`, `snowflake`, `bigquery`,
  `redshift`, `databricks`, `spark`, `spark_connect`, `trino`, `clickhouse`, `singlestore`,
  `athena`, `sqlite`, and `generic_sql`. A test carries one of these markers when it requires
  that backend to be available (e.g., credentials, a running database, or an installed
  optional dependency).

Select or deselect tests by marker expression with `pytest -m`. For example:

```bash
# Run only unit tests
pytest -m unit

# Run everything except slow tests
pytest -m "not slow"

# Run postgresql-dependent tests only
pytest -m postgresql

# Run unit tests, excluding anything also marked slow
pytest -m "unit and not slow"
```

When adding a new test, mark it accurately: `unit` for a fast, dependency-free test; `integration`
plus the relevant backend marker(s) for anything that talks to a real or emulated backend.

## Compatibility-shim import rule

Optional third-party dependencies (e.g., `sqlalchemy`, `pyspark`, cloud-provider SDKs) must not
be imported directly in library code. Instead, import them via the corresponding module under
`great_expectations/compatibility/`, which wraps the import in a `try`/`except ImportError` and
falls back to a `NotImported` sentinel (see `great_expectations/compatibility/not_imported.py`)
when the dependency isn't installed.

This lets `great_expectations/compatibility/sqlalchemy.py` (and its siblings) be imported
unconditionally — the module itself never raises at import time — while any code path that
actually *uses* a missing symbol raises a clear `ModuleNotFoundError` with an install hint, only
at the point of use. This is what allows Great Expectations to degrade gracefully when an
optional dependency isn't installed, rather than failing at import time for users who don't
need that backend.

In practice:

```python
# Correct
from great_expectations.compatibility import sqlalchemy
...
engine = sqlalchemy.create_engine(...)

# Incorrect — do not do this in library code
import sqlalchemy
```

If you need a symbol from an optional dependency that isn't yet exposed in the matching
`great_expectations/compatibility/<library>.py` module, add it there following the existing
`try`/`except (ImportError, AttributeError)` pattern rather than importing the library directly
at the call site.

## Fluent API location

The Fluent Datasources API — the primary interface for configuring datasources and data assets —
lives under `great_expectations/datasource/fluent/`. Changes to datasource or data-asset
configuration behavior generally belong there.

## Local lint and type-checking commands

This project uses `invoke` tasks (defined in `tasks.py`) for linting, formatting, and type
checking, backed by `ruff` and `mypy`. Run these before submitting a change:

```bash
# Lint (ruff check), including formatting
invoke lint

# Check formatting only, without modifying files
invoke fmt --check

# Type-check with mypy, using the same flags as CI
invoke type-check --ci --pretty
```

`invoke lint` runs `ruff format` followed by `ruff check` by default. Pass `--fix` to
`invoke lint` to have `ruff check` attempt automatic fixes.

## Integration test requirement

A behavioral change to a data source, a validation mechanic, or an Expectation requires at
least one integration test in `tests/integration/data_sources_and_expectations`. This directory
contains the shared test utilities and fixtures for exercising Expectations and validation
behavior against real (or realistically emulated) backends, rather than relying solely on unit
tests with mocked components.

If a change of this kind genuinely cannot be covered by a test in that directory, the pull
request description must explain why and describe what coverage exists instead. Don't discover
this exception in review — call it out up front.
