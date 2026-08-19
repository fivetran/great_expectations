from __future__ import annotations

from typing import Any, Dict

from great_expectations.compatibility.not_imported import NotImported

BOTO_NOT_IMPORTED = NotImported(
    "AWS S3 connection components are not installed, please 'pip install boto3 botocore'"
)
REDSHIFT_NOT_IMPORTED = NotImported(
    "AWS Redshift connection component is not installed, please 'pip install sqlalchemy_redshift'"
)
ATHENA_NOT_IMPORTED = NotImported(
    "AWS Athena connection component is not installed, please 'pip install pyathena[SQLAlchemy]>=2.0.0,<3'"  # noqa: E501 # FIXME CoP
)

try:
    import boto3
except ImportError:
    boto3 = BOTO_NOT_IMPORTED

try:
    import botocore
except ImportError:
    botocore = BOTO_NOT_IMPORTED

try:
    from botocore.client import Config
except ImportError:
    Config = BOTO_NOT_IMPORTED

try:
    from botocore import exceptions
except ImportError:
    exceptions = BOTO_NOT_IMPORTED


def get_great_expectations_version() -> str:
    """Return the Great Expectations version reported by the running package."""
    # Imported inside the function: `great_expectations/__init__.py` pulls in this
    # module while initializing, so a module-level import would couple this module
    # to `__version__` being bound before that point.
    from great_expectations import __version__

    return __version__


def get_s3_boto3_options(boto3_options: Dict[str, Any]) -> Dict[str, Any]:
    """Return boto3 client options with a ``great-expectations`` agent suffix.

    Works with Amazon S3 and any S3-compatible object store (for example
    Backblaze B2, Cloudflare R2, or MinIO). A caller-supplied ``config`` and
    ``endpoint_url`` are preserved; the suffix is appended to an existing agent
    string rather than replacing it.

    Applying the suffix is idempotent: options that already carry it are
    returned unchanged, so passing a result back through this function does not
    repeat the suffix.
    """
    suffix = f"great-expectations/{get_great_expectations_version()}"
    options = dict(boto3_options)

    if isinstance(Config, NotImported):
        return options

    config = options.get("config")
    if config is not None and not isinstance(config, Config):
        return options

    existing = getattr(config, "user_agent_extra", None) if config is not None else None
    agents = existing.split() if existing else []
    if suffix in agents:
        return options

    agents.append(suffix)
    user_agent_extra = " ".join(agents)

    if config is not None:
        options["config"] = config.merge(Config(user_agent_extra=user_agent_extra))
    else:
        options["config"] = Config(user_agent_extra=user_agent_extra)

    return options


try:
    import sqlalchemy_redshift
except ImportError:
    sqlalchemy_redshift = REDSHIFT_NOT_IMPORTED

try:
    from sqlalchemy_redshift import dialect as redshiftdialect
except (ImportError, AttributeError):
    redshiftdialect = REDSHIFT_NOT_IMPORTED

try:
    from sqlalchemy_redshift.dialect import CHAR
except (ImportError, AttributeError):
    CHAR = REDSHIFT_NOT_IMPORTED

try:
    from sqlalchemy_redshift.dialect import VARCHAR
except (ImportError, AttributeError):
    VARCHAR = REDSHIFT_NOT_IMPORTED

try:
    from sqlalchemy_redshift.dialect import INTEGER
except (ImportError, AttributeError):
    INTEGER = REDSHIFT_NOT_IMPORTED

try:
    from sqlalchemy_redshift.dialect import SMALLINT
except (ImportError, AttributeError):
    SMALLINT = REDSHIFT_NOT_IMPORTED

try:
    from sqlalchemy_redshift.dialect import BIGINT
except (ImportError, AttributeError):
    BIGINT = REDSHIFT_NOT_IMPORTED

try:
    from sqlalchemy_redshift.dialect import TIMESTAMP
except (ImportError, AttributeError):
    TIMESTAMP = REDSHIFT_NOT_IMPORTED

try:
    from sqlalchemy_redshift.dialect import DATE
except (ImportError, AttributeError):
    DATE = REDSHIFT_NOT_IMPORTED

try:
    from sqlalchemy_redshift.dialect import DOUBLE_PRECISION
except (ImportError, AttributeError):
    DOUBLE_PRECISION = REDSHIFT_NOT_IMPORTED

try:
    from sqlalchemy_redshift.dialect import BOOLEAN
except (ImportError, AttributeError):
    BOOLEAN = REDSHIFT_NOT_IMPORTED

try:
    from sqlalchemy_redshift.dialect import DECIMAL
except (ImportError, AttributeError):
    DECIMAL = REDSHIFT_NOT_IMPORTED

try:
    from sqlalchemy_redshift.dialect import GEOMETRY
except (ImportError, AttributeError):
    GEOMETRY = REDSHIFT_NOT_IMPORTED

try:
    from sqlalchemy_redshift.dialect import SUPER
except (ImportError, AttributeError):
    SUPER = REDSHIFT_NOT_IMPORTED

try:
    import pyathena  # type: ignore[import-not-found] # FIXME CoP
except ImportError:
    pyathena = ATHENA_NOT_IMPORTED

try:
    from pyathena import sqlalchemy_athena
except (ImportError, AttributeError):
    sqlalchemy_athena = ATHENA_NOT_IMPORTED

try:
    from pyathena.sqlalchemy_athena import (  # type: ignore[import-not-found] # FIXME CoP
        types as athenatypes,
    )
except (ImportError, AttributeError):
    athenatypes = ATHENA_NOT_IMPORTED


class REDSHIFT_TYPES:
    """Namespace for Redshift dialect types."""

    CHAR = CHAR
    VARCHAR = VARCHAR
    INTEGER = INTEGER
    SMALLINT = SMALLINT
    BIGINT = BIGINT
    TIMESTAMP = TIMESTAMP
    DATE = DATE
    DOUBLE_PRECISION = DOUBLE_PRECISION
    BOOLEAN = BOOLEAN
    DECIMAL = DECIMAL
    GEOMETRY = GEOMETRY
    SUPER = SUPER
