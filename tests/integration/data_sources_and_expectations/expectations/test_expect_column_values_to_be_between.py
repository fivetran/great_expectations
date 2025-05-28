from datetime import datetime
from typing import Any
from unittest.mock import ANY

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations import ExpectationSuite
from great_expectations.compatibility import pydantic
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
STRING_COLUMN = "strings"

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
        STRING_COLUMN: ["a", "b", "c", "d", "e", "f"],
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
                column=NUMERIC_COLUMN,
                min_value=0,
                max_value=6,
                strict_min=True,
                strict_max=True,
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


@pytest.mark.parametrize(
    "min_value,max_value,expected_message",
    [
        pytest.param(
            "",
            1,
            "empty strings",
            id="min_value_is_empty_string",
        ),
        pytest.param(
            0,
            "",
            "empty strings",
            id="max_value_is_empty_string",
        ),
        pytest.param(
            None,
            None,
            "min_value and max_value cannot both be None",
            id="both_values_are_none",
        ),
        pytest.param(
            "",
            "",
            "empty strings",
            id="both_values_are_empty_strings",
        ),
    ],
)
@parameterize_batch_for_data_sources(data_source_configs=JUST_PANDAS_DATA_SOURCES, data=DATA)
def test_validation_errors(
    batch_for_datasource: Batch, min_value: Any, max_value: Any, expected_message: str
) -> None:
    """Test that appropriate validation errors are raised for invalid inputs."""
    with pytest.raises(pydantic.ValidationError) as exc:
        gxe.ExpectColumnValuesToBeBetween(
            column=NUMERIC_COLUMN,
            min_value=min_value,
            max_value=max_value,
        )
    error_dict = exc.value.errors()[0]
    actual_message = error_dict["msg"]
    assert expected_message in actual_message


class TestColumnValuesBetweenAgainstInvalidColumn:
    # expect a standard error message, but exclude the column type string, which is backend specific
    EXPECTED_ERROR = "ColumnValuesBetween metrics cannot be computed on column of type"

    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=DATA,
    )
    def test_fails_when_run_against_invalid_column_type(self, batch_for_datasource: Batch) -> None:
        expect = gxe.ExpectColumnValuesToBeBetween(
            column=STRING_COLUMN,
            min_value=0,
            max_value=1,
        )
        result = batch_for_datasource.validate(expect=expect)
        exception_info = list(result.exception_info.values())
        assert len(exception_info) == 1
        assert self.EXPECTED_ERROR in exception_info[0]["exception_message"]

    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=DATA,
    )
    def test_other_expectations_pass_on_failure(self, batch_for_datasource: Batch) -> None:
        """Prior to GX v1.3.8, if ExpectColumnValuesToBeBetween ran against a string column in a
        SQL context, every other expectation would fail with an exception, including metrics for
        unrelated columns. This test ensures that when a user tries to run that expectation
        against an invalid column type, other expectations continue to work as expected.
        """
        expect = ExpectationSuite(
            name="test_suite",
            expectations=[
                gxe.ExpectColumnValuesToBeBetween(
                    column=STRING_COLUMN,
                    min_value=0,
                    max_value=1,
                ),
                # this expectation used to fail because of shared metrics
                gxe.ExpectColumnValuesToNotBeNull(column=STRING_COLUMN),
                # this expectation also used to fail despite not sharing metrics
                gxe.ExpectColumnValuesToNotBeNull(
                    column=NUMERIC_COLUMN,
                ),
            ],
        )
        result = batch_for_datasource.validate(expect=expect)
        # expect only one ExpectationResult to have an error
        results_with_errors = [
            result
            for result in result.results
            if result.exception_info.get("raised_exception") is not False
        ]
        assert len(results_with_errors) == 1
        exception_info = list(results_with_errors[0].exception_info.values())
        assert len(exception_info) == 1
        assert self.EXPECTED_ERROR in exception_info[0]["exception_message"]
