import datetime
from typing import TYPE_CHECKING, Any, Union, cast
from unittest import mock

import pytest

from great_expectations.execution_engine import ExecutionEngine, PandasExecutionEngine
from great_expectations.self_check.util import get_test_validator_with_data
from great_expectations.util import isclose
from great_expectations.validator.metric_configuration import MetricConfiguration
from great_expectations.validator.metrics_calculator import MetricsCalculator

if TYPE_CHECKING:
    import pandas as pd

    from great_expectations.validator.validator import Validator


@pytest.fixture
def integer_and_datetime_sample_dataset() -> dict:
    week_idx: int
    return {
        "a": [
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
        ],
        "b": [
            datetime.datetime(2021, 1, 1, 0, 0, 0) + datetime.timedelta(days=(week_idx * 7))  # noqa: DTZ001 # FIXME CoP
            for week_idx in range(12)
        ],
    }


# noinspection PyUnusedLocal
@pytest.mark.parametrize(
    "backend,",
    [
        pytest.param("pandas", marks=pytest.mark.unit),
        pytest.param("sqlite", marks=pytest.mark.sqlite),
    ],
)
def test_column_partition_metric(
    sa,
    in_memory_runtime_context,
    integer_and_datetime_sample_dataset: dict,
    backend: str,
):
    _test_column_partition_metric(
        sa, in_memory_runtime_context, integer_and_datetime_sample_dataset, backend
    )


@pytest.mark.spark
def test_column_partition_metric_for_spark(
    sa,
    in_memory_runtime_context,
    integer_and_datetime_sample_dataset: dict,
    spark_session,
):
    _test_column_partition_metric(
        sa, in_memory_runtime_context, integer_and_datetime_sample_dataset, "spark"
    )


def _test_column_partition_metric(
    sa,
    in_memory_runtime_context,
    integer_and_datetime_sample_dataset: dict,
    backend: str,
):
    """
    Test of "column.partition" metric for both, standard numeric column and "datetime.datetime" valued column.

    The "column.partition" metric depends on "column.max" metric and on "column.max" metric.

    For standard numerical data, test set contains 12 evenly spaced integers.
    For "datetime.datetime" data, test set contains 12 dates, starting with January 1, 2021, separated by 7 days.

    Expected partition boundaries are pre-computed algorithmically and asserted to be "close" to actual metric values.
    """  # noqa: E501 # FIXME CoP
    validator_with_data: Validator = get_test_validator_with_data(
        execution_engine=backend,
        table_name="column_partition_metric_test",
        data=integer_and_datetime_sample_dataset,
        context=in_memory_runtime_context,
    )

    metrics_calculator: MetricsCalculator = validator_with_data.metrics_calculator

    seconds_in_week = 604800

    n_bins = 10

    increment: Union[float, datetime.timedelta]
    idx: int
    element: Union[float, pd.Timestamp]

    desired_metric = MetricConfiguration(
        metric_name="column.partition",
        metric_domain_kwargs={"column": "a"},
        metric_value_kwargs={
            "bins": "uniform",
            "n_bins": n_bins,
            "allow_relative_error": False,
        },
    )
    results, _ = metrics_calculator.compute_metrics(metric_configurations=[desired_metric])

    increment = float(n_bins + 1) / n_bins
    assert all(
        isclose(operand_a=element, operand_b=(increment * idx))
        for idx, element in enumerate(results[desired_metric.id])
    )

    # Test using "datetime.datetime" column.

    desired_metric = MetricConfiguration(
        metric_name="column.partition",
        metric_domain_kwargs={"column": "b"},
        metric_value_kwargs={
            "bins": "uniform",
            "n_bins": n_bins,
            "allow_relative_error": False,
        },
    )
    results, _ = metrics_calculator.compute_metrics(metric_configurations=[desired_metric])

    increment = datetime.timedelta(seconds=(seconds_in_week * float(n_bins + 1) / n_bins))
    assert all(
        isclose(
            operand_a=element.to_pydatetime()
            if isinstance(validator_with_data.execution_engine, PandasExecutionEngine)
            else element,
            operand_b=(datetime.datetime(2021, 1, 1, 0, 0, 0) + (increment * idx)),  # noqa: DTZ001 # FIXME CoP
        )
        for idx, element in enumerate(results[desired_metric.id])
    )


@pytest.mark.unit
def test_get_metric_calls_get_metrics_and_returns_correct_result():
    """
    This basic test insures that MetricsCalculator.get_metric() uses MetricsCalculator.get_metrics() correctly.

    In more detail, the purpose of this basic test is to insure that:
        1) MetricsCalculator.get_metric() calls MetricsCalculator.get_metrics() exactly once for specific "metric_name";
        2) MetricsCalculator.get_metric() correctly retrieves result from dictionary, returned by
           MetricsCalculator.get_metrics() by using the specific "metric_name", mentioned above, as the key.

    In the present test case, the role of "ExecutionEngine" is limited to providing the required constructor argument to
    the "MetricsCalculator" class (one of whose methods is under test); hence, a "DummyExecutionEngine" is employed.

    The "with mock.patch" is used judiciously, trading off the focus on the functionality under test (i.e., avoiding
    "test leakage") against going as far as mocking all non-essential methods and properties, favoring code readability.
    """  # noqa: E501 # FIXME CoP

    class DummyExecutionEngine:
        pass

    execution_engine = cast("ExecutionEngine", DummyExecutionEngine)
    metrics_calculator = MetricsCalculator(execution_engine=execution_engine)

    metric_name = "my_metric_name"
    actual_metric_value = "my_metric_value"
    metric_domain_kwargs: dict = {}

    with mock.patch(
        "great_expectations.validator.metrics_calculator.MetricsCalculator.get_metrics",
        return_value={metric_name: actual_metric_value},
    ) as mock_get_metrics_method:
        metric_configuration = MetricConfiguration(
            metric_name=metric_name,
            metric_domain_kwargs=metric_domain_kwargs,
        )
        resolved_metric_value: Any = metrics_calculator.get_metric(metric=metric_configuration)
        mock_get_metrics_method.assert_called_once_with(metrics={metric_name: metric_configuration})
        assert resolved_metric_value == actual_metric_value


@pytest.mark.unit
def test_head_with_pyspark_style_dataframe_no_reset_index():
    """
    Regression test for issue #11617:
    Ensures that MetricsCalculator.head() does not raise an AttributeError 
    when the underlying data object (e.g., a PySpark DataFrame) 
    does not have a .reset_index() method.
    """
    # 1. Arrange: Initialize MetricsCalculator with a mock engine
    # We use a mock engine because head() internally calls get_metric()
    mock_engine = mock.MagicMock()
    metrics_calculator = MetricsCalculator(execution_engine=mock_engine)

    # Define a dummy object that lacks 'reset_index' to simulate a PySpark DataFrame
    class FakeSparkDataFrame:
        def __repr__(self):
            return "<Fake Spark DataFrame>"

    fake_df = FakeSparkDataFrame()
    
    # Mock get_metric to return our fake Spark-like object
    metrics_calculator.get_metric = mock.MagicMock(return_value=fake_df)

    # 2. Act: Execute head() and ensure it handles the object gracefully
    try:
        result = metrics_calculator.head(n_rows=5)
    except AttributeError as e:
        pytest.fail(
            f"MetricsCalculator.head() failed with AttributeError: {e}. "
            "It should handle objects without a reset_index() method (like PySpark DataFrames)."
        )

    # 3. Assert: Verify the result is returned as-is when reset_index is missing
    assert result == fake_df