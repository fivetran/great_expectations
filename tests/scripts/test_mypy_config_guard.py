"""Tests for the mypy configuration relaxation guard.

Pins three things about ``scripts/mypy_config_guard.py``: which configuration edits count as
a regression versus which count as inventory drift, that a classifier which does not
recognize a setting treats it as relaxing rather than passing it through unchecked, and that
the guard's own failure message teaches a contributor what to do without ever naming the
inventory file or a flag that would let the failure be silenced instead of addressed.

Every failure-detection test below asserts both which bucket a finding lands in (regression
vs. drift, or ok vs. not) and the specific text naming the offending entry, so that a
comparator rewritten to return a fixed verdict cannot pass this suite.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from scripts.mypy_config_guard import (
    _REGRESSION_ALTERNATIVES,
    ComparisonResult,
    GuardConfigError,
    RelaxationSurface,
    _format_drift_message,
    _format_regression_message,
    _print_result,
    compare,
    extract_surface,
    load_inventory,
    main,
    relaxing_settings,
)

if sys.version_info >= (3, 11):
    import tomllib
else:  # Python 3.10 and earlier
    import tomli as tomllib

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

pytestmark = pytest.mark.unit


# --- test helpers -----------------------------------------------------------------------


def _surface_from_toml(config_toml: str) -> RelaxationSurface:
    """Parse an inline TOML ``[tool.mypy]`` document into a RelaxationSurface."""
    return extract_surface(tomllib.loads(config_toml))


def _inventory_surface(
    *,
    exclude: Sequence[str] = ("legacy_module/",),
    files: Sequence[str] = ("great_expectations", "docs", "tests"),
    enable_error_code: Sequence[str] = ("ignore-without-code",),
    disable_error_code: Sequence[str] = (),
    follow_imports: str = "normal",
    overrides: Sequence[Mapping[str, str]] = (),
) -> RelaxationSurface:
    """Build an accepted-inventory RelaxationSurface with sensible, overridable defaults."""
    return load_inventory(
        {
            "exclude": list(exclude),
            "files": list(files),
            "enable_error_code": list(enable_error_code),
            "disable_error_code": list(disable_error_code),
            "follow_imports": follow_imports,
            "overrides": [dict(entry) for entry in overrides],
        }
    )


def _assert_single_regression(result: ComparisonResult, expected_substring: str) -> None:
    """Assert exactly one finding, that it is a regression (not drift), naming the entry."""
    assert not result.ok
    assert result.inventory_drift == ()
    assert len(result.regressions) == 1, result.regressions
    assert expected_substring in result.regressions[0]


def _assert_single_drift(result: ComparisonResult, expected_substring: str) -> None:
    """Assert exactly one finding, that it is drift (not a regression), naming the entry."""
    assert not result.ok
    assert result.regressions == ()
    assert len(result.inventory_drift) == 1, result.inventory_drift
    assert expected_substring in result.inventory_drift[0]


def _assert_setting_is_relaxing(setting: str, value: object) -> None:
    """A per-module override carrying (setting, value) alone is classified as relaxing."""
    result = relaxing_settings({"module": "compat.example_pkg.*", setting: value})
    assert setting in result
    assert result[setting] == value


def _assert_setting_is_not_relaxing(setting: str, value: object) -> None:
    """A per-module override carrying (setting, value) alone is not classified as relaxing."""
    result = relaxing_settings({"module": "compat.example_pkg.*", setting: value})
    assert result == {}


# --- baseline: a configuration matching its inventory passes -----------------------------


def test_configuration_matching_the_inventory_passes() -> None:
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/"]

        [[tool.mypy.overrides]]
        module = "compat.missing_pkg.*"
        ignore_missing_imports = true
        """
    )
    inventory = _inventory_surface(
        overrides=(
            {
                "module": "compat.missing_pkg.*",
                "setting": "ignore_missing_imports",
                "value": json.dumps(True),
            },
        )
    )
    result = compare(config, inventory)
    assert result.ok
    assert result.regressions == ()
    assert result.inventory_drift == ()


# --- regressions: a relaxation the inventory has not accepted -----------------------------


def test_new_exclude_pattern_not_in_inventory_is_a_regression() -> None:
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/", "freshly_added_pattern/"]
        """
    )
    result = compare(config, _inventory_surface())
    _assert_single_regression(result, "freshly_added_pattern/")


def test_new_relaxing_override_block_not_in_inventory_is_a_regression() -> None:
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/"]

        [[tool.mypy.overrides]]
        module = "compat.new_silent_pkg.*"
        follow_imports = "silent"
        """
    )
    result = compare(config, _inventory_surface())
    assert not result.ok
    assert result.inventory_drift == ()
    assert len(result.regressions) == 1, result.regressions
    finding = result.regressions[0]
    assert "compat.new_silent_pkg.*" in finding
    assert "follow_imports" in finding


