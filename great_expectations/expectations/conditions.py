from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Iterable, List, Literal, Union

from great_expectations.compatibility.pydantic import BaseModel, Field, validator
from great_expectations.compatibility.typing_extensions import override

if TYPE_CHECKING:
    from typing_extensions import TypeAlias


class ConditionParserError(ValueError):
    """Raised when unable to determine the Condition type from a dict."""

    def __init__(self, value: Any):
        super().__init__(f"Unable to determine Condition type from dict: {value}")


class InvalidConditionTypeError(TypeError):
    """Raised when row_condition value has an invalid type."""

    def __init__(self, value: Any):
        super().__init__(f"Invalid condition type: {type(value)}")


class Operator(str, Enum):
    EQUAL = "=="
    NOT_EQUAL = "!="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    IN = "IN"
    NOT_IN = "NOT_IN"

    @override
    def __str__(self) -> str:
        return self.value


Parameter = Any


class Column(BaseModel):
    name: str

    @override
    def __hash__(self) -> int:
        return hash(self.name)

    @override
    def __eq__(self, other: Parameter) -> ComparisonCondition:  # type: ignore[override]
        return ComparisonCondition(column=self, operator=Operator.EQUAL, parameter=other)

    @override
    def __ne__(self, other: Parameter) -> ComparisonCondition:  # type: ignore[override]
        return ComparisonCondition(column=self, operator=Operator.NOT_EQUAL, parameter=other)

    def __lt__(self, other: Parameter) -> ComparisonCondition:
        return ComparisonCondition(column=self, operator=Operator.LESS_THAN, parameter=other)

    def __le__(self, other: Parameter) -> ComparisonCondition:
        return ComparisonCondition(
            column=self, operator=Operator.LESS_THAN_OR_EQUAL, parameter=other
        )

    def __gt__(self, other: Parameter) -> ComparisonCondition:
        return ComparisonCondition(column=self, operator=Operator.GREATER_THAN, parameter=other)

    def __ge__(self, other: Parameter) -> ComparisonCondition:
        return ComparisonCondition(
            column=self, operator=Operator.GREATER_THAN_OR_EQUAL, parameter=other
        )

    def is_in(self, values: Iterable) -> ComparisonCondition:
        return ComparisonCondition(column=self, operator=Operator.IN, parameter=list(values))

    def is_not_in(self, values: Iterable) -> ComparisonCondition:
        return ComparisonCondition(column=self, operator=Operator.NOT_IN, parameter=list(values))

    def is_null(self) -> NullityCondition:
        return NullityCondition(column=self, is_null=True)

    def is_not_null(self) -> NullityCondition:
        return NullityCondition(column=self, is_null=False)


class Condition(BaseModel):
    """Base class for conditions."""

    class Config:
        # This is needed so Pydantic can discriminate between subclasses when deserializing
        use_enum_values = True

    @override
    def dict(self, **kwargs) -> dict:
        """Override dict() to ensure the 'type' discriminator field is always included.

        This is necessary because Pydantic's exclude_defaults=True would otherwise
        exclude the type field, making deserialization impossible.
        """
        result = super().dict(**kwargs)
        # If 'type' field exists in the model and was excluded, add it back
        if hasattr(self, "type") and "type" not in result:
            result["type"] = self.type
        return result

    def __and__(self, other: Condition) -> AndCondition:
        new_conditions = []
        for cond in [self, other]:
            if isinstance(cond, AndCondition):
                new_conditions.extend(cond.conditions)
            else:
                new_conditions.append(cond)
        return AndCondition(conditions=new_conditions)

    def __or__(self, other: Condition) -> OrCondition:
        new_conditions = []
        for cond in [self, other]:
            if isinstance(cond, OrCondition):
                new_conditions.extend(cond.conditions)
            else:
                new_conditions.append(cond)
        return OrCondition(conditions=new_conditions)


class NullityCondition(Condition):
    type: Literal["nullity"] = Field(default="nullity")
    column: Column
    is_null: bool

    @override
    def __repr__(self):
        null_str = "NULL" if self.is_null else "NOT NULL"
        return f"{self.column.name} IS {null_str}"


class ComparisonCondition(Condition):
    type: Literal["comparison"] = Field(default="comparison")
    column: Column
    operator: Operator
    parameter: Parameter

    @override
    def __repr__(self):
        col_name = self.column.name
        if self.operator in (Operator.IN, Operator.NOT_IN):
            return f"{col_name} {self.operator} ({', '.join(map(str, self.parameter))})"
        return f"{col_name} {self.operator} {self.parameter}"


def deserialize_row_condition(value: Any) -> Union[str, Condition, None]:
    """Parse a row_condition value into the appropriate Condition type."""
    if value is None or isinstance(value, (str, Condition)):
        return value

    if isinstance(value, dict):
        # Use the 'type' field to discriminate which Condition subclass to use
        condition_type = value.get("type")

        if condition_type == "comparison":
            return ComparisonCondition.parse_obj(value)
        elif condition_type == "nullity":
            return NullityCondition.parse_obj(value)
        elif condition_type == "and":
            return AndCondition.parse_obj(value)
        elif condition_type == "or":
            return OrCondition.parse_obj(value)
        else:
            raise ConditionParserError(value)

    raise InvalidConditionTypeError(value)


class AndCondition(Condition):
    """Represents an AND condition composed of multiple conditions."""

    type: Literal["and"] = Field(default="and")
    conditions: List[Condition]

    @validator("conditions", pre=True, each_item=True)
    def _deserialize_condition(cls, v):
        """Deserialize each condition in the list."""
        if isinstance(v, dict):
            return deserialize_row_condition(v)
        return v

    @override
    def __repr__(self) -> str:
        return "(" + " AND ".join(repr(c) for c in self.conditions) + ")"


class OrCondition(Condition):
    """Represents an OR condition composed of multiple conditions."""

    type: Literal["or"] = Field(default="or")
    conditions: List[Condition]

    @validator("conditions", pre=True, each_item=True)
    def _deserialize_condition(cls, v):
        """Deserialize each condition in the list."""
        if isinstance(v, dict):
            return deserialize_row_condition(v)
        return v

    @override
    def __repr__(self) -> str:
        return "(" + " OR ".join(repr(c) for c in self.conditions) + ")"


RowConditionType: TypeAlias = Union[
    str, ComparisonCondition, NullityCondition, AndCondition, OrCondition, None
]
