from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Literal, Type, Union

from great_expectations.compatibility.pydantic import (
    AnyUrl,
    BaseModel,
    StrictInt,
    StrictStr,
    root_validator,
)
from great_expectations.compatibility.typing_extensions import override
from great_expectations.datasource.fluent.config_str import ConfigStr
from great_expectations.datasource.fluent.sql_datasource import SQLDatasource
from great_expectations.execution_engine.redshift_execution_engine import RedshiftExecutionEngine

if TYPE_CHECKING:
    from great_expectations.execution_engine.sqlalchemy_execution_engine import (
        SqlAlchemyExecutionEngine,
    )


class RedshiftDsn(AnyUrl):
    allowed_schemes = {
        "redshift+psycopg2",
    }


class RedshiftSSLModes(Enum):
    DISABLE = "disable"
    ALLOW = "allow"
    PREFER = "prefer"
    REQUIRE = "require"
    VERIFY_CA = "verify-ca"
    VERIFY_FULL = "verify-full"


class RedshiftConnectionDetails(BaseModel):
    """
    Information needed to connect to a Redshift database.
    Alternative to a connection string.
    """

    username: StrictStr
    password: Union[ConfigStr, StrictStr]
    host: StrictStr
    port: StrictInt
    database: StrictStr
    ssl_mode: RedshiftSSLModes


class RedshiftDatasource(SQLDatasource):
    """Adds a Redshift datasource to the data context using psycopg2.

    Args:
        name: The name of this Redshift datasource.
        connection_string: The SQLAlchemy connection string used to connect to the Redshift
            database. This will use a redshift with psycopg2. For example:
            "redshift+psycopg2://username@host.amazonaws.com:5439/database"
        connection_details: A RedshiftConnectionDetails object defining the connection details.
        If connection_details is used, connection_string cannot also be provided.
        assets: An optional dictionary whose keys are TableAsset or QueryAsset names and whose
            values are TableAsset or QueryAsset objects.
    """

    type: Literal["redshift"] = "redshift"  # type: ignore[assignment] # This is a hardcoded constant
    connection_string: Union[ConfigStr, RedshiftDsn]

    @root_validator(pre=True, allow_reuse=True)
    def _build_connection_string_from_connection_details(cls, values: dict) -> dict:
        """
        If connection_details is provided, use them to construct the connection_string.
        """
        connection_string, connection_details = (
            values.get("connection_string"),
            values.get("connection_details"),
        )
        if connection_details is not None and connection_string is not None:
            raise ValueError("Cannot provide both connection_details and connection_string")  # noqa: TRY003
        if connection_details is not None:
            connection_string_from_details = f"redshift+psycopg2://{connection_details.username}:{connection_details.password}@{connection_details.host}:{connection_details.port}/{connection_details.database}?sslmode={connection_details.ssl_mode.value}"
            values["connection_string"] = connection_string_from_details
            del values["connection_details"]
        return values

    @property
    @override
    def execution_engine_type(self) -> Type[SqlAlchemyExecutionEngine]:
        """Returns the default execution engine type."""
        return RedshiftExecutionEngine
