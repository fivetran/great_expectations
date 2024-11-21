from enum import Enum
from typing import Sequence


class ObservedValueRenderState(str, Enum):
    expected = "expected"
    unexpected = "expected"
    missing = "missing"


def get_list_comparison_obs_val(
    expected: list[str], actual: list[str]
) -> Sequence[tuple[str, ObservedValueRenderState]]:
    """ """
    result: list[tuple[str, ObservedValueRenderState]] = []
    actual_set = set(actual)

    i = 0  # iterator for expected
    j = 0  # iterator for actual
    while i < len(expected) and j < len(actual):
        if expected[i] != actual[j] and expected[i] not in actual_set:
            result.append((expected[i], ObservedValueRenderState.missing))
            i += 1
            continue

        if expected[i] == actual[j]:
            result.append((actual[j], ObservedValueRenderState.expected))
        else:
            result.append((actual[j], ObservedValueRenderState.unexpected))
        i += 1
        j += 1

    while i < len(expected):
        if expected[i] not in actual_set:
            result.append((expected[i], ObservedValueRenderState.missing))
        i += 1

    while j < len(actual):
        result.append((actual[j], ObservedValueRenderState.unexpected))
        j += 1

    return result
