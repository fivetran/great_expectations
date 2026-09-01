"""Unit tests for per-expectation schema overrides.

Covers:
- expect_column_values_to_be_of_type pandas-path payload matches MapBasicResult,
  NOT ExpectColumnValuesToBeOfTypeSqlSparkResult.
- expect_column_values_to_be_of_type SQL/Spark-path payload matches the override.
- Extra fields on the override raise pydantic.ValidationError (extra=forbid).

All tests are marked @pytest.mark.unit and run via:
    pytest tests/unit/core/validation_result_schemas/test_schemas_overrides.py -m unit
"""

from __future__ import annotations

import pytest

from great_expectations.compatibility import pydantic
from great_expectations.core.validation_result_schemas.schemas.map_result import (
    MapBasicResult,
)
from great_expectations.core.validation_result_schemas.schemas.per_expectation_overrides import (
    ExpectColumnValuesToBeOfTypeSqlSparkResult,
)

# ---------------------------------------------------------------------------
# Pandas-path: expect_column_values_to_be_of_type emits a map-shaped result
# ---------------------------------------------------------------------------

_PANDAS_RESULT = {
    "element_count": 10,
    "unexpected_count": 0,
    "unexpected_percent": 0.0,
    "partial_unexpected_list": [],
}


@pytest.mark.unit
def test_pandas_path_parses_as_map_basic_result() -> None:
    """The pandas result for expect_column_values_to_be_of_type is map-shaped.

    It must parse as MapBasicResult, confirming it belongs to the Map family.
    """
    m = MapBasicResult.parse_obj(_PANDAS_RESULT)
    assert m.element_count == 10
    assert m.unexpected_count == 0
    assert m.unexpected_percent == 0.0
    assert m.partial_unexpected_list == []


# ---------------------------------------------------------------------------
# SQL/Spark-path: expect_column_values_to_be_of_type emits {observed_value: ...}
# ---------------------------------------------------------------------------

_SQL_SPARK_RESULT = {"observed_value": "str"}


@pytest.mark.unit
def test_sql_spark_path_parses_as_override() -> None:
    """The SQL/Spark result for expect_column_values_to_be_of_type matches the override.

    SQL/Spark bypasses _format_map_output and emits only {observed_value: <type-name>}.
    """
    r = ExpectColumnValuesToBeOfTypeSqlSparkResult(**_SQL_SPARK_RESULT)
    assert r.observed_value == "str"


@pytest.mark.unit
def test_sql_spark_path_observed_value_preserved() -> None:
    """observed_value carries the type name string verbatim."""
    r = ExpectColumnValuesToBeOfTypeSqlSparkResult(observed_value="INTEGER")
    assert r.observed_value == "INTEGER"


# ---------------------------------------------------------------------------
# extra=forbid: unknown fields on the override must raise
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_override_extra_field_raises() -> None:
    """ExpectColumnValuesToBeOfTypeSqlSparkResult rejects unknown extra fields."""
    with pytest.raises(pydantic.ValidationError):
        ExpectColumnValuesToBeOfTypeSqlSparkResult.parse_obj(
            {
                "observed_value": "int",
                "unexpected_extra": "x",
            }
        )
