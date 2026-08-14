from __future__ import annotations

import functools
import os
import warnings
from pathlib import Path
from typing import Any

import pytest

from great_expectations.datasource.fluent.batch_parameter_normalization import (
    BATCH_PARAMETER_DEPRECATION_MESSAGE_PREFIX,
    batch_parameter_values_match,
    is_digit_string,
    normalize_batch_parameters,
    numeric_parameter_names_of,
)
from great_expectations.warnings import GxDeprecationWarning


@pytest.mark.unit
@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param(None, False, id="none"),
        pytest.param(0, False, id="int-zero"),
        pytest.param(False, False, id="bool-false"),
        pytest.param(True, False, id="bool-true"),
        pytest.param(-1, False, id="int-negative"),
        pytest.param(4.0, False, id="float"),
        pytest.param("04", True, id="zero-padded-digit-string"),
        pytest.param("4", True, id="digit-string"),
        pytest.param("202O", False, id="letter-o-not-digit"),
        pytest.param(" 04", False, id="leading-whitespace"),
        pytest.param("+4", False, id="signed-string"),
        pytest.param("²", False, id="unicode-superscript-two"),
        pytest.param("٤", False, id="unicode-arabic-indic-digit"),
    ],
)
def test_is_digit_string(value: Any, expected: bool) -> None:
    assert is_digit_string(value) is expected


@pytest.mark.unit
def test_normalize_batch_parameters_identity_pass_through_all_int() -> None:
    """Options already satisfying the numeric contract must not be replaced or warned on."""
    options = {"year": 2020, "month": 4}
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = normalize_batch_parameters(options, {"year", "month"})

    assert result is options


@pytest.mark.unit
def test_normalize_batch_parameters_none_options_is_identity() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = normalize_batch_parameters(None, {"year", "month"})

    assert result is None


@pytest.mark.unit
def test_normalize_batch_parameters_empty_numeric_names_is_identity() -> None:
    options = {"year": "2020"}
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = normalize_batch_parameters(options, set())

    assert result is options


@pytest.mark.unit
def test_normalize_batch_parameters_non_numeric_key_untouched() -> None:
    """A digit-string under a key outside numeric_parameter_names is exempt entirely."""
    options = {"path": "04"}
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = normalize_batch_parameters(options, {"year"})

    assert result is options


@pytest.mark.unit
def test_normalize_batch_parameters_coerces_and_returns_new_dict() -> None:
    original = {"year": "2020", "month": 4}
    with pytest.warns(GxDeprecationWarning):
        result = normalize_batch_parameters(original, {"year", "month"})

    assert result == {"year": 2020, "month": 4}
    assert result is not original
    assert original == {"year": "2020", "month": 4}, "input must never be mutated"


@pytest.mark.unit
def test_normalize_batch_parameters_emits_exactly_one_warning() -> None:
    original = {"year": "2020", "month": "04"}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        normalize_batch_parameters(original, {"year", "month"})

    assert len(caught) == 1


@pytest.mark.unit
def test_normalize_batch_parameters_message_prefix_and_target_stable() -> None:
    original = {"year": "2020"}
    with pytest.warns(GxDeprecationWarning) as record:
        normalize_batch_parameters(original, {"year"})

    message = str(record[0].message)
    assert BATCH_PARAMETER_DEPRECATION_MESSAGE_PREFIX == (
        "String values for numeric batch parameters are deprecated"
    )
    assert message.startswith(BATCH_PARAMETER_DEPRECATION_MESSAGE_PREFIX)
    assert "integer" in message.lower()
    assert "2.0" in message


@pytest.mark.unit
def test_normalize_batch_parameters_message_names_keys_sorted_values_omitted() -> None:
    original = {"month": "04", "year": "2020"}
    with pytest.warns(GxDeprecationWarning) as record:
        normalize_batch_parameters(original, {"year", "month"})

    message = str(record[0].message)
    month_index = message.index("month")
    year_index = message.index("year")
    assert month_index < year_index, "coerced key names must be listed sorted"
    assert "2020" not in message, "values must not appear in the message"
    assert "04" not in message, "values must not appear in the message"


@pytest.mark.unit
def test_normalize_batch_parameters_never_raises_on_non_coercible_string() -> None:
    """A non-digit string under a numeric name is left as-is; the caller reports later."""
    original = {"year": "202O"}
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = normalize_batch_parameters(original, {"year"})

    assert result == {"year": "202O"}


@pytest.mark.unit
def test_normalize_batch_parameters_attribution_points_at_caller_module() -> None:
    """The warning must be attributed to user code, not a location inside the library."""
    original = {"year": "2020"}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        normalize_batch_parameters(original, {"year"})

    assert len(caught) == 1
    assert os.path.realpath(caught[0].filename) == os.path.realpath(__file__)


