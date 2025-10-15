from __future__ import annotations

from typing import List

from great_expectations.compatibility.pydantic import BaseModel
from great_expectations.compatibility.typing_extensions import override


class Condition(BaseModel):
    """Base class for conditions."""

    pass


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
