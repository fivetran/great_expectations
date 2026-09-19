"""Type comparison utilities for column type validation expectations.

This module consolidates all type-comparison logic used by
ExpectColumnValuesToBeOfType and ExpectColumnValuesToBeInTypeList,
including dialect-aware dispatching for SQLAlchemy backends.
"""

from __future__ import annotations

import inspect
import logging
from types import ModuleType
from typing import TYPE_CHECKING, Any, Sequence

from great_expectations.compatibility import aws, trino
from great_expectations.compatibility.bigquery import (
    BIGQUERY_GEO_SUPPORT,
    bigquery_types_tuple,
)
from great_expectations.compatibility.bigquery import (
    sqlalchemy_bigquery as BigQueryDialect,
)
from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.exceptions import InvalidExpectationConfigurationError
from great_expectations.execution_engine.sqlalchemy_dialect import GXSqlDialect
from great_expectations.util import (
    get_clickhouse_sqlalchemy_potential_type,
    get_pyathena_potential_type,
)

if TYPE_CHECKING:
    from great_expectations.execution_engine import SqlAlchemyExecutionEngine

logger = logging.getLogger(__name__)

try:
    import teradatasqlalchemy.dialect
    import teradatasqlalchemy.types as teradatatypes
except ImportError:
    teradatasqlalchemy = None
    teradatatypes = None

try:
    import clickhouse_sqlalchemy
    import clickhouse_sqlalchemy.types as ch_types
except (ImportError, KeyError):
    clickhouse_sqlalchemy = None
    ch_types = None


# Uses GXSqlDialect enum members (not raw strings) to match the rest of the
# codebase.  GXSqlDialect.__eq__ handles cross-type comparison with str values
# returned by SqlAlchemyExecutionEngine.dialect_name.
CASE_INSENSITIVE_DIALECTS: frozenset[GXSqlDialect] = frozenset(
    {
        GXSqlDialect.DATABRICKS,
        GXSqlDialect.POSTGRESQL,
        GXSqlDialect.SNOWFLAKE,
        GXSqlDialect.SQL_SERVER,
        GXSqlDialect.TRINO,
    }
)


def native_type_type_map(type_: str) -> tuple[type, ...] | None:  # noqa: C901, PLR0911
    """Map a string type name to a tuple of native Python types.

    Used by pandas validation paths to resolve type names like "int", "str", etc.
    Returns None for unrecognized types.
    """
    if type_.lower() == "none":
        return (type(None),)
    elif type_.lower() == "bool":
        return (bool,)
    elif type_.lower() in ["int", "long"]:
        return (int,)
    elif type_.lower() == "float":
        return (float,)
    elif type_.lower() == "bytes":
        return (bytes,)
    elif type_.lower() == "complex":
        return (complex,)
    elif type_.lower() in ["str", "string_types"]:
        return (str,)
    elif type_.lower() == "list":
        return (list,)
    elif type_.lower() == "dict":
        return (dict,)
    elif type_.lower() == "unicode":
        return None
    return None


def compare_column_type(
    execution_engine: SqlAlchemyExecutionEngine,
    actual_column_type: Any,
    expected_type: str,
) -> tuple[bool, Any]:
    """Compare an actual column type against an expected type string.

    Dispatches based on dialect:
    - For CASE_INSENSITIVE_DIALECTS: case-insensitive string comparison.
    - For all others: resolves expected_type to a SQLAlchemy type class and uses isinstance().

    Returns:
        (success, observed_value) where observed_value is actual_column_type as-is
        for case-insensitive dialects (typically a CaseInsensitiveString) or
        type(actual_column_type).__name__ for the isinstance path.
    """
    if execution_engine.dialect_name in CASE_INSENSITIVE_DIALECTS:
        success = _compare_type_string(actual_column_type, expected_type)
        return success, actual_column_type
    else:
        types = _get_potential_sqlalchemy_types(
            execution_engine=execution_engine, expected_type=expected_type
        )
        success = isinstance(actual_column_type, tuple(types))
        return success, type(actual_column_type).__name__


