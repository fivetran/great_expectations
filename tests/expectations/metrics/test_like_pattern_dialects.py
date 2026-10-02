from inspect import unwrap
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest
from sqlalchemy.dialects.mysql.base import MySQLDialect
from sqlalchemy.dialects.oracle.base import OracleDialect

from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.expectations.metrics.column_map_metrics import (
    column_values_match_like_pattern,
    column_values_match_like_pattern_list,
    column_values_not_match_like_pattern,
    column_values_not_match_like_pattern_list,
)
from great_expectations.expectations.metrics.util import (
    get_dialect_like_pattern_expression,
)


class _DialectModule(ModuleType):
    dialect: type[Any]


class _OracleDialectSubclass(OracleDialect):
    pass


class _SingleStoreDialectSubclass(MySQLDialect):
    pass


@pytest.mark.unit
@pytest.mark.parametrize(
    "dialect_class",
    [
        pytest.param(_OracleDialectSubclass, id="oracle"),
        pytest.param(_SingleStoreDialectSubclass, id="singlestore"),
    ],
)
@pytest.mark.parametrize("positive", [True, False], ids=["match", "not-match"])
def test_like_pattern_expression_supports_oracle_and_singlestore_dialect_subclasses(
    dialect_class: type[Any],
    positive: bool,
) -> None:
    dialect = _DialectModule("test_dialect")
    dialect.dialect = dialect_class

    expression = get_dialect_like_pattern_expression(
        column=sa.Column("value", sa.String()),
        dialect=dialect,
        like_pattern="foo%",
        positive=positive,
    )

    assert expression is not None


@pytest.mark.unit
@pytest.mark.parametrize(
    ("metric_provider", "metric_kwargs"),
    [
        pytest.param(
            column_values_match_like_pattern.ColumnValuesMatchLikePattern,
            {"like_pattern": "foo%"},
            id="match-one",
        ),
        pytest.param(
            column_values_not_match_like_pattern.ColumnValuesNotMatchLikePattern,
            {"like_pattern": "foo%"},
            id="not-match-one",
        ),
        pytest.param(
            column_values_match_like_pattern_list.ColumnValuesMatchLikePatternList,
            {"like_pattern_list": ["foo%"], "match_on": "any"},
            id="match-list",
        ),
        pytest.param(
            column_values_not_match_like_pattern_list.ColumnValuesNotMatchLikePatternList,
            {"like_pattern_list": ["foo%"]},
            id="not-match-list",
        ),
    ],
)
def test_unsupported_dialect_raises_not_implemented_error(
    metric_provider: Any,
    metric_kwargs: dict[str, Any],
) -> None:
    class UnsupportedDialect:
        name = "unsupported"

    metric_fn = unwrap(metric_provider._sqlalchemy)

    with pytest.raises(NotImplementedError):
        metric_fn(
            metric_provider,
            column=sa.column("value"),
            _dialect=SimpleNamespace(name="unsupported", dialect=UnsupportedDialect),
            **metric_kwargs,
        )
