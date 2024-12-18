from __future__ import annotations

from great_expectations.compatibility.not_imported import NotImported

DATABRICKS_CONNECT_NOT_IMPORTED = NotImported(
    "databricks-connect is not installed, please 'pip install databricks-connect'"
)


# The following types are modeled after the following documentation that is part
# of the databricks package.
# tldr: SQLAlchemy application should (mostly) "just work" with Databricks.
# https://github.com/databricks/databricks-sql-python/blob/main/src/databricks/sqlalchemy/README.sqlalchemy.md
try:
    # Importing ENUM of every Databricks SQL Type that is shown here
    # https://docs.databricks.com/en/sql/language-manual/sql-ref-datatypes.html
    from databricks.sql.parameters.native import DatabricksSupportedType
except ImportError:
    DatabricksSupportedType = DATABRICKS_CONNECT_NOT_IMPORTED  # type: ignore[misc, assignment]
try:
    BIGINT = DatabricksSupportedType.BIGINT
except (ImportError, AttributeError):
    BIGINT = DATABRICKS_CONNECT_NOT_IMPORTED  # type: ignore[assignment]

try:
    BOOLEAN = DatabricksSupportedType.BOOLEAN
except (ImportError, AttributeError):
    BOOLEAN = DATABRICKS_CONNECT_NOT_IMPORTED  # type: ignore[assignment]

try:
    DATE = DatabricksSupportedType.DATE
except (ImportError, AttributeError):
    DATE = DATABRICKS_CONNECT_NOT_IMPORTED  # type: ignore[assignment]

try:
    from databricks.sqlalchemy._types import TIMESTAMP_NTZ as TIMESTAMP_NTZ  # noqa: PLC0414, RUF100
except (ImportError, AttributeError):
    TIMESTAMP_NTZ = DATABRICKS_CONNECT_NOT_IMPORTED  # type: ignore[misc, assignment]

try:
    DOUBLE = DatabricksSupportedType.DOUBLE
except (ImportError, AttributeError):
    DOUBLE = DATABRICKS_CONNECT_NOT_IMPORTED  # type: ignore[assignment]

try:
    FLOAT = DatabricksSupportedType.FLOAT
except (ImportError, AttributeError):
    FLOAT = DATABRICKS_CONNECT_NOT_IMPORTED  # type: ignore[assignment]

try:
    INT = DatabricksSupportedType.INT
except (ImportError, AttributeError):
    INT = DATABRICKS_CONNECT_NOT_IMPORTED  # type: ignore[assignment]

try:
    DECIMAL = DatabricksSupportedType.DECIMAL
except (ImportError, AttributeError):
    DECIMAL = DATABRICKS_CONNECT_NOT_IMPORTED  # type: ignore[assignment]

try:
    SMALLINT = DatabricksSupportedType.SMALLINT
except (ImportError, AttributeError):
    SMALLINT = DATABRICKS_CONNECT_NOT_IMPORTED  # type: ignore[assignment]

try:
    INTERVAL = DatabricksSupportedType.INTERVAL
except (ImportError, AttributeError):
    INTERVAL = DATABRICKS_CONNECT_NOT_IMPORTED  # type: ignore[assignment]

try:
    VOID = DatabricksSupportedType.VOID
except (ImportError, AttributeError):
    VOID = DATABRICKS_CONNECT_NOT_IMPORTED  # type: ignore[assignment]

try:
    SMALLINT = DatabricksSupportedType.SMALLINT
except (ImportError, AttributeError):
    SMALLINT = DATABRICKS_CONNECT_NOT_IMPORTED  # type: ignore[assignment]

try:
    from databricks.sqlalchemy._types import DatabricksStringType as STRING  # noqa: PLC0414, RUF100
except (ImportError, AttributeError):
    STRING = DATABRICKS_CONNECT_NOT_IMPORTED  # type: ignore[misc, assignment]

try:
    from databricks.sqlalchemy._types import TIMESTAMP as TIMESTAMP  # noqa: PLC0414, RUF100
except (ImportError, AttributeError):
    TIMESTAMP = DATABRICKS_CONNECT_NOT_IMPORTED  # type: ignore[misc, assignment]

try:
    from databricks.sqlalchemy._types import TINYINT as TINYINT  # noqa: PLC0414, RUF100
except (ImportError, AttributeError):
    TINYINT = DATABRICKS_CONNECT_NOT_IMPORTED  # type: ignore[misc, assignment]


class DATABRICKS_TYPES:
    """Namespace for Databricks dialect types"""

    BIGINT = BIGINT
    BOOLEAN = BOOLEAN
    DATE = DATE
    TIMESTAMP_NTZ = TIMESTAMP_NTZ
    DOUBLE = DOUBLE
    FLOAT = FLOAT
    INT = INT
    DECIMAL = DECIMAL
    SMALLINT = SMALLINT
    STRING = STRING
    TIMESTAMP = TIMESTAMP
    TINYINT = TINYINT
