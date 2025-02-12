from typing import Literal, NamedTuple, Union

from great_expectations.compatibility.pydantic import BaseModel

IDDictID = Union[str, tuple[()]]


class MetricConfigurationID(NamedTuple):
    metric_name: str
    metric_domain_kwargs_id: IDDictID
    metric_value_kwargs_id: IDDictID


class _MetricResult(BaseModel):
    name: str
    error: bool


class _SuccessfulMetricResult(_MetricResult):
    error: Literal[False] = False


# base types


class _IntegerMetricResult(_SuccessfulMetricResult):
    value: int


class _FloatMetricResult(_SuccessfulMetricResult):
    value: float


class _StringMetricResult(_SuccessfulMetricResult):
    value: str


class _BooleanMetricResult(_SuccessfulMetricResult):
    value: bool


class _StringListMetricResult(_SuccessfulMetricResult):
    value: list[str]


# metric implementations

class TableColumns(_StringListMetricResult):
    name: Literal["table.columns"] = "table.columns"


class _ColumnType(BaseModel):
    name: str
    type: str


class TableColumnTypes(_SuccessfulMetricResult):
    name: Literal["table.columns"] = "table.column_types"
    value: list[_ColumnType]


class ColumnValuesNullUnexpectedCount(_IntegerMetricResult):
    name: Literal["column_values.null.unexpected_count"] = "column_values.null.unexpected_count"


class ColumnValuesNonnullUnexpectedCount(_IntegerMetricResult):
    name: Literal["column_values.nonnull.unexpected_count"] = "column_values.nonnull.unexpected_count"


class ColumnValuesValueLengthBetweenUnexpectedCount(_IntegerMetricResult):
    name: Literal["column_values.value_length.between.unexpected_count"] = "column_values.value_length.between.unexpected_count""


class TableRowCount(_IntegerMetricResult):
    name: Literal["table.row_count"] = "table.row_count"


class ColumnValuesInSetUnexpectedCount(_IntegerMetricResult):
    name: Literal["column_values.in_set.unexpected_count"] = "column_values.in_set.unexpected_count"


class ErrorMetricResult(_MetricResult):
    value: dict[str, Union[int, dict, str]]
    error: Literal[True] = True


MetricResult = Union[
    TableColumns,
    TableColumnTypes,
    ColumnValuesNullUnexpectedCount,
ColumnValuesNonnullUnexpectedCount,
ColumnValuesValueLengthBetweenUnexpectedCount,
    ErrorMetricResult,
]
