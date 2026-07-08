import datetime

import pytest

from great_expectations.expectations.metrics.column_aggregate_metrics import (
    column_distinct_values,
)


@pytest.mark.unit
def test_coerce_value_set_for_sql_preserves_non_iso_date_like_strings() -> None:
    assert column_distinct_values._coerce_value_set_for_sql(["0-10", "10-20", "20-30"]) == [
        "0-10",
        "10-20",
        "20-30",
    ]


@pytest.mark.unit
def test_coerce_value_set_for_sql_coerces_iso_date_strings() -> None:
    assert column_distinct_values._coerce_value_set_for_sql(["2024-11-19", "2024-11-20"]) == [
        datetime.date(2024, 11, 19),
        datetime.date(2024, 11, 20),
    ]


@pytest.mark.unit
def test_coerce_value_set_for_sql_preserves_invalid_iso_date_strings() -> None:
    assert column_distinct_values._coerce_value_set_for_sql(["2024-13-19"]) == ["2024-13-19"]
