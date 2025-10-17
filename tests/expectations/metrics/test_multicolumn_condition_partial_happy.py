from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd
import pytest
import sqlalchemy as sa

from great_expectations.expectations.metrics.map_metric_provider.multicolumn_condition_partial import (  # noqa: E501
    multicolumn_condition_partial,
)

pytestmark = pytest.mark.unit


def _metrics_with_columns(cols: List[str]) -> Dict[str, Any]:
    return {"table.columns": cols}


class _PandasEngineStub:
    def __init__(self, df: pd.DataFrame, column_list: List[str]):
        self._df = df
        self._column_list = column_list

    def get_compute_domain(self, domain_kwargs: dict, domain_type: Any):
        # Return dataframe and accessor with predefined column_list
        return self._df, {}, {"column_list": self._column_list}


def test_multicolumn_condition_partial_pandas_happy_path() -> None:
    from great_expectations.execution_engine.pandas_execution_engine import (
        PandasExecutionEngine,
    )

    class E(PandasExecutionEngine):  # type: ignore[misc]
        pass

    class Dummy:
        @multicolumn_condition_partial(engine=E)
        def _pandas(self, column_list, **kwargs):
            # Return all True (no unexpected), so inversion yields all False
            return pd.Series([True, True])

    df = pd.DataFrame({"a": [1, 2]})
    engine = _PandasEngineStub(df, ["a"])  # type: ignore[arg-type]

    inner = Dummy._pandas  # type: ignore[attr-defined]
    unexpected_condition, _compute, accessor = inner(
        Dummy(),
        execution_engine=engine,  # type: ignore[arg-type]
        metric_domain_kwargs={},
        metric_value_kwargs={},
        metrics=_metrics_with_columns(["a"]),
        runtime_configuration={},
    )
    assert list(unexpected_condition.values) == [False, False]
    assert accessor == {"column_list": ["a"]}


class _SqlEngineStub:
    def __init__(self, column_list: List[str]):
        self.dialect_module = None
        self.engine = None
        self._column_list = column_list

    def get_compute_domain(self, domain_kwargs: dict, domain_type: Any):
        selectable = sa.select(sa.text("1")).subquery()
        return selectable, {}, {"column_list": self._column_list}


def test_multicolumn_condition_partial_sqlalchemy_happy_path() -> None:
    from great_expectations.execution_engine.sqlalchemy_execution_engine import (
        SqlAlchemyExecutionEngine,
    )

    class Dummy:
        @multicolumn_condition_partial(engine=SqlAlchemyExecutionEngine)
        def _sqlalchemy(self, column_list, **kwargs):
            # Always True expected condition -> unexpected is False
            return sa.literal(True)

    engine = _SqlEngineStub(["a"])  # type: ignore[arg-type]

    inner = Dummy._sqlalchemy  # type: ignore[attr-defined]
    _unexpected_condition, _compute, accessor = inner(
        Dummy(),
        execution_engine=engine,  # type: ignore[arg-type]
        metric_domain_kwargs={},
        metric_value_kwargs={},
        metrics=_metrics_with_columns(["a"]),
        runtime_configuration={},
    )
    # Inversion path executed; we primarily assert accessor preserved
    assert accessor == {"column_list": ["a"]}
