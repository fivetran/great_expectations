from types import ModuleType
from typing import Any, Callable

import pytest
from sqlalchemy.dialects.mysql.base import MySQLDialect
from sqlalchemy.dialects.oracle.base import OracleDialect

from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.expectations.metrics.column_map_metrics import (
    ColumnValuesMatchLikePattern,
    ColumnValuesMatchLikePatternList,
    ColumnValuesNotMatchLikePattern,
    ColumnValuesNotMatchLikePatternList,
)
from great_expectations.expectations.metrics.util import (
    get_dialect_like_pattern_expression,
)


def _dialect_module(name: str, base: type) -> ModuleType:
    dialect_module = ModuleType(name)
    dialect_module.dialect = type(  # type: ignore[attr-defined]
        f"{name.title()}Dialect", (base,), {"name": name}
    )
    return dialect_module


@pytest.mark.unit
@pytest.mark.parametrize(
    "dialect_module",
    [
        pytest.param(
            _dialect_module("oracle", OracleDialect),
            id="oracle-base-dialect",
        ),
        pytest.param(
            _dialect_module("singlestore", MySQLDialect),
            id="mysql-base-dialect",
        ),
    ],
)
def test_like_pattern_supports_base_dialect_subclasses(dialect_module: ModuleType) -> None:
    expression = get_dialect_like_pattern_expression(
        column=sa.Column("test_column", sa.String),
        dialect=dialect_module,
        like_pattern="foo%",
    )

    assert expression is not None


def _undecorated(metric_fn: Callable) -> Callable:
    while hasattr(metric_fn, "__wrapped__"):
        metric_fn = metric_fn.__wrapped__
    return metric_fn


def _call_metric(metric_cls: Any, **kwargs: Any) -> None:
    unsupported_dialect = _dialect_module("unsupported", object)
    _undecorated(metric_cls._sqlalchemy)(
        metric_cls,
        sa.column("test_column"),
        _dialect=unsupported_dialect,
        **kwargs,
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "call_metric",
    [
        pytest.param(
            lambda: _call_metric(ColumnValuesMatchLikePattern, like_pattern="foo%"),
            id="column_values.match_like_pattern",
        ),
        pytest.param(
            lambda: _call_metric(ColumnValuesNotMatchLikePattern, like_pattern="foo%"),
            id="column_values.not_match_like_pattern",
        ),
        pytest.param(
            lambda: _call_metric(
                ColumnValuesMatchLikePatternList,
                like_pattern_list=["foo%"],
                match_on="any",
            ),
            id="column_values.match_like_pattern_list",
        ),
        pytest.param(
            lambda: _call_metric(
                ColumnValuesNotMatchLikePatternList,
                like_pattern_list=["foo%"],
            ),
            id="column_values.not_match_like_pattern_list",
        ),
    ],
)
def test_like_pattern_metric_names_unsupported_dialect(
    call_metric: Callable[[], None],
) -> None:
    with pytest.raises(NotImplementedError) as exc_info:
        call_metric()

    assert str(exc_info.value) == "Like patterns are not supported for dialect unsupported"
