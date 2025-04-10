from typing import Any

from great_expectations.metrics.column import ColumnMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnSampleValuesResult(MetricResult[list[Any]]): ...


class ColumnSampleValues(ColumnMetric[ColumnSampleValuesResult]):
    """
    This metric returns a list of sample values from the column.

    It is only supported for SQLAlchemy execution engines at this time.

    Args:
        count: The number of sample values to return.
    """

    name = "column.sample_values"

    count: int = 20
