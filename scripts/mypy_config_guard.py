"""Fail the type-check job when the mypy configuration grows a new relaxation.

**Why this exists.** A mypy configuration can be relaxed in ways that are easy to add and
easy to miss in review: a new ``exclude`` pattern that quietly drops a module from checking,
a new per-module override that turns off missing-import errors or switches import following
to ``silent``, a newly disabled error code, or a shrunk set of check roots or enabled codes.
Each of these looks like a small, reasonable diff line and none of them shows up as a type
error - the whole point of a relaxation is that it stops mypy from looking. Once the
configuration has been cleaned up to describe only real, live relaxations, the risk shifts
from "the configuration lies about what it does" to "the configuration quietly regrows what
was just cleaned out." This script is the guard against the second risk.

**The mental model.** Call everything in the mypy configuration that weakens checking - an
``exclude`` pattern, a per-module override setting that loosens checking, a globally disabled
error code, or a weaker global ``follow_imports`` mode, a missing check root, or a missing
enabled error code - the configuration's *relaxation surface*. Next to the configuration sits
a committed, machine-generated file, the *relaxation inventory*
(``scripts/mypy_relaxation_inventory.json``): a snapshot of exactly the relaxation surface
that has been reviewed and accepted. This script extracts the live surface from
``pyproject.toml``, loads the accepted surface from the inventory, and compares them field by
field. The two surfaces must match exactly. A field present in the configuration but absent
from the inventory, or vice versa, is always a finding - never silently ignored - but which
of the two failure classes it becomes depends on the field:

- For ``exclude`` patterns, override entries, and globally disabled error codes, something
  the configuration now has that the inventory does not is a **regression**: a new
  relaxation was added without being reviewed as one. Something the inventory has that the
  configuration no longer does is **inventory drift**: the relaxation was removed (good) but
  the inventory was not pruned to match.
- For check roots and enabled error codes, the direction flips: these fields get *weaker*
  when an entry is *removed*, so a missing entry is the regression and a newly added one is
  drift (recording a strengthening the inventory has not caught up with yet).
- The global ``follow_imports`` mode is compared by strictness order
  (``normal``/``error`` < ``silent`` < ``skip``); moving to a laxer mode is a regression,
  moving to a stricter one is drift.

**Deliberately accepting a new relaxation.** Sometimes relaxing the configuration really is
the right call - a batch of files temporarily excluded during a migration, a third-party
package whose stubs are known to be broken. That is not this script's decision to make; it is
a decision for whoever reviews the pull request that introduces it. The path is: make the
configuration change, then regenerate the inventory by running this script with
``--emit-inventory`` and committing its stdout as the new
``scripts/mypy_relaxation_inventory.json``. The resulting diff to the inventory file is
exactly the relaxation being introduced, sitting
in the same pull request as the configuration change, visible to a reviewer like any other
line of code. ``--emit-inventory`` only ever prints to stdout - it never writes the inventory
file itself, so committing the new inventory is always an explicit, visible act.

**Fail-closed classification.** A per-module override can set settings this script's
classifier has never heard of. Rather than silently letting an unrecognized setting through,
the classifier treats anything it does not recognize as relaxing. A setting can only be
excluded from the relaxation surface by being explicitly classified as safe, never by being
unfamiliar.

**Exit codes.** ``0``: the configuration's relaxation surface matches the inventory exactly.
``1``: a regression, inventory drift, or both were found (see stderr for details). ``2``: the
configuration or inventory could not be read or parsed, or the command line was invalid - the
check fails closed rather than silently passing on unreadable input.

**TOML parsing.** This module reads ``pyproject.toml`` with the standard library's
``tomllib`` where available (Python 3.11+) and falls back to the third-party ``tomli``
package on older interpreters. ``tomli`` needs no new dependency: both mypy and pytest
already depend on it below Python 3.11, so it is present in every environment this script
runs in.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

if sys.version_info >= (3, 11):
    import tomllib
else:  # Python 3.10 and earlier
    import tomli as tomllib


_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_PYPROJECT_PATH = _REPO_ROOT / "pyproject.toml"
_DEFAULT_INVENTORY_PATH = _REPO_ROOT / "scripts" / "mypy_relaxation_inventory.json"


class GuardConfigError(Exception):
    """The mypy configuration or the relaxation inventory could not be read as expected."""


@dataclasses.dataclass(frozen=True)
class OverrideEntry:
    """One (module pattern, relaxing setting, canonical value) triple."""

    module: str
    setting: str
    value: str  # canonical JSON rendering of the setting's value


def _override_sort_key(entry: OverrideEntry) -> tuple[str, str, str]:
    return (entry.module, entry.setting, entry.value)


@dataclasses.dataclass(frozen=True)
class RelaxationSurface:
    """Every field of the mypy configuration this guard tracks for relaxation."""

    exclude: frozenset[str]
    files: frozenset[str]
    enable_error_code: frozenset[str]
    disable_error_code: frozenset[str]
    follow_imports: str
    overrides: frozenset[OverrideEntry]


@dataclasses.dataclass(frozen=True)
class ComparisonResult:
    """The outcome of comparing a configuration's surface against the accepted inventory."""

    regressions: tuple[str, ...]  # findings whose fix is: do not relax
    inventory_drift: tuple[str, ...]  # findings whose fix is: reconcile the inventory

    @property
    def ok(self) -> bool:
        return not self.regressions and not self.inventory_drift


