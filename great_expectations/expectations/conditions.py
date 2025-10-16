from __future__ import annotations

from enum import Enum
from typing import Any, Iterable, List

from great_expectations.compatibility.pydantic import BaseModel
from great_expectations.compatibility.typing_extensions import override


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

    def __and__(self, other: Condition) -> Condition:
        new_conditions = []
        for cond in [self, other]:
            if isinstance(cond, AndCondition):
                new_conditions.extend(cond.conditions)
            else:
                new_conditions.append(cond)
        return AndCondition(conditions=new_conditions)

    def __or__(self, other: Condition) -> Condition:
        new_conditions = []
        for cond in [self, other]:
            if isinstance(cond, OrCondition):
                new_conditions.extend(cond.conditions)
            else:
                new_conditions.append(cond)
        return OrCondition(conditions=new_conditions)


class NullityCondition(Condition):
    column: Column
    is_null: bool

    @override
    def __repr__(self):
        null_str = "NULL" if self.is_null else "NOT NULL"
        return f"{self.column.name} IS {null_str}"


class ComparisonCondition(Condition):
    column: Column
    operator: Operator
    parameter: Parameter

    @override
    def __repr__(self):
        col_name = self.column.name
        if self.operator in (Operator.IN, Operator.NOT_IN):
            return f"{col_name} {self.operator} ({', '.join(map(str, self.parameter))})"
        return f"{col_name} {self.operator} {self.parameter}"


class AndCondition(Condition):
    """Represents an AND condition composed of multiple conditions."""

    conditions: List[Condition]

    @override
    def __repr__(self) -> str:
        return "(" + " AND ".join(repr(c) for c in self.conditions) + ")"


class OrCondition(Condition):
    """Represents an OR condition composed of multiple conditions."""

    conditions: List[Condition]

    @override
    def __repr__(self) -> str:
        return "(" + " OR ".join(repr(c) for c in self.conditions) + ")"
