from typing import Optional

from great_expectations.compatibility.pydantic import StrictStr
from great_expectations.expectations.model_field_types import ConditionParser
from great_expectations.metrics.metric import Metric, NonEmptyString, _MetricResult


class ColumnMetric(Metric[_MetricResult], kw_only=True):
    column: NonEmptyString
    row_condition: Optional[StrictStr] = None
    condition_parser: Optional[ConditionParser] = None
