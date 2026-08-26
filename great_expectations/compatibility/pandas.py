from __future__ import annotations

from typing import Final

from great_expectations.compatibility.not_imported import NotImported

PANDAS_NOT_IMPORTED = NotImported(
    "pandas is not installed, please 'pip install pandas' or install great_expectations[pandas]"
)

try:
    import pandas
except ImportError:
    pandas = PANDAS_NOT_IMPORTED  # type: ignore[assignment] # FIXME CoP

IS_PANDAS_INSTALLED: Final[bool] = pandas is not PANDAS_NOT_IMPORTED
