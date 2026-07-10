from __future__ import annotations

from great_expectations.compatibility.not_imported import NotImported

PYARROW_NOT_IMPORTED = NotImported("pyarrow is not installed, please 'pip install pyarrow'")

try:
    import pyarrow
except ImportError:
    # The assignment error only occurs when pyarrow is installed, so the ignore is
    # env-dependent; unused-ignore keeps --warn-unused-ignores quiet when it is not.
    pyarrow = PYARROW_NOT_IMPORTED  # type: ignore[assignment,unused-ignore]
