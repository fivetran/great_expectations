from __future__ import annotations

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