# --- relaxing-setting classification (fail-closed: unrecognized settings count as relaxing) ---

_LAXNESS_BOOLEAN_NAMES = frozenset({"ignore_missing_imports", "ignore_errors", "implicit_reexport"})
_LAXNESS_BOOLEAN_PREFIXES = ("allow_",)
_STRICTNESS_BOOLEAN_NAMES = frozenset({"check_untyped_defs"})
_STRICTNESS_BOOLEAN_PREFIXES = ("disallow_", "warn_", "strict_", "no_implicit_")

_FOLLOW_IMPORTS_LAX_VALUES = frozenset({"silent", "skip"})
_FOLLOW_IMPORTS_LEVELS = {"normal": 0, "error": 0, "silent": 1, "skip": 2}
_FOLLOW_IMPORTS_LAXEST_LEVEL = max(_FOLLOW_IMPORTS_LEVELS.values()) + 1


def _bool_setting_is_relaxing(value: object, *, relaxing_value: bool) -> bool:
    """Whether a boolean-typed setting's value is its relaxing one.

    Fails closed when value is not literally a bool: an unexpected value shape
    (e.g. an int or string where a bool was expected) is not one we can certify
    as safe, so it counts as relaxing rather than being compared by truthiness.
    """
    if not isinstance(value, bool):
        return True
    return value is relaxing_value


def _is_relaxing(setting: str, value: object) -> bool:
    """Whether one (setting, value) pair, taken alone, weakens checking."""
    if setting == "enable_error_code":
        return False  # never relaxing
    if setting == "follow_imports":
        # An unrecognized follow_imports value fails closed, mirroring the global
        # follow_imports comparison's use of _FOLLOW_IMPORTS_LAXEST_LEVEL.
        return value not in _FOLLOW_IMPORTS_LEVELS or value in _FOLLOW_IMPORTS_LAX_VALUES
    if setting == "disable_error_code":
        return bool(value)  # relaxing when non-empty
    if setting in _LAXNESS_BOOLEAN_NAMES or setting.startswith(_LAXNESS_BOOLEAN_PREFIXES):
        return _bool_setting_is_relaxing(value, relaxing_value=True)
    if setting in _STRICTNESS_BOOLEAN_NAMES or setting.startswith(_STRICTNESS_BOOLEAN_PREFIXES):
        return _bool_setting_is_relaxing(value, relaxing_value=False)
    # Unrecognized setting: fail closed. We do not know what this does, so we cannot
    # certify it as safe.
    return True


def relaxing_settings(override: Mapping[str, object]) -> dict[str, object]:
    """The subset of a per-module override's settings that weaken checking.

    Classification: laxness booleans (ignore_missing_imports, ignore_errors,
    implicit_reexport, allow_*) are relaxing when true; strictness booleans
    (disallow_*, check_untyped_defs, warn_*, strict_*, no_implicit_*) are relaxing
    when false; follow_imports is relaxing when silent or skip; disable_error_code
    is relaxing when non-empty; enable_error_code is never relaxing; any setting
    not recognized by these rules is treated as relaxing (fail-closed).
    """
    return {
        setting: value
        for setting, value in override.items()
        if setting != "module" and _is_relaxing(setting, value)
    }


def _canonical_value(value: object) -> str:
    """Render a setting's value as canonical JSON, independent of source ordering."""
    return json.dumps(_sorted_recursively(value), sort_keys=True)


