from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar, Optional, Sequence, Union

from typing_extensions import NotRequired, TypedDict

from great_expectations.compatibility.sqlalchemy import (
    sqlalchemy as sa,
)
from great_expectations.constants import MAX_RESULT_RECORDS
from great_expectations.execution_engine.sqlalchemy_dialect import GXSqlDialect
from great_expectations.expectations.metrics.metric_provider import MetricProvider
from great_expectations.util import get_sqlalchemy_subquery_type

if TYPE_CHECKING:
    from great_expectations.execution_engine import SqlAlchemyExecutionEngine

logger = logging.getLogger(__name__)

_ORDER_BY_TOKEN = "ORDER BY"
_OFFSET_TOKEN = "OFFSET"


def has_top_level_token(query: str, token: str) -> bool:
    """Return True if *token* appears at parentheses depth 0 (case-insensitive).

    Tokens nested inside parenthesised subqueries or window-function
    OVER() clauses are ignored.
    """
    upper = query.upper()
    upper_token = token.upper()
    depth = 0
    token_len = len(upper_token)
    query_len = len(upper)
    i = 0
    while i < query_len:
        char = upper[i]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif depth == 0 and upper[i : i + token_len] == upper_token:
            return True
        i += 1
    return False


def find_last_top_level_order_by(query: str) -> int:
    """Return the character position of the last top-level ORDER BY, or -1.

    ORDER BY inside parenthesised subqueries or window-function OVER()
    clauses (depth > 0) is ignored.
    """
    upper = query.upper()
    last_pos = -1
    depth = 0
    token_len = len(_ORDER_BY_TOKEN)
    query_len = len(upper)
    i = 0
    while i < query_len:
        char = upper[i]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif depth == 0 and upper[i : i + token_len] == _ORDER_BY_TOKEN:
            last_pos = i
        i += 1
    return last_pos


def strip_top_level_order_by(query: str) -> str:
    """Strip the last top-level ORDER BY clause from a SQL query.

    Used when wrapping user queries in COUNT(*) for SQL Server, where ORDER BY
    in a subquery is invalid unless TOP or OFFSET is present.  Returns the
    query unchanged if no top-level ORDER BY exists or a top-level OFFSET
    is present (stripping would remove the pagination clause).
    """
    if has_top_level_token(query, _OFFSET_TOKEN):
        return query

    pos = find_last_top_level_order_by(query)
    if pos == -1:
        return query

    return query[:pos].rstrip()


class MissingElementError(TypeError):
    def __init__(self):
        super().__init__(
            "The batch subquery selectable does not contain an "
            "element from which query parameters can be extracted."
        )


class MissingParameterError(ValueError):
    def __init__(self, parameter_name: str):
        super().__init__(f"Must provide `{parameter_name}` to `{self.__class__.__name__}` metric.")


class InvalidParameterTypeError(TypeError):
    def __init__(self, parameter_name: str, expected_type: type):
        super().__init__(f"`{parameter_name}` must be provided as type `{expected_type}`.")


class QueryParameters(TypedDict):
    column: NotRequired[str]
    column_A: NotRequired[str]
    column_B: NotRequired[str]
    columns: NotRequired[list[str]]


class QueryMetricProvider(MetricProvider):
    """Base class for all Query Metrics, which define metrics to construct SQL queries.

     An example of this is `query.table`,
     which takes in a SQL query & target table name, and returns the result of that query.

     In some cases, subclasses of MetricProvider, such as QueryMetricProvider, will already
     have correct values that may simply be inherited by Metric classes.

     ---Documentation---
         - https://docs.greatexpectations.io/docs/guides/expectations/creating_custom_expectations/how_to_create_custom_query_expectations

    Args:
         metric_name (str): A name identifying the metric. Metric Name must be globally unique in
             a great_expectations installation.
         domain_keys (tuple): A tuple of the keys used to determine the domain of the metric.
         value_keys (tuple): A tuple of the keys used to determine the value of the metric.
         query (str): A valid SQL query.
    """

    domain_keys = ("batch_id", "row_condition", "condition_parser")

    query_param_name: ClassVar[str] = "query"

    dialect_columns_require_subquery_aliases: ClassVar[set[GXSqlDialect]] = {
        GXSqlDialect.POSTGRESQL
    }

    @classmethod
    def _get_query_from_metric_value_kwargs(cls, metric_value_kwargs: dict) -> str:
        query_param = cls.query_param_name
        query: str | None = metric_value_kwargs.get(query_param) or cls.default_kwarg_values.get(
            query_param
        )
        if not query:
            raise MissingParameterError(query_param)
        if not isinstance(query, str):
            raise InvalidParameterTypeError(query_param, str)

        return query

    @classmethod
    def _get_parameters_dict_from_query_parameters(
        cls, query_parameters: Optional[QueryParameters]
    ) -> dict[str, Any]:
        if not query_parameters:
            return {}
        elif query_parameters and "columns" in query_parameters:
            columns = query_parameters.pop("columns")
            query_columns = {f"col_{i}": col for i, col in enumerate(columns, 1)}
            return {**query_parameters, **query_columns}
        else:
            return {**query_parameters}

    @classmethod
    def _get_substituted_batch_subquery_from_query_and_batch_selectable(
        cls,
        query: str,
        batch_selectable: sa.Selectable,
        execution_engine: SqlAlchemyExecutionEngine,
        query_parameters: Optional[QueryParameters] = None,
    ) -> str:
        parameters = cls._get_parameters_dict_from_query_parameters(query_parameters)

        if isinstance(batch_selectable, sa.Table):
            query = query.format(batch=batch_selectable, **parameters)
        elif isinstance(
            batch_selectable, (sa.sql.Select, get_sqlalchemy_subquery_type())
        ):  # specifying a row_condition returns the active batch as a Select
            # specifying an unexpected_rows_query returns the active batch as a Subquery or Alias
            # this requires compilation & aliasing when formatting the parameterized query
            batch = batch_selectable.compile(
                dialect=execution_engine.engine.dialect, compile_kwargs={"literal_binds": True}
            )
            # all join queries require the user to have taken care of aliasing themselves
            if "JOIN" in query.upper():
                query = query.format(batch=f"({batch})", **parameters)
            else:
                query = query.format(batch=f"({batch}) AS subselect", **parameters)
        else:
            query = query.format(batch=f"({batch_selectable})", **parameters)

        if getattr(execution_engine, "dialect_name", None) == "mssql":  # fix for batch error
            query = query.replace("WHERE true", "WHERE 1=1")

        return query

    @classmethod
    def _get_sqlalchemy_records_from_substituted_batch_subquery(
        cls,
        substituted_batch_subquery: str,
        execution_engine: SqlAlchemyExecutionEngine,
        fetch_all: bool = False,
    ) -> list[dict]:
        query_result = execution_engine.execute_query(sa.text(substituted_batch_subquery))
        result: Union[Sequence[sa.Row[Any]], Any] = (
            query_result.fetchall() if fetch_all else query_result.fetchmany(MAX_RESULT_RECORDS)
        )

        if isinstance(result, Sequence):
            return [element._asdict() for element in result]
        else:
            return [result]
