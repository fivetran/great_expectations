from __future__ import annotations

from great_expectations.compatibility.not_imported import NotImported

DATABRICKS_CONNECT_NOT_IMPORTED = NotImported(
    "databricks-connect is not installed, please 'pip install databricks-connect'"
)

# The following types are modeled after the following documentation that is part
# of the databricks package.
# tldr: SQLAlchemy application should (mostly) "just work" with Databricks,
# other than the exceptions below
# https://github.com/databricks/databricks-sql-python/blob/main/src/databricks/sqlalchemy/README.sqlalchemy.md

try:
    from databricks.sqlalchemy._types import (
        TIMESTAMP_NTZ as TIMESTAMP_NTZ,  # noqa: PLC0414, RUF100 # FIXME CoP
    )
except (ImportError, AttributeError):
    TIMESTAMP_NTZ = DATABRICKS_CONNECT_NOT_IMPORTED  # type: ignore[misc, assignment] # FIXME CoP

try:
    from databricks.sqlalchemy._types import (
        DatabricksStringType as STRING,  # noqa: PLC0414, RUF100 # FIXME CoP
    )
except (ImportError, AttributeError):
    STRING = DATABRICKS_CONNECT_NOT_IMPORTED  # type: ignore[misc, assignment] # FIXME CoP

try:
    from databricks.sqlalchemy._types import (
        TIMESTAMP as TIMESTAMP,  # noqa: PLC0414, RUF100 # FIXME CoP
    )
except (ImportError, AttributeError):
    TIMESTAMP = DATABRICKS_CONNECT_NOT_IMPORTED  # type: ignore[misc, assignment] # FIXME CoP

try:
    from databricks.sqlalchemy._types import TINYINT as TINYINT  # noqa: PLC0414, RUF100 # FIXME CoP
except (ImportError, AttributeError):
    TINYINT = DATABRICKS_CONNECT_NOT_IMPORTED  # type: ignore[misc, assignment] # FIXME CoP


class DATABRICKS_TYPES:
    """Namespace for Databricks dialect types"""

    TIMESTAMP_NTZ = TIMESTAMP_NTZ
    STRING = STRING
    TINYINT = TINYINT
    TIMESTAMP = TIMESTAMP