def compare_column_type_list(
    execution_engine: SqlAlchemyExecutionEngine,
    actual_column_type: Any,
    expected_types_list: Sequence[str],
) -> tuple[bool, str]:
    """Compare an actual column type against a list of expected type strings.

    Dispatches based on dialect:
    - For CASE_INSENSITIVE_DIALECTS: case-insensitive string comparison against each type.
    - For all others: resolves each type to a SQLAlchemy type class and uses isinstance().

    Returns:
        (success, observed_value) where observed_value is the type string representation.
    """
    if execution_engine.dialect_name in CASE_INSENSITIVE_DIALECTS:
        if isinstance(actual_column_type, str):
            success = any(
                actual_column_type.casefold() == expected_type.casefold()
                for expected_type in expected_types_list
            )
            return success, actual_column_type
        else:
            ret_type = type(actual_column_type).__name__
            success = any(
                ret_type.casefold() == expected_type.casefold()
                for expected_type in expected_types_list
            )
            return success, ret_type
    else:
        types = []
        for type_ in expected_types_list:
            types.extend(
                _get_potential_sqlalchemy_types(
                    execution_engine=execution_engine, expected_type=type_, strict=False
                )
            )
        if not types:
            raise _unresolvable_type_error(execution_engine, expected_types_list)
        success = isinstance(actual_column_type, tuple(types))
        return success, type(actual_column_type).__name__


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _unresolvable_type_error(
    execution_engine: SqlAlchemyExecutionEngine, names: Sequence[str]
) -> InvalidExpectationConfigurationError:
    quoted = ", ".join(repr(name) for name in names)
    noun = "type" if len(names) == 1 else "types"
    return InvalidExpectationConfigurationError(
        f"Unrecognized {noun}: {quoted} could not be resolved against the "
        f"{execution_engine.dialect_name} dialect module or the generic sqlalchemy "
        f"namespace. Check the spelling, or use a type name the dialect supports."
    )


def _compare_type_string(actual_column_type: Any, expected_type: str) -> bool:
    """Case-insensitive single-type comparison for CASE_INSENSITIVE_DIALECTS."""
    if isinstance(actual_column_type, str):
        # Preserve custom __eq__ behavior for str subclasses such as
        # CaseInsensitiveString, but normalize plain str values explicitly.
        if type(actual_column_type) is str:
            return actual_column_type.casefold() == expected_type.casefold()
        return actual_column_type == expected_type
    return str(actual_column_type).casefold() == expected_type.casefold()


def _get_potential_sqlalchemy_types(  # noqa: C901
    execution_engine: SqlAlchemyExecutionEngine, expected_type: str, *, strict: bool = True
) -> list:
    """Resolve a type name to candidate SQLAlchemy classes.

    With ``strict`` the name must resolve; an unresolvable name raises rather than
    yielding an empty candidate list, which would make ``isinstance(value, ())``
    unconditionally False. Callers handling a type list pass ``strict=False``, because
    a list is allowed to name types belonging to other backends.
    """
    types: list = []
    type_module = _get_dialect_type_module(execution_engine=execution_engine)
    try:
        # bigquery geography requires installing an extra package
        if (
            expected_type.lower() == "geography"
            and execution_engine.engine.dialect.name.lower() == GXSqlDialect.BIGQUERY
            and not BIGQUERY_GEO_SUPPORT
        ):
            logger.warning(
                "BigQuery GEOGRAPHY type is not supported by default. "
                + "To install support, please run:"
                + "  $ pip install 'sqlalchemy-bigquery[geography]'"
            )
            # Missing optional support, not an unresolvable name: the warning above is
            # actionable, so return empty rather than raising below.
            return types
        elif type_module.__name__ == "pyathena.sqlalchemy_athena":
            potential_type = get_pyathena_potential_type(type_module, expected_type)
            # In the case of the PyAthena dialect we need to verify that
            # the type returned is indeed a type and not an instance.
            if not inspect.isclass(potential_type):
                real_type = type(potential_type)
            else:
                real_type = potential_type
            types.append(real_type)
        elif type_module.__name__ == "clickhouse_sqlalchemy.drivers.base":
            potential_type = get_clickhouse_sqlalchemy_potential_type(type_module, expected_type)
            types.append(potential_type)
        elif type_module.__name__ == "sqlalchemy_redshift.dialect":
            types.extend(_get_redshift_sqlalchemy_types(type_module, expected_type))
        else:
            potential_type = getattr(type_module, expected_type)
            types.append(potential_type)
    except AttributeError:
        logger.debug(f"Unrecognized type: {expected_type}")

    if not types:
        # A dialect module re-exports only the subset of generic types it chooses to.
        # Oracle exports NUMBER and VARCHAR2 but not INTEGER, yet reflects an INTEGER
        # column as a generic sqlalchemy.INTEGER.
        generic_type = getattr(sa, expected_type, None)
        if generic_type is not None:
            types.append(generic_type)
        elif strict:
            raise _unresolvable_type_error(execution_engine, [expected_type])
        else:
            logger.debug(f"Unrecognized type: {expected_type}")

    return types


