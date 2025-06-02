"""Pip compatibility module for replacing pkg_resources.parse_requirements functionality."""

try:
    # pip >=20
    from pip._internal.network.session import PipSession
    from pip._internal.req import parse_requirements
except ImportError:
    try:
        # 10.0.0 <= pip <= 19.3.1
        from pip._internal.download import (
            PipSession,  # noqa: F401  # type: ignore[import-not-found]
        )
        from pip._internal.req import parse_requirements  # noqa: F401  # type: ignore[no-redef]
    except ImportError:
        # pip <= 9.0.3
        pass