def test_new_relaxing_setting_on_an_already_listed_module_is_a_regression() -> None:
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/"]

        [[tool.mypy.overrides]]
        module = "compat.missing_pkg.*"
        ignore_missing_imports = true
        implicit_reexport = true
        """
    )
    inventory = _inventory_surface(
        overrides=(
            {
                "module": "compat.missing_pkg.*",
                "setting": "ignore_missing_imports",
                "value": json.dumps(True),
            },
        )
    )
    result = compare(config, inventory)
    assert not result.ok
    assert result.inventory_drift == ()
    assert len(result.regressions) == 1, result.regressions
    finding = result.regressions[0]
    assert "compat.missing_pkg.*" in finding
    assert "implicit_reexport" in finding
    assert "ignore_missing_imports" not in finding


def test_module_added_to_a_multi_module_override_block_is_a_regression() -> None:
    """A list-valued ``module`` key fans out to one entry per module; only the new one flags.

    Real overrides in this configuration relax many modules at once via a list-valued
    ``module`` key, so the most likely real regrowth is a module appended to such a block.
    This pins that the already-accepted module in the same block is not re-reported.
    """
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/"]

        [[tool.mypy.overrides]]
        module = ["compat.pkg_a.*", "compat.pkg_b.*"]
        follow_imports = "silent"
        """
    )
    inventory = _inventory_surface(
        overrides=(
            {
                "module": "compat.pkg_a.*",
                "setting": "follow_imports",
                "value": json.dumps("silent"),
            },
        )
    )
    result = compare(config, inventory)
    assert not result.ok
    assert result.inventory_drift == ()
    assert len(result.regressions) == 1, result.regressions
    finding = result.regressions[0]
    assert "compat.pkg_b.*" in finding
    assert "compat.pkg_a.*" not in finding


def test_module_added_to_an_ignore_missing_imports_block_is_a_regression() -> None:
    """Pins the same fan-out for ignore_missing_imports, the largest real relaxation block."""
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/"]

        [[tool.mypy.overrides]]
        module = ["compat.pkg_one.*", "compat.pkg_two.*", "compat.pkg_three.*"]
        ignore_missing_imports = true
        """
    )
    inventory = _inventory_surface(
        overrides=(
            {
                "module": "compat.pkg_one.*",
                "setting": "ignore_missing_imports",
                "value": json.dumps(True),
            },
            {
                "module": "compat.pkg_two.*",
                "setting": "ignore_missing_imports",
                "value": json.dumps(True),
            },
        )
    )
    result = compare(config, inventory)
    assert not result.ok
    assert result.inventory_drift == ()
    assert len(result.regressions) == 1, result.regressions
    finding = result.regressions[0]
    assert "compat.pkg_three.*" in finding
    assert "compat.pkg_one.*" not in finding
    assert "compat.pkg_two.*" not in finding


def test_new_globally_disabled_error_code_is_a_regression() -> None:
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = ["annotation-unchecked"]
        exclude = ["legacy_module/"]
        """
    )
    result = compare(config, _inventory_surface())
    _assert_single_regression(result, "annotation-unchecked")


def test_removed_check_root_is_a_regression() -> None:
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/"]
        """
    )
    result = compare(config, _inventory_surface())
    _assert_single_regression(result, "docs")


def test_removed_enabled_error_code_is_a_regression() -> None:
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = []
        disable_error_code = []
        exclude = ["legacy_module/"]
        """
    )
    result = compare(config, _inventory_surface())
    _assert_single_regression(result, "ignore-without-code")


def test_follow_imports_weakened_from_normal_to_silent_is_a_regression() -> None:
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "silent"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/"]
        """
    )
    result = compare(config, _inventory_surface(follow_imports="normal"))
    _assert_single_regression(result, "less strictly")
    finding = result.regressions[0]
    assert "'silent'" in finding
    assert "'normal'" in finding


def test_follow_imports_weakened_from_silent_to_skip_is_a_regression() -> None:
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "skip"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/"]
        """
    )
    result = compare(config, _inventory_surface(follow_imports="silent"))
    _assert_single_regression(result, "less strictly")
    finding = result.regressions[0]
    assert "'skip'" in finding
    assert "'silent'" in finding


