from __future__ import annotations

"""This module contains shared TypeAliases"""

import pathlib
from typing import TYPE_CHECKING, Dict, List, Union

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    from great_expectations.expectations.conditions import Condition

PathStr: TypeAlias = Union[str, pathlib.Path]
JSONValues: TypeAlias = Union[
    Dict[str, "JSONValues"], List["JSONValues"], str, int, float, bool, None
]
RowConditionType: TypeAlias = Union[str, "Condition", None]
