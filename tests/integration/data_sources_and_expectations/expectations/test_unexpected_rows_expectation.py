from datetime import datetime, timezone
from typing import Sequence
from uuid import uuid4

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations.core.result_format import ResultFormat
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

# pandas not currently supported by this Expectation
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
# pandas not currently supported by this Expectation
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

TEMPLATE_SUCCESS_QUERIES = [
    {"query": "SELECT * FROM {batch} WHERE {column} > 2", "template_dict": {"column": "quantity"}},
    {
        "query": "SELECT * FROM {batch} WHERE {column_a} > 2 AND {column_b} > 91",
        "template_dict": {"column_a": "quantity", "column_b": "temperature"},
    },
    {
        "query": "SELECT * FROM {batch} WHERE {column} = {value}",
        "template_dict": {"column": "color", "value": "'blue'"},  # Note: quotes included in value
    },
]

TEMPLATE_FAILURE_QUERIES = [
    {"query": "SELECT * FROM {batch} WHERE {column} > 0", "template_dict": {"column": "quantity"}},
    {
        "query": "SELECT * FROM {batch} WHERE {column_a} > 0 AND {column_b} > 74",
        "template_dict": {"column_a": "quantity", "column_b": "temperature"},
    },
    {
        "query": "SELECT * FROM {batch} WHERE {column} = {value}",
        "template_dict": {"column": "color", "value": "'red'"},
    },
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


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=TABLE_1,
)
@pytest.mark.parametrize("unexpected_rows_query", SUCCESS_QUERIES)
def test_success_with_suite_param_other_table_name_(
    batch_for_datasource: Batch, unexpected_rows_query
) -> None:
    suite_param_key = "test_unexpected_rows_expectation"
    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect query with {batch} keyword to succeed",
        unexpected_rows_query={"$PARAMETER": suite_param_key},
        result_format=ResultFormat.SUMMARY,
    )
    result = batch_for_datasource.validate(
        expectation, expectation_parameters={suite_param_key: unexpected_rows_query}
    )
    assert result.success


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=TABLE_1,
)
@pytest.mark.parametrize("query_config", TEMPLATE_SUCCESS_QUERIES)
def test_unexpected_rows_expectation_with_template_dict_success(
    batch_for_datasource,
    query_config,
) -> None:
    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect query with template variables to succeed",
        unexpected_rows_query=query_config["query"],
        template_dict=query_config["template_dict"],
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success
    assert result.exception_info.get("raised_exception") is False


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=TABLE_1,
)
@pytest.mark.parametrize("query_config", TEMPLATE_FAILURE_QUERIES)
def test_unexpected_rows_expectation_with_template_dict_failure(
    batch_for_datasource,
    query_config,
) -> None:
    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect query with template variables to fail",
        unexpected_rows_query=query_config["query"],
        template_dict=query_config["template_dict"],
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success is False
    assert result.exception_info.get("raised_exception") is False


@parameterize_batch_for_data_sources(
    data_source_configs=EXTRA_DATA_SUPPORTED_DATA_SOURCES,
    data=TABLE_1,
    extra_data={"table_2": TABLE_2},
)
def test_unexpected_rows_expectation_template_with_join(
    batch_for_datasource,
    extra_table_names_for_datasource,
) -> None:
    """Test template functionality with JOIN queries"""
    query = """
            SELECT t1.entity_id, t1.{column}, t2.total_quantity
            FROM {batch} t1
                JOIN {table2} t2 USING (entity_id)
            WHERE t1.{column} <> t2.total_quantity \
            """

    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect query with template and JOIN to work",
        unexpected_rows_query=query,
        template_dict={"column": "quantity", "table2": extra_table_names_for_datasource["table_2"]},
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success
    assert result.exception_info.get("raised_exception") is False


@parameterize_batch_for_data_sources(
    data_source_configs=PARTITIONER_SUPPORTED_DATA_SOURCES,
    data=TABLE_1,
)
def test_unexpected_rows_expectation_template_with_partitioner(
    asset_for_datasource,
) -> None:
    """Test template functionality with partitioned data"""
    batch = asset_for_datasource.add_batch_definition_monthly(
        name="my-batch-def", column=DATE_COLUMN
    ).get_batch()

    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect query with template and partitioner to work",
        unexpected_rows_query="SELECT * FROM {batch} WHERE {column} > {threshold}",
        template_dict={"column": "quantity", "threshold": "2"},
    )
    result = batch.validate(expectation)
    assert result.success
    assert result.exception_info.get("raised_exception") is False


@parameterize_batch_for_data_sources(
    data_source_configs=[PostgreSQLDatasourceTestConfig(), RedshiftDatasourceTestConfig()],
    data=TABLE_1,
)
def test_template_result_format(batch_for_datasource: Batch) -> None:
    """Test that result format works correctly with templates"""
    result = batch_for_datasource.validate(
        gxe.UnexpectedRowsExpectation(
            unexpected_rows_query="SELECT * FROM {batch} WHERE {id_col} = {id_val}",
            template_dict={"id_col": "entity_id", "id_val": "2"},
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


# Test backward compatibility - ensure existing tests still pass without modification
@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=TABLE_1,
)
def test_backward_compatibility_no_template(batch_for_datasource) -> None:
    """Ensure queries without templates still work"""
    # This should work exactly as before
    expectation = gxe.UnexpectedRowsExpectation(
        unexpected_rows_query="SELECT * FROM {batch} WHERE quantity > 2"
    )
    result = batch_for_datasource.validate(expectation)
    assert result.success

    # Verify template_dict is optional
    assert hasattr(expectation, "template_dict")
    assert expectation.template_dict is None


@parameterize_batch_for_data_sources(
    data_source_configs=ALL_SUPPORTED_DATA_SOURCES,
    data=TABLE_1,
)
def test_template_with_suite_parameter(batch_for_datasource: Batch) -> None:
    """Test that suite parameters work with templates"""
    suite_param_key = "test_template_query"
    template_param_key = "test_template_dict"

    expectation = gxe.UnexpectedRowsExpectation(
        description="Expect query with suite parameter and template",
        unexpected_rows_query={"$PARAMETER": suite_param_key},
        template_dict={"$PARAMETER": template_param_key},
        result_format=ResultFormat.SUMMARY,
    )

    result = batch_for_datasource.validate(
        expectation,
        expectation_parameters={
            suite_param_key: "SELECT * FROM {batch} WHERE {column} > 2",
            template_param_key: {"column": "quantity"},
        },
    )
    assert result.success
