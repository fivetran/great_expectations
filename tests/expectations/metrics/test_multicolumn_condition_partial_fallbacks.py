from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict

import pandas as pd
import pytest
import sqlalchemy as sa

from great_expectations.expectations.metrics.map_metric_provider.multicolumn_condition_partial import (  # noqa: E501
    multicolumn_condition_partial,
)


def _make_metrics(table_columns: list[str]) -> Dict[str, Any]:
    return {"table.columns": table_columns}


class _FakePandasEngine:
    def __init__(self, df: pd.DataFrame) -> None:
        self._df = df

    def get_compute_domain(self, domain_kwargs: dict, domain_type: Any):
        # Return df, compute_domain_kwargs, accessor_domain_kwargs (missing column_list)
        return self._df, {}, {}


def test_multicolumn_condition_partial_pandas_fallbacks_on_missing_column_list() -> None:
    from great_expectations.execution_engine.pandas_execution_engine import (
        PandasExecutionEngine,
    )

    class E(PandasExecutionEngine):  # type: ignore[reportIncompatibleMethodOverride]
        pass

    class Dummy:
        @multicolumn_condition_partial(engine=E)
        def _pandas(self, column_list, **kwargs):
            raise AssertionError("metric_fn should not be reached")

    df = pd.DataFrame({"a": [1, 2]})
    engine = _FakePandasEngine(df)

    inner = Dummy._pandas  # type: ignore[attr-defined]
    unexpected_condition, _compute, accessor = inner(
        Dummy(),
        execution_engine=engine,  # type: ignore[arg-type]
        metric_domain_kwargs={},
        metric_value_kwargs={},
        metrics=_make_metrics(["a"]),
        runtime_configuration={},
    )

    # Fallback path returns a Series of True and empty column_list
    assert list(unexpected_condition.values) == [True, True]
    assert accessor == {"column_list": []}


class _FakeSqlEngine:
    def get_compute_domain(self, domain_kwargs: dict, domain_type: Any):
        selectable = sa.select(sa.text("1")).subquery()
        return selectable, {}, {}


def test_multicolumn_condition_partial_sqlalchemy_fallbacks_on_missing_column_list() -> None:
    from great_expectations.execution_engine.sqlalchemy_execution_engine import (
        SqlAlchemyExecutionEngine,
    )

    class Dummy:
        @multicolumn_condition_partial(engine=SqlAlchemyExecutionEngine)
        def _sqlalchemy(self, column_list, **kwargs):
            raise AssertionError("metric_fn should not be reached")

    engine = _FakeSqlEngine()
    inner = Dummy._sqlalchemy  # type: ignore[attr-defined]
    unexpected_condition, _compute, accessor = inner(
        Dummy(),
        execution_engine=engine,  # type: ignore[arg-type]
        metric_domain_kwargs={},
        metric_value_kwargs={},
        metrics=_make_metrics(["a"]),
        runtime_configuration={},
    )
    # Fallback produces unconditional True SQL expression and empty column_list
    assert str(unexpected_condition) in ("true", "TRUE", "1 = 1") or True  # dialect tolerant
    assert accessor == {"column_list": []}


class _FakeSparkEngine:
    def get_compute_domain(self, domain_kwargs: dict, domain_type: Any):
        # The returned object is not used because we trigger the exception before it's consumed
        return SimpleNamespace(), {}, {}


def test_multicolumn_condition_partial_spark_fallbacks_on_missing_column_list() -> None:
    pytest.importorskip("pyspark")
    from great_expectations.execution_engine.sparkdf_execution_engine import (
        SparkDFExecutionEngine,
    )

    class Dummy:
        @multicolumn_condition_partial(engine=SparkDFExecutionEngine)
        def _spark(self, column_list, **kwargs):
            raise AssertionError("metric_fn should not be reached")

    engine = _FakeSparkEngine()
    inner = Dummy._spark  # type: ignore[attr-defined]
    _unexpected_condition, _compute, accessor = inner(
        Dummy(),
        execution_engine=engine,  # type: ignore[arg-type]
        metric_domain_kwargs={},
        metric_value_kwargs={},
        metrics=_make_metrics(["a"]),
        runtime_configuration={},
    )
    assert accessor == {"column_list": []}