def _sorted_recursively(value: object) -> object:
    if isinstance(value, list):
        items: list[Any] = [_sorted_recursively(item) for item in value]
        try:
            return sorted(items)
        except TypeError:
            return items
    if isinstance(value, dict):
        return {key: _sorted_recursively(item) for key, item in value.items()}
    return value


# --- surface extraction -------------------------------------------------------------------


def _require_table(value: object, description: str) -> None:
    """Raise GuardConfigError unless value is a TOML table (a dict once parsed)."""
    if not isinstance(value, dict):
        msg = f"{description} must be a table"
        raise GuardConfigError(msg)


def _extract_override_entries(override: Mapping[str, Any]) -> Iterable[OverrideEntry]:
    """The relaxing OverrideEntry objects one [[tool.mypy.overrides]] block contributes."""
    modules_raw = override.get("module", [])
    modules = [modules_raw] if isinstance(modules_raw, str) else list(modules_raw)
    settings = {key: value for key, value in override.items() if key != "module"}
    for setting, value in relaxing_settings(settings).items():
        canonical = _canonical_value(value)
        for module in modules:
            yield OverrideEntry(module=module, setting=setting, value=canonical)


def extract_surface(pyproject: Mapping[str, Any]) -> RelaxationSurface:
    """Build the surface from a parsed pyproject document.

    Raises GuardConfigError if [tool.mypy] is absent or malformed - a parse
    failure must fail the check, never pass it.
    """
    try:
        mypy_config = pyproject["tool"]["mypy"]
    except (KeyError, TypeError) as exc:
        msg = "pyproject.toml has no [tool.mypy] table to check"
        raise GuardConfigError(msg) from exc
    _require_table(mypy_config, "[tool.mypy]")

    try:
        exclude = frozenset(mypy_config.get("exclude", []))
        files = frozenset(mypy_config.get("files", []))
        enable_error_code = frozenset(mypy_config.get("enable_error_code", []))
        disable_error_code = frozenset(mypy_config.get("disable_error_code", []))
        follow_imports = str(mypy_config.get("follow_imports", "normal"))

        overrides: set[OverrideEntry] = set()
        for override in mypy_config.get("overrides", []):
            _require_table(override, "each [[tool.mypy.overrides]] entry")
            overrides.update(_extract_override_entries(override))
    except GuardConfigError:
        raise
    except (TypeError, AttributeError) as exc:
        msg = f"[tool.mypy] is malformed: {exc}"
        raise GuardConfigError(msg) from exc

    return RelaxationSurface(
        exclude=exclude,
        files=files,
        enable_error_code=enable_error_code,
        disable_error_code=disable_error_code,
        follow_imports=follow_imports,
        overrides=frozenset(overrides),
    )


def _serialize_surface(surface: RelaxationSurface) -> dict[str, Any]:
    """Render a surface as the inventory's JSON document shape."""
    return {
        "exclude": sorted(surface.exclude),
        "files": sorted(surface.files),
        "enable_error_code": sorted(surface.enable_error_code),
        "disable_error_code": sorted(surface.disable_error_code),
        "follow_imports": surface.follow_imports,
        "overrides": [
            {"module": entry.module, "setting": entry.setting, "value": entry.value}
            for entry in sorted(surface.overrides, key=_override_sort_key)
        ],
    }


def load_inventory(raw: Mapping[str, Any]) -> RelaxationSurface:
    """Build the accepted surface from the committed inventory document."""
    try:
        overrides = frozenset(
            OverrideEntry(module=entry["module"], setting=entry["setting"], value=entry["value"])
            for entry in raw["overrides"]
        )
        return RelaxationSurface(
            exclude=frozenset(raw["exclude"]),
            files=frozenset(raw["files"]),
            enable_error_code=frozenset(raw["enable_error_code"]),
            disable_error_code=frozenset(raw["disable_error_code"]),
            follow_imports=str(raw["follow_imports"]),
            overrides=overrides,
        )
    except (KeyError, TypeError) as exc:
        msg = f"relaxation inventory is missing an expected field: {exc}"
        raise GuardConfigError(msg) from exc


# --- direction-aware comparison -----------------------------------------------------------


