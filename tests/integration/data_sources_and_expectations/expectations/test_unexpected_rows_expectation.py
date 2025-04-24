from datetime import datetime, timezone
from typing import Sequence
from uuid import uuid4

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.datasource.fluent.interfaces import Batch
from tests.integration.conftest import parameterize_batch_for_data_sources
from tests.integration.test_utils.data_source_config import (
    BigQueryDatasourceTestConfig,
    DatabricksDatasourceTestConfig,
    DataSourceTestConfig,
    # MSSQLDatasourceTestConfig,
    MySQLDatasourceTestConfig,
    PostgreSQLDatasourceTestConfig,
    RedshiftDatasourceTestConfig,
    SnowflakeDatasourceTestConfig,
    SparkFilesystemCsvDatasourceTestConfig,
    # SqliteDatasourceTestConfig,
)

# pandas not currently supported by this Expecatation
ALL_SUPPORTED_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    BigQueryDatasourceTestConfig(),
    DatabricksDatasourceTestConfig(),
    # MSSQLDatasourceTestConfig(),  # fix me
    MySQLDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(),
    RedshiftDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig(),
    SparkFilesystemCsvDatasourceTestConfig(),
    # SqliteDatasourceTestConfig(),  # fix me
]

# spark and big query not currently supported with extra_data, so we can't test JOIN
# pandas not currently supported by this Expecatation
EXTRA_DATA_SUPPORTED_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    DatabricksDatasourceTestConfig(),
    # MSSQLDatasourceTestConfig(),  # fix me
    MySQLDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(),
    RedshiftDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig(),
    # SqliteDatasourceTestConfig(),  # fix me
]

# pandas and spark not currently supporting partitioners
PARTITIONER_SUPPORTED_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    BigQueryDatasourceTestConfig(),
    DatabricksDatasourceTestConfig(),
    # MSSQLDatasourceTestConfig(),  # fix me
    MySQLDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(),
    RedshiftDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig(),
    # SqliteDatasourceTestConfig(),  # fix me
]

# spark and big query not currently supported with extra_data, so we can't test JOIN
# pandas and spark not currently supporting partitioners
PARTITIONER_AND_EXTRA_DATA_SUPPORTED_DATA_SOURCES: Sequence[DataSourceTestConfig] = [
    DatabricksDatasourceTestConfig(),
    # MSSQLDatasourceTestConfig(),  # fix me
    MySQLDatasourceTestConfig(),
    PostgreSQLDatasourceTestConfig(),
    RedshiftDatasourceTestConfig(),
    SnowflakeDatasourceTestConfig(),
    # SqliteDatasourceTestConfig(),  # fix me
]

TABLE_1 = pd.DataFrame(
    {
        "entity_id": [1, 2],
        "created_at": [
            datetime(year=2024, month=12, day=1, tzinfo=timezone.utc).date(),
            datetime(year=2024, month=11, day=30, tzinfo=timezone.utc).date(),
        ],
        "quantity": [1, 2],
        "temperature": [75, 92],
        "color": ["red", "red"],
    }
)

TABLE_2 = pd.DataFrame(
    {
        "entity_id": [1, 2],
        "created_at": [
            datetime(year=2024, month=12, day=1, tzinfo=timezone.utc).date(),
            datetime(year=2024, month=11, day=30, tzinfo=timezone.utc).date(),
        ],
        "total_quantity": [1, 2],
    }
)

DATE_COLUMN = "created_at"

SUCCESS_QUERIES = [
    "SELECT * FROM {batch} WHERE quantity > 2",
    "SELECT * FROM {batch} WHERE quantity > 2 AND temperature > 91",
    "SELECT * FROM {batch} WHERE quantity > 2 OR temperature > 92",
    "SELECT * FROM {batch} WHERE quantity > 2 ORDER BY quantity DESC",
    "SELECT color FROM {batch} GROUP BY color HAVING SUM(quantity) > 3",
]

JOIN_SUCCESS_QUERIES = [
    """
     SELECT t1.entity_id, t1.quantity, t2.total_quantity
     FROM {batch} t1
     JOIN table_2 t2 USING (entity_id)
     WHERE t1.quantity <> t2.total_quantity
    """,
    """
     SELECT t1.*, t2.record_count FROM
     (SELECT * FROM {batch} AS batch) AS t1
     JOIN
     (SELECT entity_id, SUM(total_quantity) as total_quantity, COUNT(*) as record_count
      FROM table_2 GROUP BY entity_id) AS t2
     ON t1.entity_id = t2.entity_id
     WHERE t1.quantity <> t2.total_quantity
    """,
]

