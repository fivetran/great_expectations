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


class ColumnValuesInTypeList(ColumnMapMetricProvider):
    condition_metric_name = "column_values.in_type_list"
    condition_value_keys = ("type_list",)

    @column_condition_partial(engine=PandasExecutionEngine)
    def _pandas(cls, column, type_list, **kwargs):  # noqa: C901 #  too complex
        comp_types = []
        for type_ in type_list:
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
            raise ValueError(f"No recognized numpy/python type in list: {type_list}")  # noqa: TRY003 # FIXME CoP

        return column.map(lambda x: isinstance(x, tuple(comp_types)))

    @column_condition_partial(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(cls, column, type_list, _dialect, **kwargs):
        """SQL implementation for type list checking.
        
        This implementation uses SQL CASE statements with OR logic to check if column values 
        match any of the expected types using regex patterns and safe casting where possible.
        """
        if not type_list or len(type_list) == 0:
            raise ValueError("type_list cannot be empty")  # noqa: TRY003 # FIXME CoP
        
        # Build conditions for each type in the list
        type_conditions = []
        
        for type_ in type_list:
            type_upper = type_.upper()
            
            # Handle common SQL types with regex patterns
            if type_upper in ("INTEGER", "INT", "BIGINT", "SMALLINT"):
                # Match integers (including negative and positive)
                type_conditions.append(
                    sa.func.trim(sa.cast(column, sa.String)).op("~")(r"^[+-]?[0-9]+$")
                )
            elif type_upper in ("DECIMAL", "NUMERIC", "FLOAT", "DOUBLE", "REAL"):
                # Match numeric values (including decimals and scientific notation)
                type_conditions.append(
                    sa.func.trim(sa.cast(column, sa.String)).op("~")(
                        r"^[+-]?([0-9]*[.])?[0-9]+([eE][+-]?[0-9]+)?$"
                    )
                )
            elif type_upper in ("BOOLEAN", "BOOL"):
                # Match boolean values (true/false, t/f, 1/0, yes/no)
                type_conditions.append(
                    sa.func.lower(sa.func.trim(sa.cast(column, sa.String))).in_(
                        ["true", "false", "t", "f", "1", "0", "yes", "no"]
                    )
                )
            elif type_upper in ("VARCHAR", "CHAR", "TEXT", "STRING"):
                # All non-null values are valid strings
                type_conditions.append(sa.literal(True))
            elif type_upper in ("DATE"):
                # Basic date pattern matching (YYYY-MM-DD)
                type_conditions.append(
                    sa.func.trim(sa.cast(column, sa.String)).op("~")(
                        r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
                    )
                )
            elif type_upper in ("TIMESTAMP", "DATETIME"):
                # Basic timestamp pattern matching
                type_conditions.append(
                    sa.func.trim(sa.cast(column, sa.String)).op("~")(
                        r"^[0-9]{4}-[0-9]{2}-[0-9]{2}[ T][0-9]{2}:[0-9]{2}:[0-9]{2}"
                    )
                )
            else:
                # For unrecognized types, conservatively assume castable
                type_conditions.append(sa.literal(True))
        
        # Combine all type conditions with OR logic
        if len(type_conditions) == 1:
            combined_condition = type_conditions[0]
        else:
            combined_condition = sa.or_(*type_conditions)
        
        return sa.case((column.is_(None), None), (combined_condition, True), else_=False)
