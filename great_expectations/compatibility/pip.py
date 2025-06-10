import warnings

from great_expectations.compatibility.not_imported import NotImported

PIP_NOT_IMPORTED = NotImported("An unsupported version of pip is installed")

with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning, module="_distutils_hack")

    try:
        from pip._internal.network.session import PipSession
    except ImportError:
        PipSession = PIP_NOT_IMPORTED  # type: ignore[misc, assignment]

try:
    from pip._internal.req import parse_requirements
except ImportError:
    parse_requirements = PIP_NOT_IMPORTED

try:
    from pip._internal.req.req_install import InstallRequirement
except ImportError:
    InstallRequirement = PIP_NOT_IMPORTED  # type: ignore[misc, assignment]
