from typing import Literal, Optional

from great_expectations.compatibility.pydantic import StrictStr
from great_expectations.expectations.model_field_types import ConditionParser
from great_expectations.metrics.metric import Metric, _MetricResult


class MultiColumnMetric(Metric[_MetricResult], kw_only=True):
    column_list: list[str]
    row_condition: Optional[StrictStr] = None
    condition_parser: Optional[ConditionParser] = None
    ignore_row_if: Literal["all_values_are_missing", "any_value_is_missing", "never"] = (
        "all_values_are_missing"
    )
