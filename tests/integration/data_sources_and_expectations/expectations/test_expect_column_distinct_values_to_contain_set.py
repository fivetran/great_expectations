from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Literal

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    ALL_DATA_SOURCES,
    DATA_SOURCES_THAT_SUPPORT_DATE_COMPARISONS,
    JUST_PANDAS_DATA_SOURCES,
)

if TYPE_CHECKING:
    from great_expectations.datasource.fluent.interfaces import Batch

COL_NAME = "my_col"

ONES_AND_TWOS = pd.DataFrame({COL_NAME: [1, 2, 2, 2]})


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=ONES_AND_TWOS)
def test_success_complete_results(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnDistinctValuesToContainSet(column=COL_NAME, value_set=[1, 2])
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success
    assert result.to_json_dict()["result"] == {
        "details": {
            "value_counts": [
                {"value": 1, "count": 1},
                {"value": 2, "count": 3},
            ]
        },
        "observed_value": [1, 2],
    }


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES,
    data=pd.DataFrame({COL_NAME: ["foo", "bar"]}),
)
def test_strings(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnDistinctValuesToContainSet(column=COL_NAME, value_set=["foo"])
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=DATA_SOURCES_THAT_SUPPORT_DATE_COMPARISONS,
    data=pd.DataFrame({COL_NAME: [datetime(2024, 11, 19).date(), datetime(2024, 11, 20).date()]}),  # noqa: DTZ001 # FIXME CoP
)
def test_dates(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnDistinctValuesToContainSet(
        column=COL_NAME,
        value_set=[datetime(2024, 11, 19).date()],  # noqa: DTZ001 # FIXME CoP
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=DATA_SOURCES_THAT_SUPPORT_DATE_COMPARISONS,
    data=pd.DataFrame({COL_NAME: [datetime(2024, 11, 19).date(), datetime(2024, 11, 20).date()]}),  # noqa: DTZ001 # FIXME CoP
)
def test_dates_with_str_value_set(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnDistinctValuesToContainSet(
        column=COL_NAME,
        value_set=[str(datetime(2024, 11, 19).date())],  # noqa: DTZ001 # FIXME CoP
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES, data=pd.DataFrame({COL_NAME: [1, 2, None]})
)
def test_ignores_nulls(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnDistinctValuesToContainSet(column=COL_NAME, value_set=[1, 2])
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES, data=pd.DataFrame({COL_NAME: [1, 2, None]})
)
def test_data_is_superset(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnDistinctValuesToContainSet(column=COL_NAME, value_set=[1])
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES, data=ONES_AND_TWOS
)
def test_failure(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnDistinctValuesToContainSet(column=COL_NAME, value_set=[1, 2, 3])
    result = batch_for_datasource.validate(expectation)
    assert not result.success


# Result format tests


@pytest.mark.parametrize(
    "result_format,expected_result_keys",
    [
        pytest.param("BOOLEAN_ONLY", set(), id="boolean_only"),
        pytest.param("BASIC", {"observed_value"}, id="basic"),
        pytest.param("SUMMARY", {"observed_value"}, id="summary"),
        pytest.param("COMPLETE", {"observed_value", "details"}, id="complete"),
    ],
)
@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES, data=ONES_AND_TWOS
)
def test_result_format_success(
    batch_for_datasource: Batch,
    result_format: Literal["BOOLEAN_ONLY", "BASIC", "SUMMARY", "COMPLETE"],
    expected_result_keys: set[str],
) -> None:
    """Test that result format controls what's included in the result on success."""
    expectation = gxe.ExpectColumnDistinctValuesToContainSet(column=COL_NAME, value_set=[1, 2])
    result = batch_for_datasource.validate(expectation, result_format=result_format)

    assert result.success

    if result_format == "BOOLEAN_ONLY":
        assert result.result == {}
    else:
        assert set(result.result.keys()) == expected_result_keys


@pytest.mark.parametrize(
    "result_format,expected_result_keys",
    [
        pytest.param("BOOLEAN_ONLY", set(), id="boolean_only"),
        pytest.param("BASIC", {"observed_value", "unexpected_count"}, id="basic"),
        pytest.param("SUMMARY", {"observed_value", "unexpected_count"}, id="summary"),
        pytest.param("COMPLETE", {"observed_value", "unexpected_count", "details"}, id="complete"),
    ],
)
@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES, data=ONES_AND_TWOS
)
def test_result_format_failure(
    batch_for_datasource: Batch,
    result_format: Literal["BOOLEAN_ONLY", "BASIC", "SUMMARY", "COMPLETE"],
    expected_result_keys: set[str],
) -> None:
    """Test that result format controls what's included in the result on failure."""
    # value_set [1, 2, 3] requires 3 but column only has [1, 2]
    expectation = gxe.ExpectColumnDistinctValuesToContainSet(column=COL_NAME, value_set=[1, 2, 3])
    result = batch_for_datasource.validate(expectation, result_format=result_format)

    assert not result.success

    if result_format == "BOOLEAN_ONLY":
        assert result.result == {}
    else:
        assert set(result.result.keys()) == expected_result_keys
        # Verify observed_value contains all distinct values from the column
        assert sorted(result.result["observed_value"]) == [1, 2]
        # Verify unexpected_count reflects number of missing values from set (3 is missing)
        assert result.result["unexpected_count"] == 1


@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES, data=ONES_AND_TWOS
)
def test_failure_complete_results(batch_for_datasource: Batch) -> None:
    """Test that COMPLETE result format includes value_counts in details on failure."""
    expectation = gxe.ExpectColumnDistinctValuesToContainSet(column=COL_NAME, value_set=[1, 2, 3])
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)

    assert not result.success
    result_dict = result.to_json_dict()["result"]

    # Check observed_value contains all distinct values
    assert sorted(result_dict["observed_value"]) == [1, 2]
    # Check unexpected_count
    assert result_dict["unexpected_count"] == 1
    # Check details contains value_counts
    assert "details" in result_dict
    assert "value_counts" in result_dict["details"]
    assert result_dict["details"]["value_counts"] == [
        {"value": 1, "count": 1},
        {"value": 2, "count": 3},
    ]
