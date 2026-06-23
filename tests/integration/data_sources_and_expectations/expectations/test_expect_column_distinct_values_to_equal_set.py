from datetime import datetime

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    ALL_DATA_SOURCES,
    DATA_SOURCES_THAT_SUPPORT_DATE_COMPARISONS,
    JUST_PANDAS_DATA_SOURCES,
)

COL_NAME = "my_col"

ONES_AND_TWOS = pd.DataFrame({COL_NAME: [1, 2, 2, 2]})


@parameterize_batch_for_data_sources(data_source_configs=ALL_DATA_SOURCES, data=ONES_AND_TWOS)
def test_success_complete_results(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnDistinctValuesToEqualSet(column=COL_NAME, value_set=[1, 2])
    result = batch_for_datasource.validate(expectation, result_format=ResultFormat.COMPLETE)
    assert result.success
    assert result.to_json_dict()["result"] == {
        "observed_value": None,
        "unexpected_count": 0,
        "partial_unexpected_list": [],
        "missing_count": 0,
        "partial_missing_list": [],
    }


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES,
    data=pd.DataFrame({COL_NAME: ["foo", "bar"]}),
)
def test_strings(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnDistinctValuesToEqualSet(
        column=COL_NAME, value_set=["foo", "bar"]
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=DATA_SOURCES_THAT_SUPPORT_DATE_COMPARISONS,
    data=pd.DataFrame({COL_NAME: [datetime(2024, 11, 19).date(), datetime(2024, 11, 20).date()]}),  # noqa: DTZ001 # FIXME CoP
)
def test_dates(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnDistinctValuesToEqualSet(
        column=COL_NAME,
        value_set=[datetime(2024, 11, 19).date(), datetime(2024, 11, 20).date()],  # noqa: DTZ001 # FIXME CoP
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=DATA_SOURCES_THAT_SUPPORT_DATE_COMPARISONS,
    data=pd.DataFrame({COL_NAME: [datetime(2024, 11, 19).date(), datetime(2024, 11, 20).date()]}),  # noqa: DTZ001 # FIXME CoP
)
def test_dates_with_str_value_set(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnDistinctValuesToEqualSet(
        column=COL_NAME,
        value_set=[str(datetime(2024, 11, 19).date()), str(datetime(2024, 11, 20).date())],  # noqa: DTZ001 # FIXME CoP
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES, data=pd.DataFrame({COL_NAME: [1, 2, None]})
)
def test_ignores_nulls(batch_for_datasource: Batch) -> None:
    expectation = gxe.ExpectColumnDistinctValuesToEqualSet(column=COL_NAME, value_set=[1, 2])
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.parametrize("value_set", [[1], [1, 4], [1, 2, 3]])
@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES, data=ONES_AND_TWOS
)
def test_fails_if_data_is_not_equal(batch_for_datasource: Batch, value_set: list[int]) -> None:
    expectation = gxe.ExpectColumnDistinctValuesToEqualSet(column=COL_NAME, value_set=value_set)
    result = batch_for_datasource.validate(expectation)
    assert not result.success


@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES,
    data=pd.DataFrame(
        {
            COL_NAME: pd.to_datetime(
                [datetime(2025, 9, 1), datetime(2025, 9, 2), datetime(2025, 9, 3)]  # noqa: DTZ001 # FIXME CoP
            ),
        }
    ),
)
def test_datetime64_ns_with_str_value_set(batch_for_datasource: Batch) -> None:
    """Test that datetime64[ns] columns work with string-formatted datetime value_set."""
    value_set = [
        d.strftime("%Y-%m-%dT%H:%M:%S")
        for d in pd.date_range(
            start=datetime(2025, 9, 1),  # noqa: DTZ001 # FIXME CoP
            end=datetime(2025, 9, 3),  # noqa: DTZ001 # FIXME CoP
            freq="1D",
        )
    ]
    expectation = gxe.ExpectColumnDistinctValuesToEqualSet(column=COL_NAME, value_set=value_set)
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES,
    data=pd.DataFrame(
        {
            COL_NAME: pd.to_datetime(
                [datetime(2025, 9, 1), datetime(2025, 9, 2), datetime(2025, 9, 3)]  # noqa: DTZ001 # FIXME CoP
            ),
        }
    ),
)
def test_datetime64_ns_with_datetime_value_set(batch_for_datasource: Batch) -> None:
    """Test that datetime64[ns] columns work with datetime objects in value_set."""
    value_set = [
        datetime(2025, 9, 1),  # noqa: DTZ001 # FIXME CoP
        datetime(2025, 9, 2),  # noqa: DTZ001 # FIXME CoP
        datetime(2025, 9, 3),  # noqa: DTZ001 # FIXME CoP
    ]
    expectation = gxe.ExpectColumnDistinctValuesToEqualSet(column=COL_NAME, value_set=value_set)
    result = batch_for_datasource.validate(expectation)
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=JUST_PANDAS_DATA_SOURCES,
    data=pd.DataFrame(
        {
            COL_NAME: pd.to_datetime(
                [datetime(2025, 9, 1), datetime(2025, 9, 2), datetime(2025, 9, 3)]  # noqa: DTZ001 # FIXME CoP
            ),
        }
    ),
)
def test_datetime64_ns_with_pd_timestamp_value_set(batch_for_datasource: Batch) -> None:
    """Test that datetime64[ns] columns work with pd.Timestamp objects in value_set."""
    value_set = pd.date_range(
        start=datetime(2025, 9, 1),  # noqa: DTZ001 # FIXME CoP
        end=datetime(2025, 9, 3),  # noqa: DTZ001 # FIXME CoP
        freq="1D",
    ).tolist()
    expectation = gxe.ExpectColumnDistinctValuesToEqualSet(column=COL_NAME, value_set=value_set)
    result = batch_for_datasource.validate(expectation)
    assert result.success