def test_unrecognized_override_setting_not_in_inventory_is_a_regression() -> None:
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/"]

        [[tool.mypy.overrides]]
        module = "compat.mystery_pkg.*"
        some_future_relaxation = true
        """
    )
    result = compare(config, _inventory_surface())
    assert not result.ok
    assert result.inventory_drift == ()
    assert len(result.regressions) == 1, result.regressions
    finding = result.regressions[0]
    assert "compat.mystery_pkg.*" in finding
    assert "some_future_relaxation" in finding


# --- drift: the inventory no longer describes the configuration ---------------------------


def test_removed_exclude_pattern_still_in_inventory_is_reported_as_drift() -> None:
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = []
        """
    )
    result = compare(config, _inventory_surface(exclude=("legacy_module/",)))
    _assert_single_drift(result, "legacy_module/")


def test_removed_override_still_in_inventory_is_reported_as_drift() -> None:
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/"]
        """
    )
    inventory = _inventory_surface(
        overrides=(
            {
                "module": "compat.missing_pkg.*",
                "setting": "ignore_missing_imports",
                "value": json.dumps(True),
            },
        )
    )
    result = compare(config, inventory)
    _assert_single_drift(result, "compat.missing_pkg.*")


def test_module_removed_from_a_multi_module_override_block_is_reported_as_drift() -> None:
    """Shrinking a list-valued ``module`` key drops only the removed module's entry as drift.

    Mirrors the regression-direction fan-out test above: the block keeps two of its three
    originally accepted modules, so only the dropped one should surface, and the two modules
    still present must not be re-reported as if they, too, had been removed.
    """
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/"]

        [[tool.mypy.overrides]]
        module = ["compat.pkg_a.*", "compat.pkg_c.*"]
        follow_imports = "silent"
        """
    )
    inventory = _inventory_surface(
        overrides=(
            {
                "module": "compat.pkg_a.*",
                "setting": "follow_imports",
                "value": json.dumps("silent"),
            },
            {
                "module": "compat.pkg_b.*",
                "setting": "follow_imports",
                "value": json.dumps("silent"),
            },
            {
                "module": "compat.pkg_c.*",
                "setting": "follow_imports",
                "value": json.dumps("silent"),
            },
        )
    )
    result = compare(config, inventory)
    assert not result.ok
    assert result.regressions == ()
    assert len(result.inventory_drift) == 1, result.inventory_drift
    finding = result.inventory_drift[0]
    assert "compat.pkg_b.*" in finding
    assert "compat.pkg_a.*" not in finding
    assert "compat.pkg_c.*" not in finding


def test_removed_globally_disabled_error_code_still_in_inventory_is_reported_as_drift() -> None:
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/"]
        """
    )
    result = compare(config, _inventory_surface(disable_error_code=("annotation-unchecked",)))
    _assert_single_drift(result, "annotation-unchecked")


def test_added_check_root_not_yet_in_inventory_is_reported_as_drift() -> None:
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests", "contrib"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/"]
        """
    )
    result = compare(config, _inventory_surface())
    _assert_single_drift(result, "contrib")


def test_added_enabled_error_code_not_yet_in_inventory_is_reported_as_drift() -> None:
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code", "explicit-override"]
        disable_error_code = []
        exclude = ["legacy_module/"]
        """
    )
    result = compare(config, _inventory_surface())
    _assert_single_drift(result, "explicit-override")


def test_follow_imports_strengthened_is_reported_as_drift_not_regression() -> None:
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/"]
        """
    )
    result = compare(config, _inventory_surface(follow_imports="silent"))
    _assert_single_drift(result, "more strictly")
    finding = result.inventory_drift[0]
    assert "'normal'" in finding
    assert "'silent'" in finding


# --- strengthening the configuration must never be reported as a regression ---------------


def test_removing_an_exclusion_and_pruning_the_inventory_passes() -> None:
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = []
        """
    )
    result = compare(config, _inventory_surface(exclude=()))
    assert result.ok
    assert result.regressions == ()
    assert result.inventory_drift == ()


def test_strengthening_override_setting_contributes_nothing_to_the_surface() -> None:
    """A tightened per-module setting drops out of the surface, so it never needs recording."""
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/"]

        [[tool.mypy.overrides]]
        module = "compat.missing_pkg.*"
        ignore_missing_imports = true
        check_untyped_defs = true
        enable_error_code = ["misc"]
        """
    )
    inventory = _inventory_surface(
        overrides=(
            {
                "module": "compat.missing_pkg.*",
                "setting": "ignore_missing_imports",
                "value": json.dumps(True),
            },
        )
    )
    result = compare(config, inventory)
    assert result.ok
    assert result.regressions == ()
    assert result.inventory_drift == ()


