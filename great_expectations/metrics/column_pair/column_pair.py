from typing import Literal

from great_expectations.metrics.batch import BatchMetric
from great_expectations.metrics.metric import NonEmptyString, _MetricResult


class ColumnPairMetric(BatchMetric[_MetricResult], kw_only=True):
    column_A: NonEmptyString
    column_B: NonEmptyString
    ignore_row_if: Literal["both_values_are_missing", "either_value_is_missing", "neither"] = (
        "both_values_are_missing"
    )
