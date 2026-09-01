from __future__ import annotations

from functools import reduce

from great_expectations.compatibility.pyspark import functions as F
from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.execution_engine import (
    PandasExecutionEngine,
    SparkDFExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.map_metric_provider import (
    MulticolumnMapMetricProvider,
)
from great_expectations.expectations.metrics.map_metric_provider.multicolumn_condition_partial import (  # noqa: E501 # FIXME CoP
    multicolumn_condition_partial,
)


class MulticolumnValuesEqual(MulticolumnMapMetricProvider):
    """Row-wise equality across a set of columns, with null-safe comparison.

    All three engines implement the same semantics: two nulls are equal, and a null and a
    non-null are not. Each engine compares every column against the first one rather than
    every pair, which is O(num_columns) instead of O(num_columns^2) and is sufficient
    because equality is transitive.
    """

    condition_metric_name = "multicolumn_values.equal"
    condition_domain_keys = (
        "batch_id",
        "table",
        "column_list",
        "row_condition",
        "condition_parser",
        "ignore_row_if",
    )
    condition_value_keys = ()

    @multicolumn_condition_partial(engine=PandasExecutionEngine)
    def _pandas(cls, column_list, **kwargs):
        reference_column = column_list.iloc[:, 0]
        reference_is_null = reference_column.isna()
        # `DataFrame.nunique(axis=1)` would be the obvious spelling here, but it is a
        # per-row Python loop, and it counts distinct objects - so a `NaN` in a float
        # column and a `None` in an object column read as two different values, which
        # would make an all-null row unequal on Pandas while SQL and Spark call it equal.
        # Comparing each column to the reference is both vectorized and sentinel-agnostic.
        # The reference is included in the comparison so that the reduction is never
        # empty for a single-column domain; matching itself is trivially true.
        conditions = [
            (column == reference_column) | (column.isna() & reference_is_null)
            for _, column in column_list.items()
        ]
        return reduce(lambda left, right: left & right, conditions)

    @multicolumn_condition_partial(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(cls, column_list, **kwargs):
        reference_column = column_list[0]
        conditions = [
            sa.or_(
                sa.and_(reference_column.is_(None), column.is_(None)),
                sa.and_(
                    reference_column.isnot(None),
                    column.isnot(None),
                    reference_column == column,
                ),
            )
            for column in column_list[1:]
        ]
        # Seeded with `true()` so that a single-column domain yields a valid (trivially
        # true) clause; a bare `and_()` renders as an empty string and emits a
        # deprecation warning.
        return sa.and_(sa.true(), *conditions)

    @multicolumn_condition_partial(engine=SparkDFExecutionEngine)
    def _spark(cls, column_list, **kwargs):
        column_names = column_list.columns
        reference_column = F.col(column_names[0])
        conditions = [
            reference_column.eqNullSafe(F.col(column_name)) for column_name in column_names[1:]
        ]
        return reduce(lambda left, right: left & right, conditions, F.lit(True))
