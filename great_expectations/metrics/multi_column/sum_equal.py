from typing import Union

from great_expectations.metrics.metric_results import MetricResult
from great_expectations.metrics.multi_column import MultiColumnMetric


class MultiColumnSumEqualUnexpectedCountResult(MetricResult[int]): ...


class MultiColumnSumEqualUnexpectedCount(
    MultiColumnMetric[MultiColumnSumEqualUnexpectedCountResult]
):
    name = "multicolumn_sum.equal.unexpected_count"
    sum_total: Union[int, float]
