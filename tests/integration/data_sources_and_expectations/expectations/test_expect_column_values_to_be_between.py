from datetime import datetime
from unittest.mock import ANY

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    JUST_PANDAS_DATA_SOURCES,
    NON_SQL_DATA_SOURCES,
    SQL_DATA_SOURCES,
)

NUMERIC_COLUMN = "numbers"
DATE_COLUMN = "dates"

DATA = pd.DataFrame(
    {
        NUMERIC_COLUMN: [1, 2, 3, 4, 5, None],
        DATE_COLUMN: [
            datetime(2023, 1, 1).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2023, 6, 15).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2023, 12, 31).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2024, 1, 1).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2024, 6, 15).date(),  # noqa: DTZ001 # FIXME CoP
            None,
        ],
    },
    dtype="object",
)


@parameterize_batch_for_data_sources(data_source_configs=SQL_DATA_SOURCES, data=DATA)
def test_success_complete_sql(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToBeBetween(column=NUMERIC_COLUMN, min_value=1, max_value=5)
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success
    assert result.to_json_dict()["result"] == {
        "element_count": 6,
        "unexpected_count": 0,
        "unexpected_percent": 0.0,
        "partial_unexpected_list": [],
        "missing_count": 1,
        "missing_percent": pytest.approx(100 / 6),
        "unexpected_percent_total": 0.0,
        "unexpected_percent_nonmissing": 0.0,
        "partial_unexpected_counts": [],
        "unexpected_list": [],
        "unexpected_index_query": ANY,
    }


@parameterize_batch_for_data_sources(data_source_configs=NON_SQL_DATA_SOURCES, data=DATA)
def test_success_complete_non_sql(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToBeBetween(column=NUMERIC_COLUMN, min_value=1, max_value=5)
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValuesToBeBetween(column=NUMERIC_COLUMN, min_value=1, max_value=5),
            id="basic_numeric_test",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeBetween(
                column=DATE_COLUMN,
                min_value=datetime(2023, 1, 1).date(),  # noqa: DTZ001 # FIXME CoP
                max_value=datetime(2024, 12, 31).date(),  # noqa: DTZ001 # FIXME CoP
            ),
            id="dates",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeBetween(
                column=NUMERIC_COLUMN, min_value=0, max_value=6, strict_min=True, strict_max=True
            ),
            id="strict_bounds",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeBetween(column=NUMERIC_COLUMN, min_value=1),
            id="just_min",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeBetween(column=NUMERIC_COLUMN, max_value=5),
            id="just_max",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeBetween(
                column=NUMERIC_COLUMN, min_value=2, max_value=5, mostly=0.8
            ),
            id="mostly",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnValuesToBeBetween,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValuesToBeBetween(column=NUMERIC_COLUMN, min_value=2, max_value=4),
            id="values_outside_range",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeBetween(
                column=DATE_COLUMN,
                min_value=datetime(2024, 1, 1).date(),  # noqa: DTZ001 # FIXME CoP
                max_value=datetime(2024, 12, 31).date(),  # noqa: DTZ001 # FIXME CoP
            ),
            id="dates_outside_range",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeBetween(
                column=NUMERIC_COLUMN, min_value=2, max_value=5, mostly=0.9
            ),
            id="mostly_requirement_not_met",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeBetween(
                column=NUMERIC_COLUMN,
                min_value=1,
                max_value=5,
                strict_min=True,
                strict_max=True,
            ),
            id="strict_bounds",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnValuesToBeBetween,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success