# --- fail-closed classification: an unrecognized setting is always relaxing ---------------


def test_unrecognized_setting_true_value_fails_closed_as_relaxing() -> None:
    _assert_setting_is_relaxing("some_unheard_of_flag", True)


def test_unrecognized_setting_false_value_fails_closed_as_relaxing() -> None:
    _assert_setting_is_relaxing("some_unheard_of_flag", False)


def test_unrecognized_setting_string_value_fails_closed_as_relaxing() -> None:
    _assert_setting_is_relaxing("some_unheard_of_flag", "strict")


def test_unrecognized_setting_integer_value_fails_closed_as_relaxing() -> None:
    _assert_setting_is_relaxing("some_unheard_of_flag", 0)


def test_unrecognized_setting_empty_list_value_fails_closed_as_relaxing() -> None:
    _assert_setting_is_relaxing("some_unheard_of_flag", [])


def test_unrecognized_setting_none_value_fails_closed_as_relaxing() -> None:
    _assert_setting_is_relaxing("some_unheard_of_flag", None)


# --- fail-closed classification: a recognized setting with a malformed value shape --------


def test_laxness_boolean_setting_with_a_non_boolean_value_fails_closed_as_relaxing() -> None:
    _assert_setting_is_relaxing("ignore_missing_imports", 1)


def test_strictness_boolean_setting_with_a_non_boolean_value_fails_closed_as_relaxing() -> None:
    _assert_setting_is_relaxing("disallow_untyped_defs", 0)


def test_override_follow_imports_with_an_unrecognized_value_fails_closed_as_relaxing() -> None:
    _assert_setting_is_relaxing("follow_imports", "bogus")


# --- the classifier is not merely fail-closed for everything: it recognizes safe values ---


def test_recognized_laxness_boolean_true_is_relaxing() -> None:
    _assert_setting_is_relaxing("ignore_missing_imports", True)


def test_recognized_laxness_boolean_false_is_not_relaxing() -> None:
    _assert_setting_is_not_relaxing("ignore_missing_imports", False)


def test_recognized_strictness_boolean_false_is_relaxing() -> None:
    _assert_setting_is_relaxing("disallow_untyped_defs", False)


def test_recognized_strictness_boolean_true_is_not_relaxing() -> None:
    _assert_setting_is_not_relaxing("disallow_untyped_defs", True)


def test_enable_error_code_on_an_override_is_never_relaxing() -> None:
    _assert_setting_is_not_relaxing("enable_error_code", ["misc"])


def test_override_follow_imports_normal_is_not_relaxing() -> None:
    _assert_setting_is_not_relaxing("follow_imports", "normal")


def test_override_follow_imports_silent_is_relaxing() -> None:
    _assert_setting_is_relaxing("follow_imports", "silent")


def test_override_follow_imports_skip_is_relaxing() -> None:
    _assert_setting_is_relaxing("follow_imports", "skip")


def test_disable_error_code_empty_on_an_override_is_not_relaxing() -> None:
    _assert_setting_is_not_relaxing("disable_error_code", [])


def test_disable_error_code_nonempty_on_an_override_is_relaxing() -> None:
    _assert_setting_is_relaxing("disable_error_code", ["misc"])


# --- the regression message teaches alternatives and never names a way around itself ------


def test_regression_message_states_exactly_three_alternatives_and_names_no_bypass() -> None:
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/", "freshly_added_pattern/"]
        """
    )
    result = compare(config, _inventory_surface())
    message = _format_regression_message(result.regressions)

    assert len(_REGRESSION_ALTERNATIVES) == 3
    for alternative in _REGRESSION_ALTERNATIVES:
        assert alternative in message

    assert "mypy_relaxation_inventory.json" not in message
    assert "--emit-inventory" not in message
    assert "--pyproject" not in message
    assert "--inventory" not in message


def test_combined_regression_and_drift_output_withholds_the_bypass_flag() -> None:
    """The one case where a leak would matter most: a regression alongside stale drift."""
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/", "brand_new_pattern/"]
        """
    )
    inventory = _inventory_surface(exclude=("legacy_module/", "stale_pattern/"))
    result = compare(config, inventory)
    assert not result.ok
    assert len(result.regressions) == 1, result.regressions
    assert len(result.inventory_drift) == 1, result.inventory_drift
    assert "brand_new_pattern/" in result.regressions[0]
    assert "stale_pattern/" in result.inventory_drift[0]

    inventory_path = Path("scripts/mypy_relaxation_inventory.json")

    original_stderr = sys.stderr
    sys.stderr = io.StringIO()
    try:
        _print_result(result, inventory_path)
        combined_output = sys.stderr.getvalue()
    finally:
        sys.stderr = original_stderr

    regression_section, _, drift_section = combined_output.partition("\n\n")

    assert "brand_new_pattern/" in regression_section
    assert "--emit-inventory" not in regression_section
    assert "mypy_relaxation_inventory.json" not in regression_section

    assert "stale_pattern/" in drift_section
    assert "mypy_relaxation_inventory.json" in drift_section
    assert "--emit-inventory" not in combined_output


