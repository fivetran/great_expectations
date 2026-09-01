"""A regex metric that cannot compile for the active dialect must say so.

Six ``_sqlalchemy`` implementations share one fallback: when
``get_dialect_regex_expression`` has no branch for the active dialect it returns
``None`` and the metric raises ``NotImplementedError``. The message that exception
carries is the only statement of the cause that reaches
``ExpectationValidationResult.exception_info`` -- a bare ``raise`` records an empty
``exception_message``, which is indistinguishable from a regex that simply matched
nothing.

These tests pin the message at each of the six raise sites. The end-to-end
propagation of that message through the validation machinery is covered against a
live SQL Server in
``tests/integration/data_sources_and_expectations/expectations/test_expect_column_values_to_match_regex.py``.
"""

from typing import Any, Callable

import pytest

from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.expectations.metrics.column_aggregate_metrics import (
    ColumnValuesMatchRegexValues,
    ColumnValuesNotMatchRegexValues,
)
from great_expectations.expectations.metrics.column_map_metrics import (
    ColumnValuesMatchRegex,
    ColumnValuesMatchRegexList,
    ColumnValuesNotMatchRegex,
    ColumnValuesNotMatchRegexList,
)

# SQL Server has no branch in get_dialect_regex_expression, and this module is what
# SqlAlchemyExecutionEngine hands the metrics as `_dialect` for that backend.
MSSQL_DIALECT_MODULE = sa.dialects.mssql

EXPECTED_MESSAGE = "Regex is not supported for dialect mssql"


def _undecorated(metric_fn: Callable) -> Callable:
    """Peel the metric decorators off, leaving the implementation itself."""
    while hasattr(metric_fn, "__wrapped__"):
        metric_fn = metric_fn.__wrapped__
    return metric_fn


class StubSqlAlchemyExecutionEngine:
    """The little of the execution engine the aggregate metrics touch before raising."""

    dialect_module = MSSQL_DIALECT_MODULE

    def get_compute_domain(
        self, metric_domain_kwargs: dict, domain_type: Any
    ) -> tuple[Any, dict, dict]:
        return sa.table("test_table"), {}, {"column": "test_column"}


def _call_column_map_metric(metric_cls: Any, **kwargs: Any) -> None:
    _undecorated(metric_cls._sqlalchemy)(
        metric_cls,
        sa.column("test_column"),
        _dialect=MSSQL_DIALECT_MODULE,
        **kwargs,
    )


def _call_column_aggregate_metric(metric_cls: Any) -> None:
    _undecorated(metric_cls._sqlalchemy)(
        metric_cls,
        execution_engine=StubSqlAlchemyExecutionEngine(),
        metric_domain_kwargs={},
        metric_value_kwargs={"regex": "^abc$", "limit": None},
        metrics={},
        runtime_configuration={},
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "call_metric",
    [
        pytest.param(
            lambda: _call_column_map_metric(ColumnValuesMatchRegex, regex="^abc$"),
            id="column_values.match_regex",
        ),
        pytest.param(
            lambda: _call_column_map_metric(ColumnValuesNotMatchRegex, regex="^abc$"),
            id="column_values.not_match_regex",
        ),
        pytest.param(
            lambda: _call_column_map_metric(
                ColumnValuesMatchRegexList, regex_list=["^abc$"], match_on="any"
            ),
            id="column_values.match_regex_list",
        ),
        pytest.param(
            lambda: _call_column_map_metric(ColumnValuesNotMatchRegexList, regex_list=["^abc$"]),
            id="column_values.not_match_regex_list",
        ),
        pytest.param(
            lambda: _call_column_aggregate_metric(ColumnValuesMatchRegexValues),
            id="column_values.match_regex_values",
        ),
        pytest.param(
            lambda: _call_column_aggregate_metric(ColumnValuesNotMatchRegexValues),
            id="column_values.not_match_regex_values",
        ),
    ],
)
def test_regex_metric_names_the_unsupported_dialect(call_metric: Callable[[], None]) -> None:
    """Every raise site carries the same message, naming the dialect, not a module repr."""
    with pytest.raises(NotImplementedError) as exc_info:
        call_metric()

    assert str(exc_info.value) == EXPECTED_MESSAGE
