from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from great_expectations.render.renderer_configuration import _RendererValueBase


class ObservedValueRenderState(str, Enum):
    EXPECTED = "expected"
    UNEXPECTED = "unexpected"
    MISSING = "missing"


@dataclass(frozen=True)
class TemplateStrVariable:
    name: str
    value: str


def _prepare_params_for_list_comparison(
    params: "_RendererValueBase",
    expected_prefix: str,
    observed_prefix: str,
) -> str:
    """
    This function mutates the `params` argument to set the render_state of each variable entry.
    Return:
        A template string that satisfies the `com.superconductive.rendered.string` schema.
    """
    expected: list[TemplateStrVariable] = [
        TemplateStrVariable(name=name, value=value.value)
        for name, value in params
        if name.startswith(expected_prefix)
    ]
    actual: list[TemplateStrVariable] = [
        TemplateStrVariable(name=name, value=value.value)
        for name, value in params
        if name.startswith(observed_prefix)
    ]
    result: list[str] = []
    actual_set = {x.value for x in actual}

    def submit(item: TemplateStrVariable, state: ObservedValueRenderState) -> None:
        params.__dict__[item.name].render_state = state.value
        result.append("$" + item.name)

    i = 0  # iterator for expected
    j = 0  # iterator for actual
    while i < len(expected) and j < len(actual):
        if expected[i].value != actual[j].value and expected[i].value not in actual_set:
            submit(expected[i], ObservedValueRenderState.MISSING)
            i += 1
            continue

        if expected[i].value == actual[j].value:
            submit(actual[j], ObservedValueRenderState.EXPECTED)
        else:
            submit(actual[j], ObservedValueRenderState.UNEXPECTED)
        i += 1
        j += 1

    while i < len(expected):
        if expected[i].value not in actual_set:
            submit(expected[i], ObservedValueRenderState.MISSING)
        i += 1

    while j < len(actual):
        submit(actual[j], ObservedValueRenderState.UNEXPECTED)
        j += 1

    return " ".join(result)
