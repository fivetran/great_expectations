from typing import TYPE_CHECKING, Any, Generic, TypedDict, TypeVar, Union

import pandas as pd

from great_expectations.compatibility.pydantic import BaseModel, GenericModel
from great_expectations.validator.exception_info import ExceptionInfo
from great_expectations.validator.metric_configuration import (
    MetricConfiguration,
    MetricConfigurationID,
)

if TYPE_CHECKING:
    from great_expectations.compatibility.pyspark import pyspark
    from great_expectations.compatibility.sqlalchemy import BinaryExpression

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


PYSPARK_SQL_COLUMN: bool


try:
    from great_expectations.compatibility.pyspark import pyspark

    PYSPARK_SQL_COLUMN = True
except ModuleNotFoundError:
    PYSPARK_SQL_COLUMN = False


SA_BINARY_EXPRESSION: bool


try:
    from great_expectations.compatibility.sqlalchemy import BinaryExpression

    SA_BINARY_EXPRESSION = True
except ModuleNotFoundError:
    SA_BINARY_EXPRESSION = False


if PYSPARK_SQL_COLUMN and SA_BINARY_EXPRESSION:
    ConditionValues = Union[pd.Series, pyspark.sql.Column, BinaryExpression]
elif PYSPARK_SQL_COLUMN:
    ConditionValues = Union[pd.Series, pyspark.sql.Column]  # type: ignore[misc]  # can't find type to satisfy "<typing special form>"
elif SA_BINARY_EXPRESSION:
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
