from datetime import datetime

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
from great_expectations.datasource.fluent.interfaces import Batch
from great_expectations.self_check.util import build_spark_engine
from great_expectations.validator.metric_configuration import MetricConfiguration
from tests.expectations.test_util import get_table_columns_metric
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


@pytest.mark.spark
def test_spark_connect_compatible(spark_session, monkeypatch) -> None:
    """Reproduces issue #11919: .rdd is not supported in Spark Connect (Databricks).

    ExpectColumnDistinctValuesToEqualSet calls column.distinct_values.missing_from_column
    which internally used .rdd.flatMap(lambda x: x), an API unavailable in Spark Connect.
    This test patches .rdd to simulate Spark Connect and verifies the metric resolves
    without accessing .rdd.
    """
    pd_df = pd.DataFrame({"colors": ["red", "green", "blue"]})
    engine = build_spark_engine(spark=spark_session, df=pd_df, batch_id="id")
    table_columns_metric, resolved = get_table_columns_metric(execution_engine=engine)

    probe_df = spark_session.createDataFrame(pd_df)
    spark_df_class = type(probe_df)

    def _rdd_not_supported(self):
        raise AttributeError(
            "[JVM_ATTRIBUTE_NOT_SUPPORTED] Attribute `rdd` is not supported in Spark Connect"
        )

    monkeypatch.setattr(spark_df_class, "rdd", property(_rdd_not_supported))

    missing_metric = MetricConfiguration(
        metric_name="column.distinct_values.missing_from_column",
        metric_domain_kwargs={"column": "colors"},
        metric_value_kwargs={"value_set": ["red", "green", "blue", "yellow"]},
    )
    missing_metric.metric_dependencies = {"table.columns": table_columns_metric}

    results = engine.resolve_metrics(metrics_to_resolve=(missing_metric,), metrics=resolved)
    assert results[missing_metric.id] == ["yellow"]
