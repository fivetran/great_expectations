from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Literal, Type, Union

from great_expectations._docs_decorators import public_api
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


@public_api
class RedshiftSSLModes(Enum):
    """
    Enum for the different SSL modes supported by the Redshift database.
    """

    DISABLE = "disable"
    ALLOW = "allow"
    PREFER = "prefer"
    REQUIRE = "require"
    VERIFY_CA = "verify-ca"
    VERIFY_FULL = "verify-full"


@public_api
class RedshiftConnectionDetails(BaseModel):
    """
    Information needed to connect to a Redshift database.
    """

    user: str
    password: Union[ConfigStr, str]
    host: str
    port: int
    database: str
    sslmode: RedshiftSSLModes


@public_api
class RedshiftDatasource(SQLDatasource):
    """Adds a Redshift datasource to the data context using psycopg2.

    Args:
        name: The name of this Redshift datasource.
        connection_string: The SQLAlchemy connection string used to connect to the Redshift database
            For example:
            "redshift+psycopg2://user:password@host.amazonaws.com:5439/database?sslmode=sslmode".
        assets: An optional dictionary whose keys are TableAsset or QueryAsset names and whose
            values are TableAsset or QueryAsset objects.
    """

    type: Literal["redshift"] = "redshift"  # type: ignore[assignment] # This is a hardcoded constant
    connection_string: Union[ConfigStr, dict, RedshiftConnectionDetails, RedshiftDsn]  # type: ignore[assignment] # Deviation from parent class as individual args are supported for connection

    @validator("connection_string", pre=True)
    def _build_connection_string_from_connection_details(
        cls, connection_string: dict | RedshiftConnectionDetails | str
    ) -> str:
        """
        If a dict or RedshiftConnectionDetails object is provided, construct the formatted
        connection string.
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
