from __future__ import annotations

import logging

from great_expectations.execution_engine.sqlalchemy_execution_engine import (
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.like_pattern import (
    get_dialect_display_name,
    get_dialect_like_pattern_expression,
)
from great_expectations.expectations.metrics.map_metric_provider import (
    ColumnMapMetricProvider,
    column_condition_partial,
)

logger = logging.getLogger(__name__)


class ColumnValuesNotMatchLikePattern(ColumnMapMetricProvider):
    condition_metric_name = "column_values.not_match_like_pattern"
    condition_value_keys = (
        "like_pattern",
        "escape",
    )

    @column_condition_partial(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(cls, column, like_pattern, _dialect, escape=None, **kwargs):
        like_pattern_expression = get_dialect_like_pattern_expression(
            column, _dialect, like_pattern, positive=False, escape=escape
        )
        if like_pattern_expression is None:
            dialect_name = get_dialect_display_name(_dialect)
            logger.warning(f"Like patterns are not supported for dialect {dialect_name}")
            raise NotImplementedError(
                f"Like patterns are not supported for dialect {dialect_name}"
            )

        return like_pattern_expression
