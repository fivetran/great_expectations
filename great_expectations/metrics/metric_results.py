from typing import Any, Generic, TypedDict, TypeVar, Union

import pandas as pd

from great_expectations.compatibility.pydantic import BaseModel, GenericModel
from great_expectations.compatibility.pyspark import pyspark
from great_expectations.compatibility.sqlalchemy import BinaryExpression, sqlalchemy
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


if pyspark and sqlalchemy:
    ConditionValues = Union[pd.Series, pyspark.sql.Column, BinaryExpression]
elif pyspark:
    ConditionValues = Union[pd.Series, pyspark.sql.Column]  # type: ignore[misc]  # can't find type to satisfy "<typing special form>"
elif sqlalchemy:
    ConditionValues = Union[pd.Series, BinaryExpression]  # type: ignore[misc]  # can't find type to satisfy "<typing special form>"
else:
    ConditionValues = pd.Series  # type: ignore[misc]  # can't find type to satisfy "<typing special form>"


class TableColumnsResult(MetricResult[list[str]]): ...


class ColumnType(BaseModel):
    class Config:
        extra = "allow"  # some backends return extra values

    name: str
    type: str


class TableColumnTypesResult(MetricResult[list[ColumnType]]): ...


class UnexpectedCountResult(MetricResult[int]): ...


class UnexpectedValuesResult(MetricResult[list[Any]]): ...
