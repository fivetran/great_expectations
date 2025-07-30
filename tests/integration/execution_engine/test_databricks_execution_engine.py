import uuid

import pandas as pd
import pytest
from sqlalchemy import VARCHAR, Column, MetaData, Table, insert

from great_expectations.core.batch_spec import SqlAlchemyDatasourceBatchSpec
from great_expectations.core.metric_function_types import (
    MetricPartialFunctionTypes,
    MetricPartialFunctionTypeSuffixes,
    SummarizationMetricNameSuffixes,
)
from great_expectations.execution_engine.sqlalchemy_execution_engine import (
    SqlAlchemyExecutionEngine,
)
from great_expectations.validator.metric_configuration import MetricConfiguration
from tests.expectations.test_util import get_table_columns_metric
from tests.integration.test_utils.data_source_config.databricks import (
    DatabricksConnectionConfig,
)


@pytest.fixture
def generate_large_table_for_metrics(sa):
    def _generate_large_table_for_metrics(num_columns, num_rows):
        data = {}
        for i in range(num_columns):
            if i % 5 == 0:
                data[f"numeric_col_{i}"] = [j * (i + 1) % 1000 for j in range(num_rows)]
            else:
                data[f"string_col_{i}"] = [f"string_{i}_{j}" for j in range(num_rows)]

        df = pd.DataFrame(data)

        config = DatabricksConnectionConfig()
        schema_name = f"test_{uuid.uuid4().hex[:8]}"
        connection_string = config.connection_string(schema_name)

        execution_engine = SqlAlchemyExecutionEngine(connection_string=connection_string)

        metadata = MetaData()
        table_name = f"test_table_{uuid.uuid4().hex[:8]}"

        with execution_engine.get_connection() as conn, conn.begin():
            conn.execute(sa.text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))

            columns = []
            for col_name in df.columns:
                columns.append(Column(col_name, VARCHAR(255)))

            table = Table(table_name, metadata, *columns, schema=schema_name)
            metadata.create_all(execution_engine.engine)

            conn.execute(insert(table), list(df.to_dict("index").values()))

        batch_spec = SqlAlchemyDatasourceBatchSpec(
            table_name=table_name,
            sampling_method="_sample_using_limit",
            sampling_kwargs={"n": num_rows},
        )
        batch_data, _ = execution_engine.get_batch_data_and_markers(batch_spec=batch_spec)
        execution_engine.load_batch_data("test_batch_id", batch_data)

        return execution_engine, df

    return _generate_large_table_for_metrics


@pytest.fixture
def add_metrics_for_each_column():
    def _add_metrics_for_each_column(execution_engine, df):
        metrics = {}
        table_columns_metric, results = get_table_columns_metric(execution_engine=execution_engine)
        metrics.update(results)

        condition_metrics = []
        for column in df.columns:
            condition_metric = MetricConfiguration(
                metric_name=f"column_values.nonnull.{MetricPartialFunctionTypeSuffixes.CONDITION.value}",
                metric_domain_kwargs={"column": column},
                metric_value_kwargs=None,
            )
            condition_metric.metric_dependencies = {
                "table.columns": table_columns_metric,
            }
            condition_metrics.append(condition_metric)

        results = execution_engine.resolve_metrics(
            metrics_to_resolve=tuple(condition_metrics), metrics=metrics
        )
        metrics.update(results)

        aggregate_fn_metrics = []
        for i, condition_metric in enumerate(condition_metrics):
            aggregate_fn_metric = MetricConfiguration(
                metric_name=(
                    f"column_values.nonnull.{SummarizationMetricNameSuffixes.UNEXPECTED_COUNT.value}."
                    f"{MetricPartialFunctionTypes.AGGREGATE_FN.metric_suffix}"
                ),
                metric_domain_kwargs={"column": df.columns[i]},
                metric_value_kwargs=None,
            )
            aggregate_fn_metric.metric_dependencies = {
                "unexpected_condition": condition_metric,
            }
            aggregate_fn_metrics.append(aggregate_fn_metric)

        results = execution_engine.resolve_metrics(
            metrics_to_resolve=tuple(aggregate_fn_metrics), metrics=metrics
        )
        metrics.update(results)

        unexpected_count_metrics = []
        for i, aggregate_fn_metric in enumerate(aggregate_fn_metrics):
            unexpected_count_metric = MetricConfiguration(
                metric_name=f"column_values.nonnull.{SummarizationMetricNameSuffixes.UNEXPECTED_COUNT.value}",
                metric_domain_kwargs={"column": df.columns[i]},
                metric_value_kwargs=None,
            )
            unexpected_count_metric.metric_dependencies = {
                "metric_partial_fn": aggregate_fn_metric,
            }
            unexpected_count_metrics.append(unexpected_count_metric)
        return (
            metrics,
            unexpected_count_metrics,
            condition_metrics,
            aggregate_fn_metrics,
            table_columns_metric,
        )

    return _add_metrics_for_each_column


