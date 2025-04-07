from typing import Any

from great_expectations.compatibility.pydantic import BaseModel, validator
from great_expectations.metrics.batch.batch import BatchMetric
from great_expectations.metrics.metric_results import MetricResult


class ColumnType(BaseModel):
    name: str
    type: Any

    @validator("type", pre=True)
    def convert_type(cls, v):
        if isinstance(v, dict):
            return v.get("type", v)
        return v


class BatchColumnTypesResult(MetricResult[list[ColumnType]]): ...


class BatchColumnTypes(BatchMetric[BatchColumnTypesResult]):
    name = "table.column_types"
