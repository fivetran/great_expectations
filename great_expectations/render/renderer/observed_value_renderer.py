from enum import Enum


class ObservedValueRenderState(str, Enum):
    EXPECTED = "expected"
    UNEXPECTED = "unexpected"
    MISSING = "missing"