# --- the drift message names the inventory and instructs how to reconcile it --------------


def test_drift_message_names_inventory_and_instructs_reconciliation() -> None:
    """The drift message must both name the inventory file and tell a contributor how to
    reconcile it: prune stale entries and record newly-applied strictness.

    A newly-added check root produces a drift finding whose own text already contains the
    word "recorded" (``_set_diff_findings``'s wording for that direction: "present in the
    configuration but not yet recorded in the accepted relaxation inventory"). The
    instruction assertions below are scoped to the text *after* the findings block - never to
    the whole message - so this test cannot pass on that finding text alone; it must see the
    actual reconciliation instruction.
    """
    config = _surface_from_toml(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests", "freshly_added_root"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/"]
        """
    )
    result = compare(config, _inventory_surface())
    assert result.regressions == ()
    assert len(result.inventory_drift) == 1, result.inventory_drift
    assert "freshly_added_root" in result.inventory_drift[0]
    assert "recorded" in result.inventory_drift[0]  # the trap: this alone must not satisfy us

    inventory_path = Path("scripts/mypy_relaxation_inventory.json")
    message = _format_drift_message(
        result.inventory_drift, inventory_path, include_regeneration_hint=False
    )
    header, _, instruction = message.partition("\n\n")

    assert "mypy_relaxation_inventory.json" in header
    assert "prune entries the configuration no longer relaxes" in instruction
    assert "Record any strictness the configuration now applies" in instruction


# --- unparseable input fails closed, never silently passes --------------------------------


def test_missing_tool_mypy_table_raises_a_config_error() -> None:
    with pytest.raises(GuardConfigError, match=r"tool\.mypy"):
        extract_surface(tomllib.loads("[tool.other]\nkey = 1\n"))


def test_missing_tool_mypy_table_exits_with_the_unparseable_input_code(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text("[tool.other]\nkey = 1\n")
    inventory_path = tmp_path / "mypy_relaxation_inventory.json"  # never reached

    exit_code = main(["--pyproject", str(pyproject_path), "--inventory", str(inventory_path)])

    assert exit_code == 2


def test_malformed_toml_syntax_exits_with_the_unparseable_input_code(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text("this is not [[[ valid toml\n")
    inventory_path = tmp_path / "mypy_relaxation_inventory.json"  # never reached

    exit_code = main(["--pyproject", str(pyproject_path), "--inventory", str(inventory_path)])

    assert exit_code == 2


def test_unparseable_inventory_exits_with_the_unparseable_input_code(tmp_path: Path) -> None:
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/"]
        """
    )
    inventory_path = tmp_path / "mypy_relaxation_inventory.json"
    inventory_path.write_text("{ not valid json")

    exit_code = main(["--pyproject", str(pyproject_path), "--inventory", str(inventory_path)])

    assert exit_code == 2


def test_valid_configuration_and_inventory_pair_exits_zero_via_the_cli(tmp_path: Path) -> None:
    """End-to-end confirmation that a matching pair passes through the CLI, not just compare()."""
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        """
        [tool.mypy]
        files = ["great_expectations", "docs", "tests"]
        follow_imports = "normal"
        enable_error_code = ["ignore-without-code"]
        disable_error_code = []
        exclude = ["legacy_module/"]
        """
    )
    inventory_path = tmp_path / "mypy_relaxation_inventory.json"
    inventory_path.write_text(
        json.dumps(
            {
                "exclude": ["legacy_module/"],
                "files": ["great_expectations", "docs", "tests"],
                "enable_error_code": ["ignore-without-code"],
                "disable_error_code": [],
                "follow_imports": "normal",
                "overrides": [],
            }
        )
    )

    exit_code = main(["--pyproject", str(pyproject_path), "--inventory", str(inventory_path)])

    assert exit_code == 0
