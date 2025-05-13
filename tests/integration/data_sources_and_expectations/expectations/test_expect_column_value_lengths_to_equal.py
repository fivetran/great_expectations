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

DIFFERENT_COL = "some_are_different"
SAME_COL = "all_the_same"

DATA = pd.DataFrame(
    {
        SAME_COL: ["FOO", "BAR", "BAZ", None],
        DIFFERENT_COL: ["FOOD", "BAR", "BAZ", None],
    }
)


@parameterize_batch_for_data_sources(data_source_configs=SQL_DATA_SOURCES, data=DATA)
def test_success_complete__sql(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValueLengthsToEqual(column=SAME_COL, value=3)
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


@parameterize_batch_for_data_sources(data_source_configs=NON_SQL_DATA_SOURCES, data=DATA)
def test_success_complete__non_sql(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnValueLengthsToEqual(column=SAME_COL, value=3)
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValueLengthsToEqual(column=SAME_COL, value=3),
            id="exact_match",
        ),
        pytest.param(
            gxe.ExpectColumnValueLengthsToEqual(column=SAME_COL, value=3, mostly=0.75),
            id="with_mostly",
        ),
        pytest.param(
            gxe.ExpectColumnValueLengthsToEqual(column=DIFFERENT_COL, value=3, mostly=0.1),
            id="different_lengths_with_mostly",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_success(
    batch_for_datasource: Batch, expectation: gxe.ExpectColumnValueLengthsToEqual
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize(
    "expectation",
    [
        pytest.param(
            gxe.ExpectColumnValueLengthsToEqual(column=DIFFERENT_COL, value=3),
            id="wrong_length",
        ),
        pytest.param(
            gxe.ExpectColumnValueLengthsToEqual(column=DIFFERENT_COL, value=3, mostly=0.9),
            id="mostly_too_high",
        ),
        pytest.param(
            gxe.ExpectColumnValueLengthsToEqual(column=SAME_COL, value=4, mostly=0.1),
            id="no_matches",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_failure(
    batch_for_datasource: Batch, expectation: gxe.ExpectColumnValueLengthsToEqual
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success
