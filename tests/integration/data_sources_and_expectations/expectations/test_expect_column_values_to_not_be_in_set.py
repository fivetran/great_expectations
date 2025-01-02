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

NUMBERS_COLUMN = "numbers"
STRINGS_COLUMN = "strings"
DATES_COLUMN = "dates"

DATA = pd.DataFrame(
    {
        NUMBERS_COLUMN: [1, 2, 3, None],
        STRINGS_COLUMN: ["a", "b", "c", None],
        DATES_COLUMN: [
            datetime(2024, 1, 1).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2024, 2, 1).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2024, 3, 1).date(),  # noqa: DTZ001 # FIXME CoP
            None,
        ],
    },
    dtype="object",
)


@parameterize_batch_for_data_sources(data_source_configs=NON_SQL_DATA_SOURCES, data=DATA)
def test_success_complete_non_sql(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToNotBeInSet(column=NUMBERS_COLUMN, value_set=[4, 5])
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success


@parameterize_batch_for_data_sources(data_source_configs=SQL_DATA_SOURCES, data=DATA)
def test_success_complete_sql(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToNotBeInSet(column=NUMBERS_COLUMN, value_set=[4, 5])
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success
    assert result.to_json_dict()["result"] == {
        "element_count": 4,
        "unexpected_count": 0,
        "unexpected_percent": 0.0,
        "partial_unexpected_list": [],
        "missing_count": 1,
        "missing_percent": 25.0,
        "unexpected_percent_total": 0.0,
        "unexpected_percent_nonmissing": 0.0,
        "partial_unexpected_counts": [],
        "unexpected_list": [],
        "unexpected_index_query": ANY,
    }


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValuesToNotBeInSet(column=NUMBERS_COLUMN, value_set=[4, 5]),
            id="no_overlap",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToNotBeInSet(column=STRINGS_COLUMN, value_set=["d", "e"]),
            id="strings",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToNotBeInSet(
                column=DATES_COLUMN,
                value_set=[
                    datetime(2024, 4, 1).date(),  # noqa: DTZ001 # FIXME CoP
                    datetime(2024, 5, 1).date(),  # noqa: DTZ001 # FIXME CoP
                ],
            ),
            id="dates",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToNotBeInSet(
                column=NUMBERS_COLUMN, value_set=[3, 4, 5], mostly=0.6
            ),
            id="mostly",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnValuesToNotBeInSet,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES, data=pd.DataFrame({NUMBERS_COLUMN: []})
)
def test_empty_data(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToNotBeInSet(column=NUMBERS_COLUMN, value_set=[])
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValuesToNotBeInSet(column=NUMBERS_COLUMN, value_set=[1, 2, 3]),
            id="exact_match",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToNotBeInSet(column=STRINGS_COLUMN, value_set=["a", "b"]),
            id="strings",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToNotBeInSet(
                column=DATES_COLUMN,
                value_set=[
                    datetime(2024, 1, 1).date(),  # noqa: DTZ001 # FIXME CoP
                    datetime(2024, 2, 1).date(),  # noqa: DTZ001 # FIXME CoP
                ],
            ),
            id="dates",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToNotBeInSet(column=NUMBERS_COLUMN, value_set=[3, 4, 5]),
            id="some_overlap",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToNotBeInSet(
                column=NUMBERS_COLUMN, value_set=[3, 4, 5], mostly=0.7
            ),
            id="mostly_not_met",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnValuesToNotBeInSet,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success
