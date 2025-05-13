from typing import Any

from great_expectations.compatibility.pydantic import BaseModel
from great_expectations.metrics.batch.batch import BatchMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnType(BaseModel):
    name: str
    type: Any


class BatchColumnTypesResult(MetricResult[list[ColumnType]]): ...


class BatchColumnTypes(BatchMetric[BatchColumnTypesResult]):
    """Table schema"""

    name = "table.column_types"