@pytest.mark.unit
def test_spark_connect_compatible() -> None:
    """Reproduces issue #11919: .rdd is not supported in Spark Connect (Databricks).

    ExpectColumnDistinctValuesToEqualSet calls column.distinct_values.missing_from_column
    which internally used .rdd.flatMap(lambda x: x), an API unavailable in Spark Connect.
    This test uses a mock DataFrame that raises on .rdd access to simulate Spark Connect,
    confirming the fix works without accessing .rdd.

    Note: uses a mock DataFrame instead of @parameterize_batch_for_data_sources because
    the bug is specific to Spark Connect (not classic local Spark), and setting up a real
    Spark Connect session locally is not practical. F is also patched so the test does not
    require an active SparkContext.
    """
    from unittest.mock import MagicMock, patch

    from great_expectations.expectations.metrics.column_aggregate_metrics.column_distinct_values_missing_from_column import (
        ColumnDistinctValuesMissingFromColumn,
    )

    class _Row:
        def __init__(self, value):
            self._value = value

        def __getitem__(self, i):
            return self._value

    class _SparkConnectLikeDF:
        """Minimal DataFrame mock simulating Spark Connect: .rdd raises, .collect() works."""

        def __init__(self, rows):
            self._rows = rows

        def select(self, *args):
            return self

        def where(self, *args):
            return self

        def distinct(self):
            return self

        @property
        def rdd(self):
            raise AttributeError(
                "[JVM_ATTRIBUTE_NOT_SUPPORTED] Attribute `rdd` is not supported in Spark Connect"
            )

        def collect(self):
            return self._rows

    mock_df = _SparkConnectLikeDF([_Row("red"), _Row("green"), _Row("blue")])
    mock_engine = MagicMock()
    mock_engine.get_compute_domain.return_value = (mock_df, {}, {"column": "colors"})

    _METRIC_MOD = "great_expectations.expectations.metrics.column_aggregate_metrics.column_distinct_values_missing_from_column"

    # Patch F so F.col() works without an active SparkContext
    with patch(f"{_METRIC_MOD}.F") as mock_F:
        mock_F.col.return_value = MagicMock()

        # Before fix: AttributeError raised when .rdd is accessed inside _spark
        # After fix: .collect() is used instead; returns ["yellow"] as the missing value
        result = ColumnDistinctValuesMissingFromColumn._spark(
            ColumnDistinctValuesMissingFromColumn,
            execution_engine=mock_engine,
            metric_domain_kwargs={"column": "colors"},
            metric_value_kwargs={"value_set": ["red", "green", "blue", "yellow"]},
        )

    assert result == ["yellow"]
