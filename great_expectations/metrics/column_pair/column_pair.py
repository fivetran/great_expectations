from typing import Literal, Optional

from great_expectations.compatibility.pydantic import StrictStr
from great_expectations.expectations.model_field_types import ConditionParser
from great_expectations.metrics.metric import Metric, NonEmptyString, _MetricResult


class ColumnPairMetric(Metric[_MetricResult], kw_only=True):
    column_A: NonEmptyString
    column_B: NonEmptyString
    ignore_row_if: Literal["both_values_are_missing", "either_value_is_missing", "neither"] = (
        "both_values_are_missing"
    )
    row_condition: Optional[StrictStr] = None
    condition_parser: Optional[ConditionParser] = None