def _set_diff_findings(
    label: str,
    config_items: Iterable[str],
    inventory_items: Iterable[str],
    *,
    added_is_regression: bool,
) -> tuple[list[str], list[str]]:
    """Diff one flat-string field, returning (regressions, drift) finding strings.

    added_is_regression is True for fields that relax when something is *added* to the
    configuration (exclude, globally disabled codes) and False for fields that relax when
    something is *removed* (check roots, enabled codes).
    """
    added = sorted(set(config_items) - set(inventory_items))
    removed = sorted(set(inventory_items) - set(config_items))

    regressions: list[str] = []
    drift: list[str] = []
    if added_is_regression:
        regressions.extend(
            f"{label} {item!r} is present in the configuration but not in the accepted "
            "relaxation inventory"
            for item in added
        )
        drift.extend(
            f"{label} {item!r} is recorded in the accepted relaxation inventory but is no "
            "longer present in the configuration"
            for item in removed
        )
    else:
        drift.extend(
            f"{label} {item!r} is present in the configuration but not yet recorded in the "
            "accepted relaxation inventory"
            for item in added
        )
        regressions.extend(
            f"{label} {item!r} is recorded in the accepted relaxation inventory but is no "
            "longer present in the configuration"
            for item in removed
        )
    return regressions, drift


def _override_findings(
    config_overrides: frozenset[OverrideEntry],
    inventory_overrides: frozenset[OverrideEntry],
) -> tuple[list[str], list[str]]:
    added = sorted(config_overrides - inventory_overrides, key=_override_sort_key)
    removed = sorted(inventory_overrides - config_overrides, key=_override_sort_key)

    def describe(entry: OverrideEntry) -> str:
        return (
            f"override entry (module={entry.module!r}, setting={entry.setting!r}, "
            f"value={entry.value})"
        )

    regressions = [
        f"{describe(entry)} is present in the configuration but not in the accepted "
        "relaxation inventory"
        for entry in added
    ]
    drift = [
        f"{describe(entry)} is recorded in the accepted relaxation inventory but is no "
        "longer present in the configuration"
        for entry in removed
    ]
    return regressions, drift


def _follow_imports_findings(
    config_value: str, inventory_value: str
) -> tuple[list[str], list[str]]:
    config_level = _FOLLOW_IMPORTS_LEVELS.get(config_value, _FOLLOW_IMPORTS_LAXEST_LEVEL)
    inventory_level = _FOLLOW_IMPORTS_LEVELS.get(inventory_value, _FOLLOW_IMPORTS_LAXEST_LEVEL)
    if config_level > inventory_level:
        return (
            [
                f"global follow_imports is {config_value!r}, which follows imports less "
                f"strictly than the accepted {inventory_value!r}"
            ],
            [],
        )
    if config_level < inventory_level:
        return (
            [],
            [
                f"global follow_imports is {config_value!r}, which follows imports more "
                f"strictly than the accepted relaxation inventory records ({inventory_value!r})"
            ],
        )
    return [], []


def compare(surface: RelaxationSurface, inventory: RelaxationSurface) -> ComparisonResult:
    """Direction-aware exact comparison; equal surfaces yield ok."""
    regressions: list[str] = []
    drift: list[str] = []

    field_specs: tuple[tuple[str, frozenset[str], frozenset[str], bool], ...] = (
        ("exclude pattern", surface.exclude, inventory.exclude, True),
        (
            "globally disabled error code",
            surface.disable_error_code,
            inventory.disable_error_code,
            True,
        ),
        ("check root", surface.files, inventory.files, False),
        ("enabled error code", surface.enable_error_code, inventory.enable_error_code, False),
    )
    for label, config_items, inventory_items, added_is_regression in field_specs:
        found_regressions, found_drift = _set_diff_findings(
            label, config_items, inventory_items, added_is_regression=added_is_regression
        )
        regressions.extend(found_regressions)
        drift.extend(found_drift)

    found_regressions, found_drift = _override_findings(surface.overrides, inventory.overrides)
    regressions.extend(found_regressions)
    drift.extend(found_drift)

    found_regressions, found_drift = _follow_imports_findings(
        surface.follow_imports, inventory.follow_imports
    )
    regressions.extend(found_regressions)
    drift.extend(found_drift)

    return ComparisonResult(regressions=tuple(regressions), inventory_drift=tuple(drift))


# --- messages -------------------------------------------------------------------------------

