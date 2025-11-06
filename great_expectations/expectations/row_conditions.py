from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Iterable, List, Literal, Union

from great_expectations._docs_decorators import public_api
from great_expectations.compatibility.pydantic import BaseModel, Field, root_validator, validator
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


class AndContainsOrError(ValueError):
    """Raised when an AND group contains OR conditions."""

    def __init__(self):
        super().__init__("AND groups cannot contain OR conditions")


class NestedOrError(ValueError):
    """Raised when OR groups contain nested OR conditions."""

    def __init__(self):
        super().__init__("OR groups cannot contain nested OR conditions")


class TooManyConditionsError(ValueError):
    """Raised when the number of conditions exceeds the maximum allowed."""

    def __init__(self, count: int, max_conditions: int):
        super().__init__(
            f"{max_conditions} conditions is the maximum, but {count} conditions are defined"
        )


class InvalidParameterTypeError(TypeError):
    """Raised when the type of the parameter is invalid."""

    def __init__(self, parameter: Any, suggestion: str | None = None):
        message = f"Invalid Parameter type: {type(parameter)}"
        if suggestion:
            message += f". {suggestion}"
        super().__init__(message)


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


@public_api
class Column(BaseModel):
    """
    Specify the column in a condition statement.
    """

    name: str

    def __init__(self, name: str):
        super().__init__(name=name)

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

    @public_api
    def is_in(self, values: Iterable) -> ComparisonCondition:
        """
        Operator for a condition statement that a column's value belongs to a set.
        """
        return ComparisonCondition(column=self, operator=Operator.IN, parameter=list(values))

    @public_api
    def is_not_in(self, values: Iterable) -> ComparisonCondition:
        """
        Operator for a condition statement that a column's value does not belong to a set.
        """
        return ComparisonCondition(column=self, operator=Operator.NOT_IN, parameter=list(values))

    @public_api
    def is_null(self) -> NullityCondition:
        """
        Operator for a condition statement that a column's value is null.
        """
        return NullityCondition(column=self, is_null=True)

    @public_api
    def is_not_null(self) -> NullityCondition:
        """
        Operator for a condition statement that a column's value is not null.
        """
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
        """Construct an AndCondition"""
        return AndCondition(conditions=[self, other])

    def __or__(self, other: Condition) -> OrCondition:
        """Construct an OrCondition"""
        return OrCondition(conditions=[self, other])


@public_api
class NullityCondition(Condition):
    """Condition representing the whether or not a column is null."""

    type: Literal["nullity"] = Field(default="nullity")
    column: Column
    is_null: bool

    @override
    def __repr__(self):
        null_str = "NULL" if self.is_null else "NOT NULL"
        return f"{self.column.name} IS {null_str}"


@public_api
class ComparisonCondition(Condition):
    """Condition representing the comparison of a column with a parameter."""

    type: Literal["comparison"] = Field(default="comparison")
    column: Column
    operator: Operator
    parameter: Parameter = Field(...)

    @root_validator
    def _validate_parameter_not_none(cls, values):
        parameter = values.get("parameter")
        operator = values.get("operator")
        if parameter is None:
            if operator == Operator.EQUAL:
                suggestion = "Did you mean to use Column.is_null()?"
            elif operator == Operator.NOT_EQUAL:
                suggestion = "Did you mean to use Column.is_not_null()?"
            else:
                suggestion = None
            raise InvalidParameterTypeError(parameter, suggestion)
        return values

    @root_validator
    def _validate_in_set_operator_parameter(cls, values):
        parameter = values.get("parameter")
        operator = values.get("operator")
        if operator in (Operator.IN, Operator.NOT_IN):
            cls._validate_parameter_is_iterable(parameter, operator)
            cls._validate_parameter_element_types(parameter, operator)
        return values

    @staticmethod
    def _validate_parameter_is_iterable(parameter: Parameter, operator: Operator) -> None:
        """Validate that parameter is an iterable (but not a string)."""
        if not isinstance(parameter, Iterable) or isinstance(parameter, str):
            raise InvalidParameterTypeError(
                parameter,
                f"For {operator} operator, parameter must be an iterable "
                "(list, tuple, set, etc.), but not a string",
            )

    @staticmethod
    def _validate_parameter_element_types(parameter: Iterable[Any], operator: Operator) -> None:
        """Validate that all elements in parameter are compatible types."""
        numeric_types = {int, float}
        allowed_types = numeric_types | {str}
        parameter_iter = iter(parameter)
        try:
            first_value = next(parameter_iter)
        except StopIteration:
            # Empty iterable is allowed
            return

        # Check that first item is one of the allowed types
        first_type = type(first_value)
        if first_type not in allowed_types:
            raise InvalidParameterTypeError(
                parameter,
                f"For {operator} operator, parameter values must contain only "
                f"these types: {', '.join(t.__name__ for t in allowed_types)}. "
                f"Found {first_type.__name__} at index 0",
            )
        first_is_numeric = first_type in numeric_types
        for i, value in enumerate(parameter_iter, start=1):
            # Check that all subsequent items match the type category of the first item
            # Allow mixing numeric types
            value_type = type(value)
            if first_is_numeric:
                is_valid = value_type in numeric_types
            else:
                is_valid = value_type == first_type
            if not is_valid:
                raise InvalidParameterTypeError(
                    parameter,
                    f"For {operator} operator, all items in parameter "
                    "must be of the same type. "
                    f"First item is {first_type.__name__}, but found "
                    f"{value_type.__name__} at index {i}",
                )

    @override
    def __repr__(self):
        col_name = self.column.name
        if self.operator in (Operator.IN, Operator.NOT_IN):
            return f"{col_name} {self.operator} ({', '.join(map(str, self.parameter))})"
        return f"{col_name} {self.operator} {self.parameter}"


