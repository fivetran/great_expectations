import warnings

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning, module="_distutils_hack")

    try:
        # pip >=20
        from pip._internal.network.session import PipSession
        from pip._internal.req import parse_requirements
    except ImportError:
        try:
            # 10.0.0 <= pip <= 19.3.1
            from pip._internal.download import (  # type: ignore[import-not-found, no-redef]
                PipSession,  # noqa: F401
            )
            from pip._internal.req import parse_requirements  # noqa: F401  # type: ignore[no-redef]
        except ImportError:
            # pip <= 9.0.3
            pass
