from typing import Union

from great_expectations.metrics import Metric
from great_expectations.metrics.domain import MultiColumnValues
from great_expectations.metrics.metric_results import MetricResult


class MultiColumnSumEqualUnexpectedCountResult(MetricResult[int]): ...


class MultiColumnSumEqualUnexpectedCount(
    Metric[MultiColumnSumEqualUnexpectedCountResult], MultiColumnValues
):
    name = "multicolumn_sum.equal.unexpected_count"
    sum_total: Union[int, float]
