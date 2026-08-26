"""Utilities and imports for ensuring compatibility with different versions
of numpy that are supported by great expectations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from packaging import version

from great_expectations.compatibility.not_imported import NotImported

NUMPY_NOT_IMPORTED = NotImported(
    "numpy is not installed, please 'pip install numpy' or install great_expectations[numpy]"
)

try:
    import numpy as np
except ImportError:
    np = NUMPY_NOT_IMPORTED  # type: ignore[assignment] # FIXME CoP

IS_NUMPY_INSTALLED: Final[bool] = np is not NUMPY_NOT_IMPORTED

if TYPE_CHECKING:
    # needed until numpy min version 1.20
    from numpy import typing as npt


def numpy_quantile(
    a: npt.NDArray, q: float, method: str, axis: int | None = None
) -> np.float64 | npt.NDArray:
    """
    As of NumPy 1.21.0, the 'interpolation' arg in quantile() has been renamed to `method`.
    Source: https://numpy.org/doc/stable/reference/generated/numpy.quantile.html
    """
    quantile: npt.NDArray
    if version.parse(np.__version__) >= version.parse("1.22.0"):
        quantile = np.quantile(  # type: ignore[call-overload] # FIXME CoP
            a=a,
            q=q,
            axis=axis,
            method=method,
        )
    else:
        quantile = np.quantile(  # type: ignore[call-overload] # FIXME CoP
            a=a,
            q=q,
            axis=axis,
            interpolation=method,
        )

    return quantile
