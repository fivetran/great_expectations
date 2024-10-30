from __future__ import annotations

from typing import Final

from great_expectations.compatibility.not_imported import NotImported

SNOWFLAKE_NOT_IMPORTED = NotImported(
    "snowflake connection components are not installed, please 'pip install snowflake-sqlalchemy snowflake-connector-python'"  # noqa: E501
)

try:
    import snowflake
except ImportError:
    snowflake = SNOWFLAKE_NOT_IMPORTED

try:
    from snowflake.sqlalchemy import URL
except ImportError:
    URL = SNOWFLAKE_NOT_IMPORTED

try:
    import snowflake.sqlalchemy as snowflakesqlalchemy
except (ImportError, AttributeError):
    snowflakesqlalchemy = SNOWFLAKE_NOT_IMPORTED

try:
    import snowflake.sqlalchemy.snowdialect as snowflakedialect
except (ImportError, AttributeError):
    snowflakedialect = SNOWFLAKE_NOT_IMPORTED

try:
    import snowflake.sqlalchemy.custom_types as snowflaketypes
except (ImportError, AttributeError):
    snowflaketypes = SNOWFLAKE_NOT_IMPORTED

IS_SNOWFLAKE_INSTALLED: Final[bool] = snowflake is not SNOWFLAKE_NOT_IMPORTED

try:
    from snowflake.sqlalchemy.custom_types import ARRAY as _ARRAY
except (ImportError, AttributeError):
    _ARRAY = SNOWFLAKE_NOT_IMPORTED

try:
    from snowflake.sqlalchemy.custom_types import BYTEINT as _BYTEINT
except (ImportError, AttributeError):
    _BYTEINT = SNOWFLAKE_NOT_IMPORTED


try:
    from snowflake.sqlalchemy.custom_types import CHARACTER as _CHARACTER
except (ImportError, AttributeError):
    _CHARACTER = SNOWFLAKE_NOT_IMPORTED


try:
    from snowflake.sqlalchemy.custom_types import DEC as _DEC
except (ImportError, AttributeError):
    _DEC = SNOWFLAKE_NOT_IMPORTED


try:
    from snowflake.sqlalchemy.custom_types import FIXED as _FIXED
except (ImportError, AttributeError):
    _FIXED = SNOWFLAKE_NOT_IMPORTED

try:
    from snowflake.sqlalchemy.custom_types import GEOGRAPHY as _GEOGRAPHY
except (ImportError, AttributeError):
    _GEOGRAPHY = SNOWFLAKE_NOT_IMPORTED


try:
    from snowflake.sqlalchemy.custom_types import GEOMETRY as _GEOMETRY
except (ImportError, AttributeError):
    _GEOMETRY = SNOWFLAKE_NOT_IMPORTED


try:
    from snowflake.sqlalchemy.custom_types import NUMBER as _NUMBER
except (ImportError, AttributeError):
    _NUMBER = SNOWFLAKE_NOT_IMPORTED


try:
    from snowflake.sqlalchemy.custom_types import OBJECT as _OBJECT
except (ImportError, AttributeError):
    _OBJECT = SNOWFLAKE_NOT_IMPORTED


try:
    from snowflake.sqlalchemy.custom_types import STRING as _STRING
except (ImportError, AttributeError):
    _STRING = SNOWFLAKE_NOT_IMPORTED


try:
    from snowflake.sqlalchemy.custom_types import TEXT as _TEXT
except (ImportError, AttributeError):
    _TEXT = SNOWFLAKE_NOT_IMPORTED


try:
    from snowflake.sqlalchemy.custom_types import TIMESTAMP_LTZ as _TIMESTAMP_LTZ
except (ImportError, AttributeError):
    _TIMESTAMP_LTZ = SNOWFLAKE_NOT_IMPORTED


try:
    from snowflake.sqlalchemy.custom_types import TIMESTAMP_NTZ as _TIMESTAMP_NTZ
except (ImportError, AttributeError):
    _TIMESTAMP_NTZ = SNOWFLAKE_NOT_IMPORTED


try:
    from snowflake.sqlalchemy.custom_types import TIMESTAMP_TZ as _TIMESTAMP_TZ
except (ImportError, AttributeError):
    _TIMESTAMP_TZ = SNOWFLAKE_NOT_IMPORTED


try:
    from snowflake.sqlalchemy.custom_types import TINYINT as _TINYINT
except (ImportError, AttributeError):
    _TINYINT = SNOWFLAKE_NOT_IMPORTED


try:
    from snowflake.sqlalchemy.custom_types import VARBINARY as _VARBINARY
except (ImportError, AttributeError):
    _VARBINARY = SNOWFLAKE_NOT_IMPORTED


try:
    from snowflake.sqlalchemy.custom_types import VARIANT as _VARIANT
except (ImportError, AttributeError):
    _VARIANT = SNOWFLAKE_NOT_IMPORTED

try:
    from snowflake.sqlalchemy.custom_types import DOUBLE as _DOUBLE
except (ImportError, AttributeError):
    _DOUBLE = SNOWFLAKE_NOT_IMPORTED





# the following types allow us to write a union of Snowflake types, which might not be installed
class ARRAY:
    ...


class NUMBER:
    ...


class STRING:
    ...


class DEC:
    ...

class SNOWFLAKE_TYPES:
    """Namespace for Snowflake dialect types."""

    ARRAY = ARRAY
    BYTEINT = BYTEINT
    CHARACTER = CHARACTER
    DEC = DEC
    DOUBLE = DOUBLE
    FIXED = FIXED
    GEOGRAPHY = GEOGRAPHY
    GEOMETRY = GEOMETRY
    NUMBER = NUMBER
    OBJECT = OBJECT
    STRING = STRING
    TEXT = TEXT
    TIMESTAMP_LTZ = TIMESTAMP_LTZ
    TIMESTAMP_NTZ = TIMESTAMP_NTZ
    TIMESTAMP_TZ = TIMESTAMP_TZ
    TINYINT = TINYINT
    VARBINARY = VARBINARY
    VARIANT = VARIANT