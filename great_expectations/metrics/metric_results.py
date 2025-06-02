from typing import TYPE_CHECKING, Any, Generic, TypeVar, Union

import pandas as pd

from great_expectations.compatibility.pydantic import BaseModel, GenericModel
from great_expectations.validator.metric_configuration import (
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


class MetricErrorResultValue(BaseModel):
    exception_message: str
    exception_traceback: Union[str, None] = None


class MetricErrorResult(MetricResult[MetricErrorResultValue]): ...


class ConditionValuesValueError(ValueError):
    def __init__(self, actual_type: type) -> None:
        super().__init__(
            "Value must be one of: "
            "pandas.Series, pyspark.sql.Column, or sqlalchemy.BinaryExpression. "
            f"Got type `{actual_type}` instead."
        )


class ConditionValues(MetricResult[Union[pd.Series, "pyspark.sql.Column", "BinaryExpression"]]):
    @classmethod
    def validate_value_type(cls, value):
        if isinstance(value, pd.Series):
            return value

        try:
            from great_expectations.compatibility.pyspark import pyspark

            if isinstance(value, pyspark.sql.Column):
                return value
        except (ImportError, AttributeError):
            pass

        try:
            from great_expectations.compatibility.sqlalchemy import BinaryExpression

            if isinstance(value, BinaryExpression):
                return value
        except (ImportError, AttributeError):
            pass

        raise ConditionValuesValueError(type(value))

    @classmethod
    def __get_validators__(cls):
        yield cls.validate_value_type


class TableColumnsResult(MetricResult[list[str]]): ...


class ColumnType(BaseModel):
    class Config:
        extra = "allow"  # some backends return extra values

    name: str
    type: str


class TableColumnTypesResult(MetricResult[list[ColumnType]]): ...


class UnexpectedCountResult(MetricResult[int]): ...


class UnexpectedValuesResult(MetricResult[list[Any]]): ...
