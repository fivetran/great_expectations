import pytest

from great_expectations.compatibility import pydantic
from great_expectations.expectations.core import ExpectTableColumnsToMatchOrderedList


@pytest.mark.unit
@pytest.mark.parametrize("invalid_column_list", [None, [], set()])
def test_expect_table_columns_to_match_ordered_list_rejects_none_and_empty(invalid_column_list):
    with pytest.raises(pydantic.ValidationError):
        ExpectTableColumnsToMatchOrderedList(column_list=invalid_column_list)


@pytest.mark.unit
@pytest.mark.parametrize("valid_column_list", [["a", "b"], {"a", "b"}, {"$PARAMETER": "cols"}])
def test_expect_table_columns_to_match_ordered_list_accepts_non_empty(valid_column_list):
    exp = ExpectTableColumnsToMatchOrderedList(column_list=valid_column_list)
    assert exp.column_list == valid_column_list