def _get_redshift_sqlalchemy_types(type_module: ModuleType, expected_type: Any) -> list:
    types: list = []
    potential_type = getattr(type_module, expected_type)
    types.append(potential_type)
    if expected_type.lower() == "decimal":
        # There is no redshift numeric type NUMERIC. It is suppose to be a synonym for
        # the official type DECIMAL, according to the docs:
        # https://docs.aws.amazon.com/redshift/latest/dg/c_Supported_data_types.html
        # However we have observed the raw sqltypes.[NUMERIC|Numeric] instead so we
        # add this as an allowed matching type.
        types.append(sa.sql.sqltypes.NUMERIC)
    return types


def _get_dialect_type_module(  # noqa: C901, PLR0911
    execution_engine: SqlAlchemyExecutionEngine,
) -> ModuleType:
    if execution_engine.dialect_module is None:
        logger.warning("No sqlalchemy dialect found; relying on top-level sqlalchemy types.")
        return sa

    # Redshift does not (yet) export types to top level; only recognize base SA types
    if aws.redshiftdialect and isinstance(
        execution_engine.dialect_module,
        aws.redshiftdialect.RedshiftDialect,
    ):
        return execution_engine.dialect_module.sa
    else:
        pass

    # Bigquery works with newer versions, but use a patch if we had to define bigquery_types_tuple
    try:
        if BigQueryDialect and (
            isinstance(
                execution_engine.dialect_module,
                BigQueryDialect,
            )
            and bigquery_types_tuple is not None
        ):
            return bigquery_types_tuple
    except (TypeError, AttributeError):
        pass

    # Teradata types module
    try:
        if (
            teradatasqlalchemy is not None
            and issubclass(
                execution_engine.dialect_module,  # type: ignore[arg-type] # dialect_module can be a class
                teradatasqlalchemy.dialect.TeradataDialect,
            )
            and teradatatypes is not None
        ):
            return teradatatypes
    except (TypeError, AttributeError):
        pass

    try:
        if (
            clickhouse_sqlalchemy is not None
            and issubclass(
                execution_engine.dialect_module,  # type: ignore[arg-type] # dialect_module can be a class
                clickhouse_sqlalchemy.drivers.base.ClickHouseDialect,
            )
            and ch_types is not None
        ):
            return ch_types
    except (TypeError, AttributeError):
        pass

    # Trino types module
    try:
        if (
            trino.trinodialect
            and trino.trinotypes
            and isinstance(
                execution_engine.dialect,
                trino.trinodialect.TrinoDialect,
            )
        ):
            return trino.trinotypes
    except (TypeError, AttributeError):
        pass

    return execution_engine.dialect_module
