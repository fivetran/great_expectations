from typing import Literal

from great_expectations.metrics.domain import NonEmptyString
from great_expectations.metrics.metric_results import MetricResult


class BatchMetric:
    pass


class ColumnPairMetric(BatchMetric[MetricResult]):
    column_A: NonEmptyString
    column_B: NonEmptyString
    ignore_row_if: Literal["both_values_are_missing", "either_value_is_missing", "neither"] = (
        "both_values_are_missing"
    )
