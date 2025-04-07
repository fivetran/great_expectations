from pydantic import BaseModel
from great_expectations.metrics.batch.batch import BatchMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnType(BaseModel):
    name: str
    type: str


class BatchColumnTypesResult(MetricResult[ColumnType]): ...


class BatchColumnTypes(BatchMetric[BatchColumnTypesResult]):
    name = "table.column_types"
