import subprocess
import sys

import pytest

# module level markers
pytestmark = pytest.mark.unit


def test_importing_great_expectations_does_not_silence_warnings():
    """`import great_expectations` must not globally silence `warnings.warn(...)`
    for users who have not configured logging themselves.

    Several modules used to call `logging.captureWarnings(True)` at import time.
    That call is process-global: it redirects `warnings.showwarning` into the
    `logging` module, and if no handler is configured anywhere in the `logging`
    hierarchy (the common case for a script/notebook with no logging setup),
    Python's own `logging.captureWarnings` machinery attaches a `NullHandler` to
    the `py.warnings` logger, which silently swallows the warning instead of
    printing it. See GH issue #12067.

    This must be checked via a subprocess (inspecting real stderr output),
    because `pytest.warns`/`warnings.catch_warnings` install their own
    `showwarning` hook and would mask the regression.
    """
    result = subprocess.run(  # trusted, fixed argv, no shell
        [
            sys.executable,
            "-c",
            "import great_expectations; import warnings; "
            "warnings.warn('test warning from ge', UserWarning)",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.stderr, (
        "Expected the UserWarning to be printed to stderr, but stderr was empty. "
        "This means importing great_expectations silenced warnings for users "
        "with no logging configured."
    )
    assert "test warning from ge" in result.stderr
