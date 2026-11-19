import pytest

from great_expectations.compatibility import pydantic
from great_expectations.expectations.core import ExpectTableColumnsToMatchSet


@pytest.mark.unit
@pytest.mark.parametrize("invalid_column_set", [None, [], set()])
def test_expect_table_columns_to_match_set_rejects_none_and_empty(invalid_column_set):
    with pytest.raises(pydantic.ValidationError):
        ExpectTableColumnsToMatchSet(column_set=invalid_column_set)


@pytest.mark.unit
@pytest.mark.parametrize("valid_column_set", [["a", "b"], {"a", "b"}, {"$PARAMETER": "cols"}])
def test_expect_table_columns_to_match_set_accepts_non_empty(valid_column_set):
    exp = ExpectTableColumnsToMatchSet(column_set=valid_column_set)
    assert exp.column_set == valid_column_set