@pytest.mark.unit
def test_normalize_batch_parameters_attribution_skips_stdlib_frame() -> None:
    """A stdlib frame sitting between the last library frame and user code (e.g.
    functools.cached_property on a checkpoint's property chain) must not be
    mistaken for the user's location, and must not poison that stdlib module's own
    warning registry. Simulated by spoofing a GX-package call site's filename via a
    replaced code object, then reaching it through a real functools.cached_property
    __get__ frame -- reproducing "GX method -> functools.py -> user code" exactly.
    """
    import great_expectations as gx

    gx_package_dir = Path(gx.__file__).resolve().parent
    spoofed_filename = str(gx_package_dir / "_fake_module_for_test.py")

    def _gx_authored_method(_self: Any) -> Any:
        return normalize_batch_parameters({"year": "2020"}, {"year"})

    spoofed_code = _gx_authored_method.__code__.replace(co_filename=spoofed_filename)
    _gx_authored_method.__code__ = spoofed_code
    assert os.path.realpath(spoofed_code.co_filename).startswith(
        os.path.realpath(gx_package_dir)
    ), "setup check: the spoofed frame must resolve inside the GX package"

    class _HasCachedProperty:
        options = functools.cached_property(_gx_authored_method)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _ = _HasCachedProperty().options

    assert len(caught) == 1
    assert os.path.realpath(caught[0].filename) == os.path.realpath(__file__)
    assert os.path.realpath(functools.__file__) != os.path.realpath(caught[0].filename)
    assert os.path.realpath(spoofed_filename) != os.path.realpath(caught[0].filename)


@pytest.mark.unit
def test_normalize_batch_parameters_bool_value_is_not_coerced() -> None:
    """Bools are not digit-strings and must never be coerced or warned on."""
    original = {"year": True}
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = normalize_batch_parameters(original, {"year"})

    assert result is original


@pytest.mark.unit
@pytest.mark.parametrize(
    "requested,candidate,expected",
    [
        pytest.param(2020, 2020, True, id="int-int-equal"),
        pytest.param("2020", "2020", True, id="str-str-equal-fast-path"),
        pytest.param(4, "04", True, id="int-vs-zero-padded-digit-string"),
        pytest.param("04", 4, True, id="digit-string-vs-int-reversed"),
        pytest.param(True, 1, False, id="bool-excluded-from-int-side"),
        pytest.param(1, True, False, id="bool-excluded-reversed"),
        pytest.param("01", 1, True, id="zero-padded-digit-string-vs-int-equivalent"),
        pytest.param("01", "1", False, id="string-string-stays-exact-no-numeric-coercion"),
        pytest.param(4, "202O", False, id="non-digit-string-never-matches-int"),
        pytest.param(None, None, True, id="none-none-equal"),
        pytest.param(None, 4, False, id="none-vs-int-no-match"),
        pytest.param("path/a", "path/a", True, id="path-string-equal-fast-path"),
    ],
)
def test_batch_parameter_values_match(requested: Any, candidate: Any, expected: bool) -> None:
    assert batch_parameter_values_match(requested, candidate) is expected


@pytest.mark.unit
def test_numeric_parameter_names_of_returns_declared_names() -> None:
    class _FakePartitioner:
        numeric_param_names = ["year", "month"]

    assert numeric_parameter_names_of(_FakePartitioner()) == frozenset({"year", "month"})


@pytest.mark.unit
def test_numeric_parameter_names_of_fail_closed_for_unknown_kind() -> None:
    """A partitioner declaring nothing (or of an unrecognized kind) is exempt, not coerced."""

    class _NoDeclaration:
        pass

    assert numeric_parameter_names_of(_NoDeclaration()) == frozenset()


@pytest.mark.unit
def test_numeric_parameter_names_of_none_partitioner_is_exempt() -> None:
    assert numeric_parameter_names_of(None) == frozenset()


@pytest.mark.unit
def test_numeric_parameter_names_of_fail_closed_when_declaration_raises() -> None:
    """A declaration that raises while being read is exempt, not propagated."""

    class _RaisingDeclaration:
        @property
        def numeric_param_names(self) -> list[str]:
            raise RuntimeError("boom")

    assert numeric_parameter_names_of(_RaisingDeclaration()) == frozenset()


@pytest.mark.unit
def test_numeric_parameter_names_of_fail_closed_for_non_iterable_declaration() -> None:
    """A declaration that isn't a usable collection of names is exempt, not a crash."""

    class _NonIterableDeclaration:
        numeric_param_names = 5

    assert numeric_parameter_names_of(_NonIterableDeclaration()) == frozenset()


@pytest.mark.unit
def test_numeric_parameter_names_of_fail_closed_for_bare_string_declaration() -> None:
    """A bare string declaration is exempt rather than silently exploded per-character."""

    class _StringDeclaration:
        numeric_param_names = "year"

    assert numeric_parameter_names_of(_StringDeclaration()) == frozenset()