FAILURE_QUERIES = [
    "SELECT * FROM {batch}",
    "SELECT * FROM {batch} WHERE quantity > 0",
    "SELECT * FROM {batch} WHERE quantity > 0 AND temperature > 74",
    "SELECT * FROM {batch} WHERE quantity > 0 OR temperature > 92",
    "SELECT * FROM {batch} WHERE quantity > 0 ORDER BY quantity DESC",
    "SELECT color FROM {batch} GROUP BY color HAVING SUM(quantity) > 0",
]

JOIN_FAILURE_QUERIES = [
    """
     SELECT t1.entity_id, t1.quantity, t2.total_quantity
     FROM {batch} t1
     JOIN table_2 t2 USING (entity_id)
     WHERE t1.quantity = t2.total_quantity
    """,
    """
     SELECT t1.*, t2.record_count FROM
     (SELECT * FROM {batch} AS batch) AS t1
     JOIN
     (SELECT entity_id, SUM(total_quantity) as total_quantity, COUNT(*) as record_count
      FROM table_2 GROUP BY entity_id) AS t2
     ON t1.entity_id = t2.entity_id
     WHERE t1.quantity = t2.total_quantity
    """,
]


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=TABLE_1,
)
@pytest.mark.parametrize("unexpected_rows_query", SUCCESS_QUERIES)
def test_unexpected_rows_expectation_batch_keyword_success(
    batch_for_datasource,
    unexpected_rows_query,
) -> None:
    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect query with {batch} keyword to succeed",
        unexpected_rows_query=unexpected_rows_query,
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success
    assert result.exception_info.get("raised_exception") is False


@parameterize_batch_for_data_sources(
    data_source_configs=EXTRA_DATA_SUPPORTED_DATA_SOURCES,
    data=TABLE_1,
    extra_data={"table_2": TABLE_2},
)
def test_unexpected_rows_expectation_join_keyword_success(
    batch_for_datasource,
    extra_table_names_for_datasource,
) -> None:
    for join_success_query in JOIN_SUCCESS_QUERIES:
        unexpected_rows_query = join_success_query.replace(
            "table_2", extra_table_names_for_datasource["table_2"]
        )
        expectation = gxe.UnexpectedRowsExpectation(
            description="Expect query with JOIN keyword to succeed",
            unexpected_rows_query=unexpected_rows_query,
        )
        result = batch_for_datasource.validate(expectation)
        assert result.success
        assert result.exception_info.get("raised_exception") is False


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=TABLE_1,
)
@pytest.mark.parametrize("unexpected_rows_query", FAILURE_QUERIES)
def test_unexpected_rows_expectation_batch_keyword_failure(
    batch_for_datasource,
    unexpected_rows_query,
) -> None:
    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect query with {batch} keyword to fail",
        unexpected_rows_query=unexpected_rows_query,
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success is False
    assert result.exception_info.get("raised_exception") is False


@parameterize_batch_for_data_sources(
    data_source_configs=EXTRA_DATA_SUPPORTED_DATA_SOURCES,
    data=TABLE_1,
    extra_data={"table_2": TABLE_2},
)
def test_unexpected_rows_expectation_join_keyword_failure(
    batch_for_datasource,
    extra_table_names_for_datasource,
) -> None:
    for join_failure_query in JOIN_FAILURE_QUERIES:
        unexpected_rows_query = join_failure_query.replace(
            "table_2", extra_table_names_for_datasource["table_2"]
        )
        expectation = gxe.UnexpectedRowsExpectation(
            description="Expect query with JOIN keyword to fail",
            unexpected_rows_query=unexpected_rows_query,
        )
        result = batch_for_datasource.validate(expectation)
        assert result.success is False
        assert result.exception_info.get("raised_exception") is False


@parameterize_batch_for_data_sources(
    data_source_configs=PARTITIONER_SUPPORTED_DATA_SOURCES,
    data=TABLE_1,
)
@pytest.mark.parametrize("unexpected_rows_query", SUCCESS_QUERIES)
def test_unexpected_rows_expectation_batch_keyword_partitioner_success(
    asset_for_datasource,
    unexpected_rows_query,
) -> None:
    batch = asset_for_datasource.add_batch_definition_monthly(
        name="my-batch-def", column=DATE_COLUMN
    ).get_batch()
    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect query with {batch} keyword and paritioner defined to succeed",
        unexpected_rows_query=unexpected_rows_query,
    )
    result = batch.validate(expectation)
    assert result.success
    assert result.exception_info.get("raised_exception") is False


