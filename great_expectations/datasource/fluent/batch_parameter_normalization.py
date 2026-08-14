from __future__ import annotations

import os
import re
import sys
import sysconfig
import warnings
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Collection,
    Dict,
    Final,
    FrozenSet,
    List,
    Optional,
    Pattern,
    Tuple,
)

from great_expectations.warnings import GxDeprecationWarning

if TYPE_CHECKING:
    from types import FrameType

    from great_expectations.datasource.fluent.batch_request import BatchParameters

BATCH_PARAMETER_DEPRECATION_MESSAGE_PREFIX: Final[str] = (
    "String values for numeric batch parameters are deprecated"
)

_DIGIT_STRING_PATTERN: Final[Pattern[str]] = re.compile(r"[0-9]+")

# Roots used to identify "library" frames (this package plus the stdlib) so the
# deprecation warning below can be attributed to the first frame outside both,
# i.e. the user's own code. Realpath-normalized so Homebrew's opt/ symlinks
# (which resolve into Cellar/) don't defeat a raw prefix comparison.
_GX_PACKAGE_ROOT: Final[str] = str(Path(__file__).resolve().parent.parent.parent)
_STDLIB_ROOTS: Final[Tuple[str, ...]] = tuple(
    {
        str(Path(sysconfig.get_paths()["stdlib"]).resolve()),
        str(Path(sysconfig.get_paths()["platstdlib"]).resolve()),
    }
)


def is_digit_string(value: object) -> bool:
    """True iff value is a str matching fullmatch [0-9]+ (ASCII only).

    Bools, ints, None, signed/whitespace/Unicode-digit strings all return False:
    only plain ASCII digit sequences (including zero-padded ones like "04") count.
    Bools are excluded implicitly: `isinstance(True, str)` is False, so they never
    reach the pattern match.
    """
    if not isinstance(value, str):
        return False
    return _DIGIT_STRING_PATTERN.fullmatch(value) is not None


def normalize_batch_parameters(
    options: Optional[BatchParameters],
    numeric_parameter_names: Collection[str],
) -> Optional[BatchParameters]:
    """Coerce digit-string values under numeric_parameter_names to int.

    Returns a new dict when anything is coerced; the input dict is never mutated.
    When nothing is coercible (including when options is None/empty or
    numeric_parameter_names is empty), the identical `options` object is returned
    and nothing is emitted. This function never raises: values that cannot be
    interpreted as digit-strings are left untouched for the caller to diagnose
    downstream.
    """
    if not options or not numeric_parameter_names:
        return options

    numeric_names = set(numeric_parameter_names)
    coerced_keys: List[str] = []
    result: Optional[Dict[str, Any]] = None
    for key, value in options.items():
        if key in numeric_names and is_digit_string(value):
            if result is None:
                result = dict(options)
            result[key] = int(value)
            coerced_keys.append(key)

    if result is None:
        return options

    _warn_digit_string_coercion(coerced_keys)
    return result


def batch_parameter_values_match(requested: object, candidate: object) -> bool:
    """Equality extended with int-to-digit-string numeric equivalence.

    - requested == candidate -> True (today's rule, unchanged), except bools never
      numerically equate to anything but another bool of the same value.
    - one side a non-bool int, the other a digit-string -> compared as ints
      (so "04" and 4 match).
    - all other cross-type pairs -> False, including string-vs-string ("01" vs "1"
      stays an exact, non-numeric comparison).
    """
    if isinstance(requested, bool) or isinstance(candidate, bool):
        return type(requested) is type(candidate) and requested == candidate

    if requested == candidate:
        return True

    if isinstance(requested, int) and isinstance(candidate, str) and is_digit_string(candidate):
        return requested == int(candidate)

    if isinstance(candidate, int) and isinstance(requested, str) and is_digit_string(requested):
        return int(requested) == candidate

    return False


def numeric_parameter_names_of(partitioner: object) -> FrozenSet[str]:
    """The partitioner's declared numeric_param_names, or empty when it declares none.

    Fail-closed: a partitioner of an unrecognized kind, one with no such
    attribute, one whose declaration raises while being read, or one whose
    declaration isn't a usable collection of names (a bare string, or
    anything non-iterable) is treated as declaring nothing and is therefore
    exempt from coercion rather than assumed numeric.
    """
    if partitioner is None:
        return frozenset()
    try:
        names = getattr(partitioner, "numeric_param_names", None)
    except Exception:
        return frozenset()
    if not names or isinstance(names, str):
        return frozenset()
    try:
        return frozenset(names)
    except TypeError:
        return frozenset()


def _warn_digit_string_coercion(coerced_key_names: Collection[str]) -> None:
    """Emit the single deprecation warning for a coercion, attributed to user code."""
    names = ", ".join(sorted(coerced_key_names))
    message = (
        f"{BATCH_PARAMETER_DEPRECATION_MESSAGE_PREFIX}: {names}. "
        "Pass integer values instead; string support is planned for removal in 2.0."
    )
    warnings.warn(  # deprecated-v1.21.0
        message, GxDeprecationWarning, stacklevel=_stacklevel_to_user_code()
    )


def _stacklevel_to_user_code() -> int:
    """Walk the call stack to find the stacklevel of the first non-library frame.

    "Library" means either this package or the stdlib (both realpath-normalized).
    The returned value is a stacklevel usable directly by the `warnings.warn` call
    in `_warn_digit_string_coercion`: stacklevel=2 identifies that function's
    immediate caller, stacklevel=3 the caller's caller, and so on. Falls back to 2
    (the immediate caller) when every frame above it is inside this package or the
    stdlib, which can happen in tests that call the module directly through only
    library code.
    """
    frame: Optional[FrameType] = sys._getframe(2)  # caller of _warn_digit_string_coercion
    level = 2
    while frame is not None:
        filename = str(Path(frame.f_code.co_filename).resolve())
        if not _is_library_frame(filename):
            return level
        frame = frame.f_back
        level += 1
    return 2


def _is_library_frame(realpath_filename: str) -> bool:
    roots = (_GX_PACKAGE_ROOT, *_STDLIB_ROOTS)
    return any(
        realpath_filename == root or realpath_filename.startswith(root + os.sep) for root in roots
    )
