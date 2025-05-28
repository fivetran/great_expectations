from __future__ import annotations

from great_expectations.compatibility.not_imported import NotImported

POSTGRESQL_NOT_IMPORTED = NotImported(
    "postgresql connection components are not installed, please 'pip install psycopg2'"
)

try:
    import psycopg2  # noqa: F401 # FIXME CoP
    import sqlalchemy.dialects.postgresql as postgresqltypes
except ImportError:
    postgresqltypes = POSTGRESQL_NOT_IMPORTED  # type: ignore[assignment] # FIXME CoP

try:
    from sqlalchemy.dialects.postgresql import TEXT
except (ImportError, AttributeError):
    TEXT = POSTGRESQL_NOT_IMPORTED  # type: ignore[misc, assignment] # FIXME CoP

try:
    from sqlalchemy.dialects.postgresql import CHAR
except (ImportError, AttributeError):
    CHAR = POSTGRESQL_NOT_IMPORTED  # type: ignore[misc, assignment] # FIXME CoP

try:
    from sqlalchemy.dialects.postgresql import INTEGER
except (ImportError, AttributeError):
    INTEGER = POSTGRESQL_NOT_IMPORTED  # type: ignore[misc, assignment] # FIXME CoP

try:
    from sqlalchemy.dialects.postgresql import SMALLINT
except (ImportError, AttributeError):
    SMALLINT = POSTGRESQL_NOT_IMPORTED  # type: ignore[misc, assignment] # FIXME CoP

try:
    from sqlalchemy.dialects.postgresql import BIGINT
except (ImportError, AttributeError):
    BIGINT = POSTGRESQL_NOT_IMPORTED  # type: ignore[misc, assignment] # FIXME CoP

try:
    from sqlalchemy.dialects.postgresql import TIMESTAMP
except (ImportError, AttributeError):
    TIMESTAMP = POSTGRESQL_NOT_IMPORTED  # type: ignore[misc, assignment] # FIXME CoP

try:
    from sqlalchemy.dialects.postgresql import DATE
except (ImportError, AttributeError):
    DATE = POSTGRESQL_NOT_IMPORTED  # type: ignore[misc, assignment] # FIXME CoP

try:
    from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION
except (ImportError, AttributeError):
    DOUBLE_PRECISION = POSTGRESQL_NOT_IMPORTED  # type: ignore[misc, assignment] # FIXME CoP

try:
    from sqlalchemy.dialects.postgresql import BOOLEAN
except (ImportError, AttributeError):
    BOOLEAN = POSTGRESQL_NOT_IMPORTED  # type: ignore[misc, assignment] # FIXME CoP

try:
    from sqlalchemy.dialects.postgresql import NUMERIC
except (ImportError, AttributeError):
    NUMERIC = POSTGRESQL_NOT_IMPORTED  # type: ignore[misc, assignment] # FIXME CoP


class POSTGRESQL_TYPES:
    """Namespace for PostgreSQL dialect types."""

    TEXT = TEXT
    CHAR = CHAR
    INTEGER = INTEGER
    SMALLINT = SMALLINT
    BIGINT = BIGINT
    TIMESTAMP = TIMESTAMP
    DATE = DATE
    DOUBLE_PRECISION = DOUBLE_PRECISION
    BOOLEAN = BOOLEAN
    NUMERIC = NUMERIC