@parameterize_batch_for_data_sources(
    data_source_configs=PARTITIONER_AND_EXTRA_DATA_SUPPORTED_DATA_SOURCES,
    data=TABLE_1,
    extra_data={"table_2": TABLE_2},
)
def test_unexpected_rows_expectation_join_keyword_partitioner_success(
    asset_for_datasource,
    extra_table_names_for_datasource,
) -> None:
    batch = asset_for_datasource.add_batch_definition_monthly(
        name="my-batch-def", column=DATE_COLUMN
    ).get_batch()
    for join_success_query in JOIN_SUCCESS_QUERIES:
        unexpected_rows_query = join_success_query.replace(
            "table_2", extra_table_names_for_datasource["table_2"]
        )
        expectation = gxe.UnexpectedRowsExpectation(
            description="Expect query with JOIN keyword and paritioner defined to succeed",
            unexpected_rows_query=unexpected_rows_query,
        )
        result = batch.validate(expectation)
        assert result.success
        assert result.exception_info.get("raised_exception") is False


@parameterize_batch_for_data_sources(
    data_source_configs=PARTITIONER_SUPPORTED_DATA_SOURCES,
    data=TABLE_1,
)
@pytest.mark.parametrize("unexpected_rows_query", FAILURE_QUERIES)
def test_unexpected_rows_expectation_batch_keyword_partitioner_failure(
    asset_for_datasource,
    unexpected_rows_query,
) -> None:
    batch = asset_for_datasource.add_batch_definition_monthly(
        name=str(uuid4()), column=DATE_COLUMN
    ).get_batch()
    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect query with {batch} keyword and partitioner defined to fail",
        unexpected_rows_query=unexpected_rows_query,
    )
    result = batch.validate(expectation)
    assert result.success is False
    assert result.exception_info.get("raised_exception") is False


@parameterize_batch_for_data_sources(
    data_source_configs=PARTITIONER_AND_EXTRA_DATA_SUPPORTED_DATA_SOURCES,
    data=TABLE_1,
    extra_data={"table_2": TABLE_2},
)
def test_unexpected_rows_expectation_join_keyword_partitioner_failure(
    asset_for_datasource,
    extra_table_names_for_datasource,
) -> None:
    batch = asset_for_datasource.add_batch_definition_monthly(
        name=str(uuid4()), column=DATE_COLUMN
    ).get_batch()
    for join_failure_query in JOIN_FAILURE_QUERIES:
        unexpected_rows_query = join_failure_query.replace(
            "table_2", extra_table_names_for_datasource["table_2"]
        )
        expectation = gxe.UnexpectedRowsExpectation(
            description="Expect query with JOIN keyword and paritioner defined to fail",
            unexpected_rows_query=unexpected_rows_query,
        )
        result = batch.validate(expectation)
        assert result.success is False
        assert result.exception_info.get("raised_exception") is False


@parameterize_batch_for_data_sources(
    data_source_configs=[PostgreSQLDatasourceTestConfig(), RedshiftDatasourceTestConfig()],
    data=TABLE_1,
)
def test_success_result_format(batch_for_datasource: Batch) -> None:
    result = batch_for_datasource.validate(
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query="SELECT * FROM {batch} WHERE entity_id = 123"
        )
    )

    assert result.success
    assert result.result == {
        "observed_value": 0,
        "details": {
            "unexpected_rows": [],
        },
    }


@parameterize_batch_for_data_sources(
    data_source_configs=[PostgreSQLDatasourceTestConfig(), RedshiftDatasourceTestConfig()],
    data=TABLE_1,
)
def test_fail_result_format(batch_for_datasource: Batch) -> None:
    result = batch_for_datasource.validate(
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query="SELECT * FROM {batch} WHERE entity_id = 2"
        )
    )

    assert not result.success
    assert result.result == {
        "observed_value": 1,
        "details": {
            "unexpected_rows": [
                {
                    "entity_id": 2,
                    "created_at": datetime(year=2024, month=11, day=30, tzinfo=timezone.utc).date(),
                    "quantity": 2,
                    "temperature": 92,
                    "color": "red",
                }
            ],
        },
    }
