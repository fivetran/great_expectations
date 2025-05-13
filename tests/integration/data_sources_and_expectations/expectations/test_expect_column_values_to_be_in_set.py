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
NULLS_COLUMN = "nulls"

DATA = pd.DataFrame(
    {
        NUMBERS_COLUMN: [1, 2, 3],
        STRINGS_COLUMN: ["a", "b", "c"],
        DATES_COLUMN: [
            datetime(2024, 1, 1).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2024, 2, 1).date(),  # noqa: DTZ001 # FIXME CoP
            datetime(2024, 3, 1).date(),  # noqa: DTZ001 # FIXME CoP
        ],
        NULLS_COLUMN: [1, None, 3],
    },
    dtype="object",
)


@parameterize_batch_for_data_sources(data_source_configs=NON_SQL_DATA_SOURCES, data=DATA)
def test_success_complete_non_sql(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToBeInSet(column=NUMBERS_COLUMN, value_set=[1, 2, 3])
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success


@parameterize_batch_for_data_sources(data_source_configs=SQL_DATA_SOURCES, data=DATA)
def test_success_complete_sql(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToBeInSet(column=NUMBERS_COLUMN, value_set=[1, 2, 3])
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success
    assert result.to_json_dict()["result"] == {
        "element_count": 3,
        "unexpected_count": 0,
        "unexpected_percent": 0.0,
        "partial_unexpected_list": [],
        "missing_count": 0,
        "missing_percent": 0.0,
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
            gxe.ExpectColumnValuesToBeInSet(column=NUMBERS_COLUMN, value_set=[1, 2, 3]),
            id="basic_number_set",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInSet(column=STRINGS_COLUMN, value_set=["a", "b", "c"]),
            id="string_set",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInSet(
                column=DATES_COLUMN,
                value_set=[
                    datetime(2024, 1, 1).date(),  # noqa: DTZ001 # FIXME CoP
                    datetime(2024, 2, 1).date(),  # noqa: DTZ001 # FIXME CoP
                    datetime(2024, 3, 1).date(),  # noqa: DTZ001 # FIXME CoP
                ],
            ),
            id="date_set",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInSet(column=NUMBERS_COLUMN, value_set=[1, 2, 3, 4]),
            id="superset",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInSet(column=NUMBERS_COLUMN, value_set=[1, 2], mostly=0.66),
            id="mostly_in_set",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInSet(column=NULLS_COLUMN, value_set=[1, 3]),
            id="ignore_nulls",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnValuesToBeInSet,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValuesToBeInSet(column=NUMBERS_COLUMN, value_set=[1, 2]),
            id="incomplete_number_set",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInSet(column=NUMBERS_COLUMN, value_set=[1, 2], mostly=0.7),
            id="mostly_threshold_not_met",
        ),
        pytest.param(
            gxe.ExpectColumnValuesToBeInSet(column=NUMBERS_COLUMN, value_set=[]),
            id="empty_set",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(
    batch_for_datasource: Batch,
    expectation: gxe.ExpectColumnValuesToBeInSet,
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success


@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES, data=pd.DataFrame({NUMBERS_COLUMN: []})
)
def test_empty_data_empty_set(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValuesToBeInSet(column=NUMBERS_COLUMN, value_set=[])
    result = batch_for_datasource.validate(expectation)
    assert result.success
