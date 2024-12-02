import datetime as dt

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.data_sources_and_expectations.test_canonical_expectations import (
    ALL_DATA_SOURCES,
)
from tests.integration.test_utils.data_source_config.base import DataSourceTestConfig

PANDAS_DATA_SOURCES: list[DataSourceTestConfig] = [
    ds for ds in ALL_DATA_SOURCES if ds.label.startswith("pandas")
]
SPARK_DATA_SOURCES: list[DataSourceTestConfig] = [
    ds for ds in ALL_DATA_SOURCES if ds.label.startswith("spark")
]
SQL_DATA_SOURCES: list[DataSourceTestConfig] = [
    ds for ds in ALL_DATA_SOURCES if ds not in PANDAS_DATA_SOURCES and ds not in SPARK_DATA_SOURCES
]


@pytest.mark.unit
def test_parameterization():
    # Ensure that all data sources are covered
    assert len(PANDAS_DATA_SOURCES) + len(SPARK_DATA_SOURCES) + len(SQL_DATA_SOURCES) == len(
        ALL_DATA_SOURCES
    )


def assert_misconfiguration(
    batch_for_datasource: Batch, expectation: gxe.Expectation, exception_message: str
) -> None:
    result = batch_for_datasource.validate(expectation)
    assert not result.success
    assert exception_message in str(result.exception_info)


class TestNumericExpectationAgainstStrDataMisconfiguration:
    # Currently bugs with the following (not raising misconfiguration errors at all):
    #  - sqlite
    #  - databricks
    #  - mysql
    #  - spark-filesystem-csv

    _DATA = pd.DataFrame({"a": ["b", "c"]})
    _EXPECTATION = gxe.ExpectColumnStdevToBeBetween(
        column="a",
        min_value=0,
        max_value=1,
        strict_min=True,
        strict_max=True,
    )

    @parameterize_batch_for_data_sources(
        data_source_configs=PANDAS_DATA_SOURCES,
        data=_DATA,
    )
    def test_pandas(self, batch_for_datasource) -> None:
        assert_misconfiguration(
            batch_for_datasource=batch_for_datasource,
            expectation=self._EXPECTATION,
            exception_message="could not convert string to float",
        )

    @parameterize_batch_for_data_sources(
        data_source_configs=list(filter(lambda d: d.label == "big-query", SQL_DATA_SOURCES)),
        data=_DATA,
    )
    def test_bigquery(self, batch_for_datasource) -> None:
        assert_misconfiguration(
            batch_for_datasource=batch_for_datasource,
            expectation=self._EXPECTATION,
            exception_message="No matching signature for operator * for argument types: FLOAT64, STRING",  # noqa: E501
        )

    @parameterize_batch_for_data_sources(
        data_source_configs=list(filter(lambda d: d.label == "mssql", SQL_DATA_SOURCES)),
        data=_DATA,
    )
    def test_mssql(self, batch_for_datasource) -> None:
        assert_misconfiguration(
            batch_for_datasource=batch_for_datasource,
            expectation=self._EXPECTATION,
            exception_message="Error converting data type varchar to float",
        )

    @parameterize_batch_for_data_sources(
        data_source_configs=list(filter(lambda d: d.label == "postgresql", SQL_DATA_SOURCES)),
        data=_DATA,
    )
    def test_postgresql(self, batch_for_datasource) -> None:
        assert_misconfiguration(
            batch_for_datasource=batch_for_datasource,
            expectation=self._EXPECTATION,
            exception_message='invalid input syntax for type double precision: "b"',
        )

    @parameterize_batch_for_data_sources(
        data_source_configs=list(filter(lambda d: d.label == "snowflake", SQL_DATA_SOURCES)),
        data=_DATA,
    )
    def test_snowflake(self, batch_for_datasource) -> None:
        assert_misconfiguration(
            batch_for_datasource=batch_for_datasource,
            expectation=self._EXPECTATION,
            exception_message="Numeric value 'b' is not recognized",
        )


class TestNonExistentColumnMisconfiguration:
    _DATA = pd.DataFrame({"a": [1, 2]})
    _EXPECTATION = gxe.ExpectColumnMedianToBeBetween(column="b", min_value=5, max_value=10)

    @parameterize_batch_for_data_sources(
        data_source_configs=PANDAS_DATA_SOURCES,
        data=_DATA,
    )
    def test_pandas(self, batch_for_datasource) -> None:
        assert_misconfiguration(
            batch_for_datasource=batch_for_datasource,
            expectation=self._EXPECTATION,
            exception_message="The column 'b' in BatchData does not exist",
        )

    @parameterize_batch_for_data_sources(
        data_source_configs=SQL_DATA_SOURCES,
        data=_DATA,
    )
    def test_sql(self, batch_for_datasource) -> None:
        assert_misconfiguration(
            batch_for_datasource=batch_for_datasource,
            expectation=self._EXPECTATION,
            exception_message='The column "b" in BatchData does not exist',
        )

    @parameterize_batch_for_data_sources(
        data_source_configs=SPARK_DATA_SOURCES,
        data=_DATA,
    )
    def test_spark(self, batch_for_datasource) -> None:
        assert_misconfiguration(
            batch_for_datasource=batch_for_datasource,
            expectation=self._EXPECTATION,
            exception_message="A column or function parameter with name `b` cannot be resolved",
        )


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES,
    data=pd.DataFrame({"a": [1, 2]}),
)
def test_datetime_expectation_against_numeric_data_misconfiguration(batch_for_datasource) -> None:
    expectation = gxe.ExpectColumnMaxToBeBetween(
        column="a",
        min_value=dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc),
        max_value=dt.datetime(2024, 1, 2, tzinfo=dt.timezone.utc),
        strict_max=True,
    )
    assert_misconfiguration(
        batch_for_datasource=batch_for_datasource,
        expectation=expectation,
        exception_message="into datetime representation",
    )


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES,
    data=pd.DataFrame({"a": [1, 2]}),
)
def test_column_min_max_mismatch_misconfiguration(batch_for_datasource) -> None:
    expectation = gxe.ExpectColumnValuesToBeBetween(column="a", min_value=2, max_value=1)
    assert_misconfiguration(
        batch_for_datasource=batch_for_datasource,
        expectation=expectation,
        exception_message="min_value cannot be greater than max_value",
    )


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_DATA_SOURCES,
    data=pd.DataFrame({"a": [1, 2]}),
)
def test_column_min_max_missing_misconfiguration(batch_for_datasource) -> None:
    expectation = gxe.ExpectColumnValuesToBeBetween(column="a")
    assert_misconfiguration(
        batch_for_datasource=batch_for_datasource,
        expectation=expectation,
        exception_message="min_value and max_value cannot both be None",
    )
