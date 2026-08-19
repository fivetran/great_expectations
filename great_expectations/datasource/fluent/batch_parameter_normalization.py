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
    NamedTuple,
    Optional,
    Pattern,
    Set,
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
# Subtracted from the stdlib roots below. In a virtualenv site-packages is nested
# inside platstdlib (<venv>/lib/pythonX.Y/site-packages), so a prefix test against
# the stdlib roots alone classifies every installed distribution as library code --
# including the caller's own package, which is exactly the frame we are looking for.
_SITE_PACKAGES_ROOTS: Final[Tuple[str, ...]] = tuple(
    {
        str(Path(sysconfig.get_paths()["purelib"]).resolve()),
        str(Path(sysconfig.get_paths()["platlib"]).resolve()),
    }
)

# Per-process record of (message, user call-site file, user call-site line) triples
# that have already been warned on. Python's own per-module warning registry isn't a
# reliable substitute for this: it is invalidated wholesale whenever anything in the
# process (including code well outside our control, e.g. pandas mutating dtypes)
# calls warnings.filterwarnings/simplefilter, which happens routinely during a real
# checkpoint run. Keying on the user's own call site instead of the interpreter's
# filter state gives a "once per place in the user's code" guarantee that survives
# that mutation.
_WARNED_CALL_SITES: Set[Tuple[str, Optional[str], Optional[int]]] = set()


def _reset_warned_call_sites_for_tests() -> None:
    """Clear the per-process call-site dedup registry.

    Test-facing only: the registry is intentionally scoped to the process, so a test
    suite that asserts on warning counts must reset it between tests to avoid one
    test's emission suppressing another's identical (message, file, line) triple.
    Not part of the public API.
    """
    _WARNED_CALL_SITES.clear()


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


class _UserFrameLocation(NamedTuple):
    """Result of walking the stack to find the first non-library frame.

    `stacklevel` is usable directly by `warnings.warn`: stacklevel=2 identifies the
    immediate caller of `_warn_digit_string_coercion`, stacklevel=3 the caller's
    caller, and so on. `filename` and `lineno` are the resolved (realpath-normalized)
    location of that same frame, used as part of the dedup key so repeat warnings
    from the identical call site are recognized regardless of interpreter warning
    filter state. When the walk falls back (no user frame found -- every frame above
    is inside this package or the stdlib), `filename`/`lineno` are None: there is no
    real user location to key on, so callers should treat that as its own bucket
    rather than colliding with any real call site.
    """

    stacklevel: int
    filename: Optional[str]
    lineno: Optional[int]


def _warn_digit_string_coercion(coerced_key_names: Collection[str]) -> None:
    """Emit the deprecation warning for a coercion, once per user call site.

    Attributed to user code via stacklevel. Deduplicated per-process on
    (message, call-site file, call-site line) rather than relying on Python's
    built-in per-module warning registry, which is invalidated process-wide by any
    unrelated `warnings.filterwarnings`/`simplefilter` call happening in between --
    something real workloads trigger routinely (e.g. pandas mutates warning filters
    while casting dtypes).
    """
    names = ", ".join(sorted(coerced_key_names))
    message = (
        f"{BATCH_PARAMETER_DEPRECATION_MESSAGE_PREFIX}: {names}. "
        "Pass integer values instead; string support is planned for removal in 2.0."
    )
    location = _stacklevel_to_user_code()
    key = (message, location.filename, location.lineno)
    if key in _WARNED_CALL_SITES:
        return

    # Record the call site only once the warning has actually reached someone.
    # warnings.warn returns normally when a filter suppresses the warning, so
    # recording beforehand would let a first occurrence that nobody could see spend
    # the one warning this call site gets -- silencing it for the rest of the
    # process precisely for the callers the deprecation exists to reach (a setup
    # phase under -W ignore, a framework quieting warnings while it initializes).
    # Delegating to whatever showwarning is installed keeps recorders (pytest's
    # recwarn, catch_warnings(record=True)) counting as delivery, and an "error"
    # filter propagates out of warn() with the site still unrecorded, so the next
    # occurrence raises again rather than being swallowed.
    delivered = False
    original_showwarning = warnings.showwarning

    def _mark_delivered(*args: Any, **kwargs: Any) -> None:
        nonlocal delivered
        delivered = True
        original_showwarning(*args, **kwargs)

    warnings.showwarning = _mark_delivered
    try:
        warnings.warn(  # deprecated-v1.21.0
            message, GxDeprecationWarning, stacklevel=location.stacklevel
        )
    finally:
        warnings.showwarning = original_showwarning

    if delivered:
        _WARNED_CALL_SITES.add(key)


def _stacklevel_to_user_code() -> _UserFrameLocation:
    """Walk the call stack to find the first non-library frame.

    "Library" means either this package or the stdlib (both realpath-normalized).
    Frames whose co_filename is a pseudo-filename -- the angle-bracket names the
    interpreter gives to code with no file ("<frozen runpy>", "<string>", "<stdin>",
    exec'd code) -- are not paths and are never resolved: doing so fabricates a path
    under the cwd that matches no library root, which would end the walk on whichever
    such frame it met first. Bootstrap frames are skipped; an entry-point frame is
    the user's own code and is keyed on its name verbatim.

    Falls back to stacklevel 2 (the immediate caller) with filename/lineno left None
    when every frame above it is inside this package or the stdlib, which can happen
    in tests that call the module directly through only library code.
    """
    frame: Optional[FrameType] = sys._getframe(2)  # caller of _warn_digit_string_coercion
    level = 2
    while frame is not None:
        raw_filename = frame.f_code.co_filename
        if raw_filename.startswith("<frozen "):
            # Import/runpy bootstrap, e.g. "<frozen runpy>" under `python -m`.
            frame = frame.f_back
            level += 1
            continue
        if raw_filename.startswith("<"):
            # "<string>", "<stdin>", exec'd code: the user's own entry point.
            return _UserFrameLocation(
                stacklevel=level, filename=raw_filename, lineno=frame.f_lineno
            )
        filename = str(Path(raw_filename).resolve())
        if not _is_library_frame(filename):
            return _UserFrameLocation(stacklevel=level, filename=filename, lineno=frame.f_lineno)
        frame = frame.f_back
        level += 1
    return _UserFrameLocation(stacklevel=2, filename=None, lineno=None)


def _is_library_frame(realpath_filename: str) -> bool:
    if _is_under_any(realpath_filename, _SITE_PACKAGES_ROOTS):
        # Under site-packages this package is the only library: anything else
        # installed alongside it is the caller -- their own package, or a framework
        # wrapping us -- and is the closest thing to "the user's own code" there is.
        return _is_under_any(realpath_filename, (_GX_PACKAGE_ROOT,))
    return _is_under_any(realpath_filename, (_GX_PACKAGE_ROOT, *_STDLIB_ROOTS))


def _is_under_any(realpath_filename: str, roots: Tuple[str, ...]) -> bool:
    return any(
        realpath_filename == root or realpath_filename.startswith(root + os.sep) for root in roots
    )
