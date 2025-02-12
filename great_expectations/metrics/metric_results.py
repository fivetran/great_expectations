from typing import Any, Literal, NamedTuple, Union

from great_expectations.compatibility.pydantic import BaseModel, validator

IDDictID = Union[str, tuple[()]]


class MetricConfigurationID(NamedTuple):
    metric_name: str
    metric_domain_kwargs_id: IDDictID
    metric_value_kwargs_id: IDDictID


class _MetricResult(BaseModel):
    id: MetricConfigurationID
    error: bool


class _SuccessfulMetricResult(_MetricResult):
    error: Literal[False] = False


class InvalidMetricError(TypeError):
    def __init__(self, expected_metric: str, actual_metric: str):
        super().__init__(
            f"Invalid metric: expected {expected_metric} but received {actual_metric}."
        )


class TableColumns(_SuccessfulMetricResult):
    @validator("id")
    def validate_id(cls, v):
        if v[0] != "table.columns":
            raise InvalidMetricError(expected_metric="table.columns", actual_metric=v[0])

    value: list[str]


class _ColumnType(BaseModel):
    name: str
    type: str


class TableColumnTypes(_SuccessfulMetricResult):
    @validator("id")
    def validate_id(cls, v):
        if v[0] != "table.column_types":
            raise InvalidMetricError(expected_metric="table.column_types", actual_metric=v[0])

    value: list[_ColumnType]


class UnexpectedCount(_SuccessfulMetricResult):
    @validator("id")
    def validate_id(cls, v):
        metric_name = v[0]
        if metric_name.split(".")[-1] != "unexpected_count":
            raise InvalidMetricError(expected_metric="unexpected_count", actual_metric=metric_name)

    value: int


class UnexpectedValues(_SuccessfulMetricResult):
    @validator("id")
    def validate_id(cls, v):
        metric_name = v[0]
        if metric_name.split(".")[-1] != "unexpected_values":
            raise InvalidMetricError(expected_metric="unexpected_values", actual_metric=metric_name)

    value: list[Any]  # unknowable type, since this is a sample of user data


class TableRowCount(_SuccessfulMetricResult):
    @validator("id")
    def validate_id(cls, v):
        if v[0] != "table.row_count":
            raise InvalidMetricError(expected_metric="table.row_count", actual_metric=v[0])

    value: int


class ErrorMetricResult(_MetricResult):
    value: dict[str, Union[int, dict, str]]
    error: Literal[True] = True


MetricResult = Union[
    TableColumns,
    TableColumnTypes,
    UnexpectedCount,
    UnexpectedValues,
    TableRowCount,
    ErrorMetricResult,
]
