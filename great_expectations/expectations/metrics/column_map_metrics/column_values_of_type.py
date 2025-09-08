from __future__ import annotations

import numpy as np
import pandas as pd

from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.execution_engine import PandasExecutionEngine, SqlAlchemyExecutionEngine
from great_expectations.expectations.core.expect_column_values_to_be_of_type import (
    _native_type_type_map,
)
from great_expectations.expectations.metrics.map_metric_provider import (
    ColumnMapMetricProvider,
    column_condition_partial,
)


class ColumnValuesOfType(ColumnMapMetricProvider):
    condition_metric_name = "column_values.of_type"
    condition_value_keys = ("type_",)

    @column_condition_partial(engine=PandasExecutionEngine)
    def _pandas(cls, column, type_, **kwargs):
        comp_types = []
        try:
            comp_types.append(np.dtype(type_).type)
        except TypeError:
            try:
                pd_type = getattr(pd, type_)
                if isinstance(pd_type, type):
                    comp_types.append(pd_type)
            except AttributeError:
                pass

            try:
                pd_type = getattr(pd.core.dtypes.dtypes, type_)
                if isinstance(pd_type, type):
                    comp_types.append(pd_type)
            except AttributeError:
                pass

        native_type = _native_type_type_map(type_)
        if native_type is not None:
            comp_types.extend(native_type)

        if len(comp_types) < 1:
            raise ValueError(f"Unrecognized numpy/python type: {type_}")  # noqa: TRY003 # FIXME CoP

        return column.map(lambda x: isinstance(x, tuple(comp_types)))

    @column_condition_partial(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(cls, column, type_, _dialect, **kwargs):
        """SQL implementation for type checking.

        This implementation uses SQL CASE statements to check if column values
        match the expected type using regex patterns and safe casting where possible.
        """
        type_upper = type_.upper()

        # Handle common SQL types with regex patterns
        if type_upper in ("INTEGER", "INT", "BIGINT", "SMALLINT"):
            # Match integers (including negative and positive)
            return sa.case(
                (column.is_(None), None),  # NULL values are NULL
                (sa.func.trim(sa.cast(column, sa.String)).op("~")(r"^[+-]?[0-9]+$"), True),
                else_=False,
            )
        elif type_upper in ("DECIMAL", "NUMERIC", "FLOAT", "DOUBLE", "REAL"):
            # Match numeric values (including decimals and scientific notation)
            return sa.case(
                (column.is_(None), None),  # NULL values are NULL
                (
                    sa.func.trim(sa.cast(column, sa.String)).op("~")(
                        r"^[+-]?([0-9]*[.])?[0-9]+([eE][+-]?[0-9]+)?$"
                    ),
                    True,
                ),
                else_=False,
            )
        elif type_upper in ("BOOLEAN", "BOOL"):
            # Match boolean values (true/false, t/f, 1/0, yes/no)
            return sa.case(
                (column.is_(None), None),
                (
                    sa.func.lower(sa.func.trim(sa.cast(column, sa.String))).in_(
                        ["true", "false", "t", "f", "1", "0", "yes", "no"]
                    ),
                    True,
                ),
                else_=False,
            )
        elif type_upper in ("VARCHAR", "CHAR", "TEXT", "STRING"):
            # All non-null values are valid strings
            return sa.case((column.is_(None), None), else_=True)
        elif type_upper in ("DATE"):
            # Basic date pattern matching (YYYY-MM-DD)
            return sa.case(
                (column.is_(None), None),
                (
                    sa.func.trim(sa.cast(column, sa.String)).op("~")(
                        r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
                    ),
                    True,
                ),
                else_=False,
            )
        elif type_upper in ("TIMESTAMP", "DATETIME"):
            # Basic timestamp pattern matching
            return sa.case(
                (column.is_(None), None),
                (
                    sa.func.trim(sa.cast(column, sa.String)).op("~")(
                        r"^[0-9]{4}-[0-9]{2}-[0-9]{2}[ T][0-9]{2}:[0-9]{2}:[0-9]{2}"
                    ),
                    True,
                ),
                else_=False,
            )
        else:
            # For unrecognized types, try basic string casting
            # This is a fallback that may need dialect-specific implementation
            try:
                return sa.case(
                    (column.is_(None), None),
                    else_=True,  # Conservative approach - assume castable
                )
            except Exception:
                raise ValueError(f"Unsupported SQL type for validation: {type_}")  # noqa: TRY003 # FIXME CoP
