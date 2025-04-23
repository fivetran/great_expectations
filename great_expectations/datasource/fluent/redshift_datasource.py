from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Literal, Type, Union

from great_expectations.compatibility.pydantic import (
    AnyUrl,
    BaseModel,
    validator,
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

    user: str
    password: Union[ConfigStr, str]
    host: str
    port: int
    database: str
    sslmode: RedshiftSSLModes


class RedshiftDatasource(SQLDatasource):
    """Adds a Redshift datasource to the data context using psycopg2.

    Args:
        name: The name of this Redshift datasource.
        connection_string: The SQLAlchemy connection string used to connect to the Redshift
            database. This will use a redshift with psycopg2. For example:
            "redshift+psycopg2://user:password@host.amazonaws.com:5439/database?sslmode=sslmode".
            Alternatively, a RedshiftConnectionDetails object can be used.
        If connection_details is used, connection_string cannot also be provided.
        assets: An optional dictionary whose keys are TableAsset or QueryAsset names and whose
            values are TableAsset or QueryAsset objects.
    """

    type: Literal["redshift"] = "redshift"  # type: ignore[assignment] # This is a hardcoded constant
    connection_string: Union[RedshiftConnectionDetails, ConfigStr, RedshiftDsn]  # type: ignore[assignment] # Deviation from parent class as individual args are supported for connection

    @validator("connection_string", pre=True)
    def _build_connection_string_from_connection_details(
        cls, connection_string: str | dict | RedshiftConnectionDetails
    ) -> str:
        """
        If dict of connection details is provided, construct the connection_string.
        """
        if isinstance(connection_string, str):
            return connection_string

        if isinstance(connection_string, dict):
            connection_details = RedshiftConnectionDetails(**connection_string)
        elif isinstance(connection_string, RedshiftConnectionDetails):
            connection_details = connection_string
        else:
            raise TypeError("Invalid connection_string type: ", type(connection_string))  # noqa: TRY003
        connection_string = f"redshift+psycopg2://{connection_details.user}:{connection_details.password}@{connection_details.host}:{connection_details.port}/{connection_details.database}?sslmode={connection_details.sslmode.value}"
        return connection_string

    @property
    @override
    def execution_engine_type(self) -> Type[SqlAlchemyExecutionEngine]:
        """Returns the default execution engine type."""
        return RedshiftExecutionEngine
