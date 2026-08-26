from __future__ import annotations

from great_expectations.compatibility.not_imported import NotImported

DUCKDB_NOT_IMPORTED = NotImported(
    "duckdb is not installed, please 'pip install duckdb' or install great_expectations[duckdb]"
)

try:
    import duckdb
except ImportError:
    duckdb = DUCKDB_NOT_IMPORTED  # type: ignore[assignment] # FIXME CoP
