from __future__ import annotations

from typing import List

from great_expectations.compatibility.pydantic import BaseModel, validator
from great_expectations.compatibility.typing_extensions import override

# Error messages for condition validation
_NESTED_OR_IN_AND_ERROR = "AND groups cannot contain OR conditions"
_NESTED_OR_ERROR = "OR groups cannot contain nested OR conditions"


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


class AndCondition(Condition):
    """Represents an AND condition composed of multiple conditions."""

    conditions: List[Condition]

    @validator("conditions")
    def validate_and_flatten(cls, conditions: List[Condition]) -> List[Condition]:
        flattened = []
        for cond in conditions:
            if isinstance(cond, OrCondition):
                raise TypeError(_NESTED_OR_IN_AND_ERROR)
            elif isinstance(cond, AndCondition):
                # Flatten nested AND conditions
                flattened.extend(cond.conditions)
            else:
                flattened.append(cond)
        return flattened

    @override
    def __repr__(self) -> str:
        return "(" + " AND ".join(repr(c) for c in self.conditions) + ")"


class OrCondition(Condition):
    """Represents an OR condition composed of multiple conditions."""

    conditions: List[Condition]

    @validator("conditions")
    def validate_no_nested_or(cls, conditions: List[Condition]) -> List[Condition]:
        for cond in conditions:
            if isinstance(cond, OrCondition):
                raise TypeError(_NESTED_OR_ERROR)
        return conditions

    @override
    def __repr__(self) -> str:
        return "(" + " OR ".join(repr(c) for c in self.conditions) + ")"
