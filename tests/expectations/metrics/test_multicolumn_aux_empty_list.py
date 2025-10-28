from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict, Tuple

import pandas as pd
import pytest
import sqlalchemy as sa

from great_expectations.expectations.metrics.map_metric_provider.multicolumn_map_condition_auxilliary_methods import (  # noqa: E501
    _pandas_multicolumn_map_condition_filtered_row_count,
    _pandas_multicolumn_map_condition_values,
    _sqlalchemy_multicolumn_map_condition_filtered_row_count,
    _sqlalchemy_multicolumn_map_condition_values,
)

pytestmark = pytest.mark.unit


class _FakePandasEngine:
    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df

    def get_domain_records(self, domain_kwargs: Dict[str, Any]) -> pd.DataFrame:
        return self._df


def _make_metrics_tuple(
    boolean_mask: Any,
    compute_domain_kwargs: Dict[str, Any],
    accessor_domain_kwargs: Dict[str, Any],
) -> Tuple[Any, Dict[str, Any], Dict[str, Any]]:
    return boolean_mask, compute_domain_kwargs, accessor_domain_kwargs


def test_pandas_values_empty_column_list_returns_empty() -> None:
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    engine = _FakePandasEngine(df)

    metrics: Dict[str, Any] = {
        "unexpected_condition": _make_metrics_tuple(
            boolean_mask=None,
            compute_domain_kwargs={},
            accessor_domain_kwargs={},  # missing column_list
        ),
        "table.columns": ["A", "B"],
    }
    result = _pandas_multicolumn_map_condition_values(
        cls=None,  # type: ignore[arg-type]
        execution_engine=engine,  # type: ignore[arg-type]
        metric_domain_kwargs={},
        metric_value_kwargs={"result_format": {"result_format": "COMPLETE"}},
        metrics=metrics,
    )
    assert result == []


def test_pandas_filtered_row_count_empty_column_list_returns_total_rows() -> None:
    df = pd.DataFrame({"A": [1, 2, 3]})
    engine = _FakePandasEngine(df)

    metrics: Dict[str, Any] = {
        "unexpected_condition": _make_metrics_tuple(
            boolean_mask=None,
            compute_domain_kwargs={},
            accessor_domain_kwargs={},  # missing column_list
        ),
        "table.columns": ["A"],
    }
    count = _pandas_multicolumn_map_condition_filtered_row_count(
        cls=None,  # type: ignore[arg-type]
        execution_engine=engine,  # type: ignore[arg-type]
        metric_domain_kwargs={},
        metric_value_kwargs={"result_format": {"result_format": "COMPLETE"}},
        metrics=metrics,
    )
    assert count == 3


class _FakeResult:
    def __init__(self, value: int) -> None:
        self._value = value

    def scalar(self) -> int:
        return self._value


class _FakeSqlAlchemyEngine:
    def __init__(self, count_value: int = 0) -> None:
        self._count_value = count_value

    def get_domain_records(self, domain_kwargs: Dict[str, Any]) -> Any:
        # Return any SQLAlchemy selectable-like object; a simple select works fine
        return sa.select(sa.text("1")).subquery()

    def execute_query(self, query: Any) -> _FakeResult:
        return _FakeResult(self._count_value)


def test_sqlalchemy_values_empty_column_list_returns_empty(monkeypatch) -> None:
    engine = _FakeSqlAlchemyEngine()

    metrics: Dict[str, Any] = {
        "unexpected_condition": _make_metrics_tuple(
            boolean_mask=sa.text("1=1"),
            compute_domain_kwargs={},
            accessor_domain_kwargs={},  # missing column_list
        ),
        "table.columns": ["A", "B"],
    }

    result = _sqlalchemy_multicolumn_map_condition_values(
        cls=SimpleNamespace(),  # type: ignore[arg-type]
        execution_engine=engine,  # type: ignore[arg-type]
        metric_domain_kwargs={},
        metric_value_kwargs={"result_format": {"result_format": "COMPLETE"}},
        metrics=metrics,
    )
    assert result == []


def test_sqlalchemy_filtered_row_count_empty_column_list_executes_count(monkeypatch) -> None:
    # Ensure get_sqlalchemy_selectable returns a valid selectable to avoid dialect differences
    from great_expectations.expectations.metrics.map_metric_provider import (
        multicolumn_map_condition_auxilliary_methods as mod,
    )

    monkeypatch.setattr(mod, "get_sqlalchemy_selectable", lambda s: s)

    engine = _FakeSqlAlchemyEngine(count_value=7)

    metrics: Dict[str, Any] = {
        "unexpected_condition": _make_metrics_tuple(
            boolean_mask=sa.text("1=1"),
            compute_domain_kwargs={},
            accessor_domain_kwargs={},  # missing column_list
        ),
        "table.columns": ["A"],
    }

    count = _sqlalchemy_multicolumn_map_condition_filtered_row_count(
        cls=SimpleNamespace(),  # type: ignore[arg-type]
        execution_engine=engine,  # type: ignore[arg-type]
        metric_domain_kwargs={},
        metric_value_kwargs={"result_format": {"result_format": "COMPLETE"}},
        metrics=metrics,
    )
    assert count == 7
