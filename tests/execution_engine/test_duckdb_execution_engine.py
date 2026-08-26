from __future__ import annotations

import pandas as pd
import pytest

from great_expectations.execution_engine import DuckDBExecutionEngine
from great_expectations.execution_engine.duckdb_batch_data import DuckDBBatchData
from great_expectations.expectations.row_conditions import Column
from great_expectations.validator.metric_configuration import MetricConfiguration
from great_expectations.validator.validation_graph import ValidationGraph

pytestmark = pytest.mark.unit


@pytest.fixture
def duckdb_engine() -> DuckDBExecutionEngine:
    engine = DuckDBExecutionEngine()
    engine.load_batch_data(
        "batch1",
        pd.DataFrame(
            {
                "a": [1, 2, 3, 4, 10],
                "b": ["x", "y", None, "z", "w"],
            }
        ),
    )
    return engine


def _resolve(
    engine: DuckDBExecutionEngine, metric_name: str, domain_kwargs: dict, value_kwargs=None
):
    mc = MetricConfiguration(
        metric_name=metric_name,
        metric_domain_kwargs=domain_kwargs,
        metric_value_kwargs=value_kwargs,
    )
    graph = ValidationGraph(execution_engine=engine)
    graph.build_metric_dependency_graph(mc)
    resolved, aborted = graph.resolve(show_progress_bars=False)
    assert not aborted, f"metrics aborted: {aborted}"
    return resolved[mc.id]


class TestGetBatchDataAndMarkers:
    def test_load_dataframe_directly(self, duckdb_engine: DuckDBExecutionEngine):
        batch_data = duckdb_engine.batch_manager.active_batch_data
        assert isinstance(batch_data, DuckDBBatchData)
        assert batch_data.relation.fetchall() == [
            (1, "x"),
            (2, "y"),
            (3, None),
            (4, "z"),
            (10, "w"),
        ]

    def test_read_csv_path_batch_spec(self, duckdb_engine: DuckDBExecutionEngine, tmp_path):
        from great_expectations.core.batch_spec import PathBatchSpec

        csv_path = tmp_path / "data.csv"
        csv_path.write_text("a,b\n1,x\n2,y\n")

        batch_data, markers = duckdb_engine.get_batch_data_and_markers(
            PathBatchSpec(path=str(csv_path), reader_options={})
        )
        assert batch_data.relation.fetchall() == [(1, "x"), (2, "y")]
        assert markers["ge_load_time"] is not None


class TestConditionToFilterClause:
    def test_comparison_and_nullity(self, duckdb_engine: DuckDBExecutionEngine):
        condition = (Column("a") > 1) & Column("b").is_not_null()
        relation = duckdb_engine.get_domain_records(
            {"batch_id": "batch1", "row_condition": condition}
        )
        assert relation.fetchall() == [(2, "y"), (4, "z"), (10, "w")]

    def test_in_and_or(self, duckdb_engine: DuckDBExecutionEngine):
        condition = Column("a").is_in([1, 10]) | Column("b").is_null()
        relation = duckdb_engine.get_domain_records(
            {"batch_id": "batch1", "row_condition": condition}
        )
        assert relation.fetchall() == [(1, "x"), (3, None), (10, "w")]

    def test_not_in(self, duckdb_engine: DuckDBExecutionEngine):
        condition = Column("a").is_not_in([1, 2])
        relation = duckdb_engine.get_domain_records(
            {"batch_id": "batch1", "row_condition": condition}
        )
        assert relation.fetchall() == [(3, None), (4, "z"), (10, "w")]


class TestResolveMetricBundle:
    def test_table_row_count(self, duckdb_engine: DuckDBExecutionEngine):
        assert _resolve(duckdb_engine, "table.row_count", {"batch_id": "batch1"}) == 5

    def test_column_aggregates_bundle_in_one_query(self, duckdb_engine: DuckDBExecutionEngine):
        domain_kwargs = {"batch_id": "batch1", "column": "a"}
        assert _resolve(duckdb_engine, "column.mean", domain_kwargs) == 4.0
        assert _resolve(duckdb_engine, "column.min", domain_kwargs) == 1
        assert _resolve(duckdb_engine, "column.max", domain_kwargs) == 10

    def test_row_count_with_row_condition(self, duckdb_engine: DuckDBExecutionEngine):
        condition = Column("a") > 2
        domain_kwargs = {"batch_id": "batch1", "row_condition": condition}
        assert _resolve(duckdb_engine, "table.row_count", domain_kwargs) == 3
