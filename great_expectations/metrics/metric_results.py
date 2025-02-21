from typing import Any, Generic, TypedDict, TypeVar

from great_expectations.compatibility.pydantic import BaseModel, GenericModel
from great_expectations.validator.exception_info import ExceptionInfo
from great_expectations.validator.metric_configuration import (
    MetricConfiguration,
    MetricConfigurationID,
)

_MetricResultValue = TypeVar("_MetricResultValue")


class MetricResult(GenericModel, Generic[_MetricResultValue]):
    id: MetricConfigurationID
    value: _MetricResultValue

    class Config:
        arbitrary_types_allowed = True


class MetricErrorResultValue(TypedDict):
    metric_configuration: MetricConfiguration
    exception_info: ExceptionInfo
    num_failures: int


class MetricErrorResult(MetricResult[MetricErrorResultValue]): ...


class TableColumnsResult(MetricResult[list[str]]): ...


class ColumnType(BaseModel):
    class Config:
        extra = "allow"  # some backends return extra values

    name: str
    type: str


class TableColumnTypesResult(MetricResult[list[ColumnType]]): ...


class UnexpectedCountResult(MetricResult[int]): ...


class UnexpectedValuesResult(MetricResult[list[Any]]): ...
