from __future__ import annotations

from typing import Final

from great_expectations.compatibility.not_imported import NotImported

SCIPY_NOT_IMPORTED = NotImported(
    "scipy is not installed, please 'pip install scipy' or install great_expectations[scipy]"
)

try:
    from scipy import stats
except ImportError:
    stats = SCIPY_NOT_IMPORTED  # FIXME CoP

IS_SCIPY_INSTALLED: Final[bool] = stats is not SCIPY_NOT_IMPORTED
