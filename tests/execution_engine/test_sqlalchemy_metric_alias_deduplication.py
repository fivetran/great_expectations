from unittest.mock import patch

import pytest

from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.execution_engine.execution_engine import (
    MetricComputationConfiguration,
)
from great_expectations.execution_engine.sqlalchemy_execution_engine import (
    SqlAlchemyExecutionEngine,
)
from great_expectations.validator.metric_configuration import MetricConfiguration

pytestmark = pytest.mark.unit


def _make_bundle_entry(column: str) -> MetricComputationConfiguration:
    """Build a bundle entry whose metric name collides with the others."""
    return MetricComputationConfiguration(
        metric_configuration=MetricConfiguration(
            metric_name="column_values.nonnull.unexpected_count",
            metric_domain_kwargs={"column": column},
            metric_value_kwargs=None,
        ),
        metric_fn=sa.func.sum(sa.column(column)),
        compute_domain_kwargs={},
        accessor_domain_kwargs={"column": column},
        metric_provider_kwargs={},
    )


def test_organize_metrics_by_domain_deduplicates_metric_aliases():
    """Regression test for #10926.

    Bundling multiple expectations that resolve to the same underlying metric
    (e.g. column_values.nonnull.unexpected_count on different columns) must
    produce unique, deterministic SQL aliases so strict backends (ClickHouse,
    BigQuery) do not fail with "Duplicated field name in view schema".
    """
    engine = SqlAlchemyExecutionEngine(connection_string="sqlite://")
    selectable = sa.table(
        "test_table",
        sa.column("field1"),
        sa.column("field2"),
        sa.column("field3"),
    )

    bundle = [
        _make_bundle_entry("field1"),
        _make_bundle_entry("field2"),
        _make_bundle_entry("field3"),
    ]

    with patch.object(SqlAlchemyExecutionEngine, "get_domain_records", return_value=selectable):
        queries = engine._organize_metrics_by_domain(bundle)

    assert len(queries) == 1
    labels = [select.name for select in queries[0]["select"]]
    assert labels == [
        "column_values.nonnull.unexpected_count",
        "column_values.nonnull.unexpected_count_1",
        "column_values.nonnull.unexpected_count_2",
    ]
    assert len(queries[0]["metric_ids"]) == 3
