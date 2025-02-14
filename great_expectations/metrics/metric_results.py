from typing import Any, Generic, TypeVar, Union

from great_expectations.compatibility.pydantic import BaseModel, GenericModel
from great_expectations.validator.metric_configuration import MetricConfigurationID

_MetricResultValue = TypeVar("_MetricResultValue")


class MetricResult(GenericModel, Generic[_MetricResultValue]):
    id: MetricConfigurationID
    value: _MetricResultValue


class MetricErrorResult(MetricResult[dict[str, Union[int, dict, str]]]): ...


class TableColumnsResult(MetricResult[list[str]]): ...


class ColumnType(BaseModel):
    class Config:
        extra = "allow"  # some backends return extra values

    name: str
    type: str


class TableColumnTypesResult(MetricResult[list[ColumnType]]): ...


class UnexpectedCountResult(MetricResult[int]): ...


class UnexpectedValuesResult(MetricResult[list[Any]]): ...


class TableRowCountResult(MetricResult[int]): ...
