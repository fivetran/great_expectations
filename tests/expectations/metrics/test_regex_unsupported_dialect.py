import pytest
from great_expectations.expectations.metrics.column_map_metrics.column_values_match_regex import (
    ColumnValuesMatchRegex,
)

class DummyMSSQLDialect:
    class dialect:
        name = "mssql"

def test_regex_unsupported_dialect_raises_not_implemented_error_with_message():
    fake_dialect = DummyMSSQLDialect()
    raw_fn = ColumnValuesMatchRegex._sqlalchemy.__wrapped__.__wrapped__

    with pytest.raises(NotImplementedError) as exc_info:
        raw_fn(ColumnValuesMatchRegex, "test_col", "^abc$", fake_dialect)

    assert "Regex is not supported for dialect mssql" in str(exc_info.value)
