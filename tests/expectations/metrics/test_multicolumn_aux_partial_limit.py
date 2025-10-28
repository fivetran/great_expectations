from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict

import pytest
import sqlalchemy as sa

from great_expectations.expectations.metrics.map_metric_provider.multicolumn_map_condition_auxilliary_methods import (  # noqa: E501
    _sqlalchemy_multicolumn_map_condition_values,
)

pytestmark = pytest.mark.unit


class _FakeResult:
    def fetchmany(self, n: int):
        return [SimpleNamespace(_asdict=lambda: {"A": 1}) for _ in range(min(n, 1))]


class _FakeSqlAlchemyEngine:
    def __init__(self):
        # minimal attributes used down the stack
        self.dialect_module = None

    def get_domain_records(self, domain_kwargs: Dict[str, Any]) -> Any:
        return sa.select(sa.text("1")).subquery()

    def execute_query(self, query: Any) -> _FakeResult:
        # Ensure a LIMIT has been applied
        assert hasattr(query, "_limit_clause") or "LIMIT" in str(query).upper()
        return _FakeResult()


def test_sqlalchemy_values_partial_result_format_applies_limit() -> None:
    engine = _FakeSqlAlchemyEngine()

    metrics: Dict[str, Any] = {
        "unexpected_condition": (
            sa.text("1=1"),
            {},
            {"column_list": ["A"]},
        ),
        "table.columns": ["A"],
    }

    res = _sqlalchemy_multicolumn_map_condition_values(
        cls=SimpleNamespace(),  # type: ignore[arg-type]
        execution_engine=engine,  # type: ignore[arg-type]
        metric_domain_kwargs={},
        metric_value_kwargs={
            "result_format": {
                "result_format": "SUMMARY",
                "partial_unexpected_count": 5,
            }
        },
        metrics=metrics,
    )
    assert res == [{"A": 1}]