@pytest.mark.databricks
class TestDatabricksExecutionEngineIntegration:
    """Integration tests for Databricks execution engine with large datasets and parameter sets.

    This test verifies that the execution engine can handle large numbers of columns
    and complex metric calculations that may hit database parameter limits.
    """

    def test_resolve_metric_bundle_with_large_parameter_set(
        self, caplog, sa, generate_large_table_for_metrics, add_metrics_for_each_column
    ):
        """Test metric resolution with large parameter sets to verify parameter limit handling.

        This test creates a table with 129 columns and generates multiple metrics per column
        to test that the execution engine properly handles cases where SQL query parameters
        exceeds database limits (e.g., Databricks parameter limits).

        Args:
            caplog: Pytest log capture fixture
            sa: SQLAlchemy fixture
            generate_large_table_for_metrics: Fixture for creating large test tables
            add_metrics_for_each_column: Fixture for adding metrics to each column
        """
        COLUMNS = (
            129  # 129 columns to test the param limit by generating 2 aggregate metrics per each.
        )
        ROWS = 2

        execution_engine, df = generate_large_table_for_metrics(COLUMNS, ROWS)

        (
            metrics,
            unexpected_count_metrics,
            condition_metrics,
            aggregate_fn_metrics,
            table_columns_metric,
        ) = add_metrics_for_each_column(execution_engine, df)

        results = execution_engine.resolve_metrics(
            metrics_to_resolve=tuple(unexpected_count_metrics), metrics=metrics
        )
        metrics.update(results)

        expected_total_metrics = 2 + (3 * COLUMNS)  # 2 table.columns + 3 metrics per column
        actual_total_metrics = len(metrics)

        assert expected_total_metrics == actual_total_metrics

        table_columns_metric_id = table_columns_metric.id
        assert table_columns_metric_id in metrics, "table.columns metric should be present"
        table_columns_result = metrics[table_columns_metric_id]
        assert isinstance(table_columns_result, list), "table.columns should return a list"
        assert len(table_columns_result) == COLUMNS, f"table.columns should have {COLUMNS} columns"

        for condition_metric in condition_metrics:
            assert condition_metric.id in metrics, (
                f"Condition metric {condition_metric.id} should be present"
            )
            condition_result = metrics[condition_metric.id]
            assert condition_result is not None, (
                f"Condition metric {condition_metric.id} should not be None"
            )

        for aggregate_fn_metric in aggregate_fn_metrics:
            assert aggregate_fn_metric.id in metrics, (
                f"Aggregate function metric {aggregate_fn_metric.id} should be present"
            )
            aggregate_result = metrics[aggregate_fn_metric.id]
            assert aggregate_result is not None, (
                f"Aggregate function metric {aggregate_fn_metric.id} should not be None"
            )

    @pytest.mark.parametrize(
        "columns,description",
        [
            (127, "Just under limit"),  # 127 * 2 = 254 params (under limit)
            (128, "Exactly at limit"),  # 128 * 2 = 256 params (at limit)
            (129, "Just over limit"),  # 129 * 2 = 258 params (over limit)
            (255, "Near full limit"),  # 255 * 2 = 510 params (well over limit)
        ],
    )
    def test_parameter_limit_edge_cases(
        self,
        caplog,
        sa,
        generate_large_table_for_metrics,
        add_metrics_for_each_column,
        columns,
        description,
    ):
        """Test parameter limit handling at various boundary conditions.

        This test verifies the _handle_databricks_parameter_limit method works
        correctly at edge cases around the 256 parameter limit.

        Args:
            caplog: Pytest log capture fixture
            sa: SQLAlchemy fixture
            generate_large_table_for_metrics: Fixture for creating large test tables
            add_metrics_for_each_column: Fixture for adding metrics to each column
            columns: Number of columns to test with
            description: Description of the test case
        """
        ROWS = 2
        execution_engine, df = generate_large_table_for_metrics(columns, ROWS)

        (
            metrics,
            unexpected_count_metrics,
            condition_metrics,
            aggregate_fn_metrics,
            table_columns_metric,
        ) = add_metrics_for_each_column(execution_engine, df)

        results = execution_engine.resolve_metrics(
            metrics_to_resolve=tuple(unexpected_count_metrics), metrics=metrics
        )
        metrics.update(results)

        expected_total_metrics = 2 + (
            3 * columns
        )  # 2 table.columns + 3 metrics per column (2 aggregate + 1 condition )
        actual_total_metrics = len(metrics)

        assert expected_total_metrics == actual_total_metrics, (
            f"{description}: Expected {expected_total_metrics} metrics, got {actual_total_metrics}"
        )

    def test_single_column_parameter_limit(
        self, sa, generate_large_table_for_metrics, add_metrics_for_each_column
    ):
        """Test parameter limit handling with minimal column count.

        This test verifies that the batching logic works correctly even with
        very small numbers of columns that shouldn't trigger batching.
        """
        COLUMNS = 1  # Minimal case
        ROWS = 10

        execution_engine, df = generate_large_table_for_metrics(COLUMNS, ROWS)

        (
            metrics,
            unexpected_count_metrics,
            condition_metrics,
            aggregate_fn_metrics,
            table_columns_metric,
        ) = add_metrics_for_each_column(execution_engine, df)

        results = execution_engine.resolve_metrics(
            metrics_to_resolve=tuple(unexpected_count_metrics), metrics=metrics
        )
        metrics.update(results)

        # Should have 2 table metrics + 3 column metrics for single column
        expected_total_metrics = 2 + (3 * COLUMNS)
        actual_total_metrics = len(metrics)

        assert expected_total_metrics == actual_total_metrics
        assert len(df.columns) == COLUMNS

    def test_high_volume_metrics_parameter_batching(
        self, sa, generate_large_table_for_metrics, add_metrics_for_each_column
    ):
        """Test parameter limit handling with high volume of metrics (~600)."""
        COLUMNS = 200  # Will generate ~602 metrics (2 table + 200*3 column metrics)
        ROWS = 5

        execution_engine, df = generate_large_table_for_metrics(COLUMNS, ROWS)

        (
            metrics,
            unexpected_count_metrics,
            condition_metrics,
            aggregate_fn_metrics,
            table_columns_metric,
        ) = add_metrics_for_each_column(execution_engine, df)

        results = execution_engine.resolve_metrics(
            metrics_to_resolve=tuple(unexpected_count_metrics), metrics=metrics
        )
        metrics.update(results)

        expected_total_metrics = 2 + (3 * COLUMNS)  # 602 total metrics
        actual_total_metrics = len(metrics)

        assert expected_total_metrics == actual_total_metrics

        assert table_columns_metric.id in metrics

        for i, column in enumerate(df.columns):
            # Check condition metric
            condition_metric = condition_metrics[i]
            assert condition_metric.id in metrics
            condition_result = metrics[condition_metric.id]
            assert condition_result is not None

            # Check aggregate function metric
            aggregate_fn_metric = aggregate_fn_metrics[i]
            assert aggregate_fn_metric.id in metrics
            aggregate_result = metrics[aggregate_fn_metric.id]
            assert aggregate_result is not None

            # Check unexpected count metric
            unexpected_count_metric = unexpected_count_metrics[i]
            assert unexpected_count_metric.id in metrics
            unexpected_result = metrics[unexpected_count_metric.id]
            assert unexpected_result is not None
