from __future__ import annotations

from typing import Any, Dict

import pandas as pd
import pytest

from great_expectations.expectations.metrics.map_metric_provider.multicolumn_condition_partial import (  # noqa: E501
    multicolumn_condition_partial,
)

pytestmark = pytest.mark.unit


class _PandasEngine:
    def __init__(self, df: pd.DataFrame, accessor: Dict[str, Any]):
        self._df = df
        self._accessor = accessor

    def get_compute_domain(self, domain_kwargs: dict, domain_type: Any):
        return self._df, {}, self._accessor


def test_pandas_map_condition_raises_then_fallbacks() -> None:
    from great_expectations.execution_engine.pandas_execution_engine import (
        PandasExecutionEngine,
    )

    class E(PandasExecutionEngine):  # type: ignore[misc]
        pass

    class Dummy:
        @multicolumn_condition_partial(engine=E)
        def _pandas(self, column_list, **kwargs):
            # Force error to trigger fallback path
            raise RuntimeError("boom")

    df = pd.DataFrame({"a": [1, 2]})
    engine = _PandasEngine(df, {"column_list": ["a"]})  # type: ignore[arg-type]

    inner = Dummy._pandas  # type: ignore[attr-defined]
    unexpected_condition, _compute, accessor = inner(
        Dummy(),
        execution_engine=engine,  # type: ignore[arg-type]
        metric_domain_kwargs={},
        metric_value_kwargs={},
        metrics={"table.columns": ["a"]},
        runtime_configuration={},
    )

    # Fallback path returns True for all rows and empty column_list
    assert list(unexpected_condition.values) == [True, True]
    assert accessor == {"column_list": []}
