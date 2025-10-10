from __future__ import annotations

from typing import List

from great_expectations.compatibility.pydantic import BaseModel, validator
from great_expectations.compatibility.typing_extensions import override

# Error messages for condition validation
_NESTED_OR_IN_AND_ERROR = "AND groups cannot contain nested OR conditions"
_NESTED_AND_ERROR = "AND groups cannot contain nested AND conditions"
_NESTED_OR_ERROR = "OR groups cannot contain nested OR conditions"


class ConditionError(TypeError):
    """Exception for condition validation errors."""

    pass


class Condition(BaseModel):
    """Base class for conditions."""

    pass


class AndCondition(Condition):
    """Represents an AND condition composed of multiple conditions."""

    conditions: List[Condition]

    @validator("conditions")
    def validate_no_nested_or_or_nested_and(cls, conditions: List[Condition]) -> List[Condition]:
        for cond in conditions:
            if isinstance(cond, OrCondition):
                raise ConditionError(_NESTED_OR_IN_AND_ERROR)
            if isinstance(cond, AndCondition):
                raise ConditionError(_NESTED_AND_ERROR)
        return conditions

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
                raise ConditionError(_NESTED_OR_ERROR)
        return conditions

    @override
    def __repr__(self) -> str:
        return "(" + " OR ".join(repr(c) for c in self.conditions) + ")"
