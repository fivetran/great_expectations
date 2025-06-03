from __future__ import annotations

import warnings

from great_expectations.compatibility.not_imported import NotImported

PIP_NOT_IMPORTED = NotImported("An unsupported version of pip is installed")

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning, module="_distutils_hack")

    try:
        # pip >=20
        from pip._internal.network.session import PipSession
    except ImportError:
        try:
            # 10.0.0 <= pip <= 19.3.1
            from pip._internal.download import (  # type: ignore[import-not-found, no-redef]
                PipSession,
            )
        except ImportError:
            try:
                # pip <= 9.0.3
                from pip.download import (  # type: ignore[import-not-found, no-redef]
                    PipSession,
                )
            except ImportError:
                PipSession = PIP_NOT_IMPORTED  # type: ignore[misc, assignment]

    try:
        # pip >=20
        from pip._internal.req import parse_requirements
    except ImportError:
        try:
            # 10.0.0 <= pip <= 19.3.1
            from pip._internal.req import parse_requirements
        except ImportError:
            try:
                # pip <= 9.0.3
                from pip.req import (  # type: ignore[import-not-found, no-redef]
                    parse_requirements,
                )
            except ImportError:
                parse_requirements = PIP_NOT_IMPORTED