# Exactly three alternatives (see the module docstring's "deliberately accepting a new
# relaxation" section for the reviewed path this deliberately does not name here). This
# message must never describe a mechanism that would make the failure pass - only what a
# contributor should do about their own code.
_REGRESSION_ALTERNATIVES = (
    "fix or annotate the code so it type-checks as written",
    "suppress only the offending line with a code-scoped, comment-bearing inline ignore, "
    "e.g. `# type: ignore[<code>]  # <reason the suppression is correct>`",
    "raise the case for maintainer review as a deliberate decision",
)


def _format_regression_message(findings: Sequence[str]) -> str:
    lines = ["Type checking would be relaxed by this change:"]
    lines.extend(f"  - {finding}" for finding in findings)
    lines.append("")
    lines.append("Instead:")
    numbered_alternatives = enumerate(_REGRESSION_ALTERNATIVES, start=1)
    lines.extend(f"  {index}. {alternative}" for index, alternative in numbered_alternatives)
    return "\n".join(lines)


def _render_inventory_path(inventory_path: Path) -> str:
    """Render an inventory path for display: repo-relative when it is inside the repo this
    script lives in, else the path as given (unresolved), so a caller pointing outside the
    tree still sees something unambiguous instead of a crash."""
    try:
        return str(inventory_path.resolve().relative_to(_REPO_ROOT))
    except ValueError:
        return str(inventory_path)


def _format_drift_message(
    findings: Sequence[str], inventory_path: Path, *, include_regeneration_hint: bool
) -> str:
    lines = [
        f"The relaxation inventory ({_render_inventory_path(inventory_path)}) no longer "
        "matches the configuration it is meant to describe:",
    ]
    lines.extend(f"  - {finding}" for finding in findings)
    lines.append("")
    lines.append(
        "Reconcile the inventory with the configuration: prune entries the configuration no "
        "longer relaxes. Record any strictness the configuration now applies that the "
        "inventory has not yet caught up with."
    )
    if include_regeneration_hint:
        lines.append(
            "This script's --emit-inventory mode prints the current configuration's "
            "relaxation surface as inventory JSON to stdout for that reconciliation; "
            "review and commit its output as the new inventory file."
        )
    return "\n".join(lines)


# --- CLI ------------------------------------------------------------------------------------


def _load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare the mypy configuration's relaxation surface against the accepted "
            "relaxation inventory."
        )
    )
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=_DEFAULT_PYPROJECT_PATH,
        help="Path to the pyproject.toml file holding the [tool.mypy] configuration.",
    )
    parser.add_argument(
        "--inventory",
        type=Path,
        default=_DEFAULT_INVENTORY_PATH,
        help="Path to the accepted relaxation inventory JSON file.",
    )
    parser.add_argument(
        "--emit-inventory",
        action="store_true",
        help=(
            "Print the current configuration's relaxation surface as inventory JSON to "
            "stdout, then exit. Does not read or write the inventory file."
        ),
    )
    return parser


def _read_surface(pyproject_path: Path) -> RelaxationSurface:
    return extract_surface(_load_toml(pyproject_path))


def _read_inventory(inventory_path: Path) -> RelaxationSurface:
    return load_inventory(json.loads(inventory_path.read_text()))


def _print_result(result: ComparisonResult, inventory_path: Path) -> None:
    if result.regressions:
        print(_format_regression_message(result.regressions), file=sys.stderr)
    if result.inventory_drift:
        if result.regressions:
            print(file=sys.stderr)
        print(
            _format_drift_message(
                result.inventory_drift,
                inventory_path,
                include_regeneration_hint=not result.regressions,
            ),
            file=sys.stderr,
        )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI: exit 0 ok; exit 1 regression or drift; exit 2 usage or parse error."""
    try:
        args = _build_arg_parser().parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2

    try:
        surface = _read_surface(args.pyproject)
    except (GuardConfigError, OSError, tomllib.TOMLDecodeError) as exc:
        print(f"error: could not read the mypy configuration: {exc}", file=sys.stderr)
        return 2

    if args.emit_inventory:
        json.dump(_serialize_surface(surface), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    try:
        inventory_surface = _read_inventory(args.inventory)
    except (GuardConfigError, OSError, json.JSONDecodeError) as exc:
        print(f"error: could not read the relaxation inventory: {exc}", file=sys.stderr)
        return 2

    result = compare(surface, inventory_surface)
    if result.ok:
        return 0

    _print_result(result, args.inventory)
    return 1


if __name__ == "__main__":
    sys.exit(main())