class PassThroughCondition(Condition):
    """Condition that passes a filter string directly to the execution engine.

    This is used for legacy pandas/spark condition_parser syntax where the
    row_condition string is passed directly to DataFrame.query() or DataFrame.filter().
    """

    type: Literal["pass_through"] = Field(default="pass_through")
    pass_through_filter: str

    @override
    def __repr__(self):
        return f"PassThrough({self.pass_through_filter!r})"


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
        elif condition_type == "pass_through":
            return PassThroughCondition.parse_obj(value)
        else:
            raise ConditionParserError(value)

    raise InvalidConditionTypeError(value)


@public_api
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


@public_api
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
    str,
    ComparisonCondition,
    NullityCondition,
    AndCondition,
    OrCondition,
    PassThroughCondition,
    None,
]


# Maximum number of conditions allowed in a row_condition
MAX_CONDITIONS = 100


def _count_total_conditions(conditions: List[Condition]) -> int:
    """Recursively count all conditions including nested ones."""
    count = 0
    for condition in conditions:
        if isinstance(condition, (AndCondition, OrCondition)):
            count += _count_total_conditions(condition.conditions)
        else:
            count += 1
    return count


def _flatten_and_conditions(conditions: List[Condition]) -> List[Condition]:
    """Flatten nested AndConditions within a list of conditions."""
    flattened = []
    for condition in conditions:
        if isinstance(condition, AndCondition):
            # Recursively flatten nested AndConditions
            flattened.extend(_flatten_and_conditions(condition.conditions))
        else:
            flattened.append(condition)
    return flattened


def _contains_or_in_and(condition: Condition) -> bool:
    """Check if an AndCondition contains any OrConditions."""
    if isinstance(condition, AndCondition):
        for cond in condition.conditions:
            if isinstance(cond, OrCondition):
                return True
            # Recursively check nested AndConditions
            if isinstance(cond, AndCondition) and _contains_or_in_and(cond):
                return True
    return False


def _contains_nested_or(condition: Condition) -> bool:
    """Check if an OrCondition contains nested OrConditions."""
    if isinstance(condition, OrCondition):
        for cond in condition.conditions:
            if isinstance(cond, OrCondition):
                return True
            # Also check if any nested AndConditions contain OrConditions
            # (which would create a nested OR structure)
            if isinstance(cond, AndCondition):
                for and_cond in cond.conditions:
                    if isinstance(and_cond, OrCondition):
                        # This is an OR within an AND within an OR, which creates nested ORs
                        return True
    return False


def _validate_and_condition(row_condition: AndCondition) -> AndCondition:
    """Validate AndCondition constraints."""
    # Check for OrConditions within AndConditions
    if _contains_or_in_and(row_condition):
        raise AndContainsOrError()

    # Flatten nested AndConditions
    # We only flatten nested AndConditions because
    # logical ANDs are associative, while logical ORs are non-associative.
    flattened_conditions = _flatten_and_conditions(row_condition.conditions)

    # Return flattened AndCondition
    return AndCondition(conditions=flattened_conditions)


def _validate_or_condition(row_condition: OrCondition) -> OrCondition:
    """Validate OrCondition constraints."""
    # Check for nested OrConditions
    if _contains_nested_or(row_condition):
        raise NestedOrError()

    return row_condition


def validate_row_condition(row_condition: RowConditionType) -> RowConditionType:
    """Validate row_condition according to GX Cloud UI constraints.

    1. Flatten nested AndConditions within AndConditions
    2. Raise error if OrConditions are nested within AndConditions
    3. Raise error if OrConditions are nested within OrConditions
    4. Raise error if total conditions exceed MAX_CONDITIONS

    Args:
        row_condition: The row condition to validate

    Returns:
        The validated (and possibly flattened) row condition

    Raises:
        ValueError: If the row condition violates any constraints
    """
    # String conditions and None are always valid
    if row_condition is None or isinstance(row_condition, str):
        return row_condition

    # Single condition types are always valid
    if isinstance(row_condition, (ComparisonCondition, NullityCondition, PassThroughCondition)):
        return row_condition

    # Validate total condition count
    total_count = _count_total_conditions(row_condition.conditions)
    if total_count > MAX_CONDITIONS:
        raise TooManyConditionsError(total_count, MAX_CONDITIONS)

    # Validate AndCondition
    if isinstance(row_condition, AndCondition):
        return _validate_and_condition(row_condition)

    # Validate OrCondition
    if isinstance(row_condition, OrCondition):
        return _validate_or_condition(row_condition)

    raise InvalidConditionTypeError(row_condition)
