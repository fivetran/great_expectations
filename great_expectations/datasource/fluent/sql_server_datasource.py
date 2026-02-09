from __future__ import annotations

from typing import TYPE_CHECKING, Final, Literal, Union
from urllib.parse import quote, quote_plus

from great_expectations.compatibility import pydantic
from great_expectations.compatibility.pydantic import Field
from great_expectations.compatibility.sqlalchemy import sqlalchemy as sa
from great_expectations.compatibility.typing_extensions import override
from great_expectations.datasource.fluent.config_str import ConfigStr
from great_expectations.datasource.fluent.sql_datasource import (
    FluentBaseModel,
    SQLDatasource,
)

if TYPE_CHECKING:
    from great_expectations.compatibility import sqlalchemy


class SqlServerDsn(pydantic.AnyUrl):
    allowed_schemes = {"mssql+pyodbc"}
    host_required = True

    @classmethod
    def from_url(cls, url: str) -> SqlServerDsn:
        """Validate and return a SqlServerDsn from a raw URL string."""

        class _Model(pydantic.BaseModel):
            url: SqlServerDsn

        return _Model(url=url).url  # type: ignore[arg-type] # pydantic coerces str to SqlServerDsn


_ENCRYPT_VALUE_MAP: Final[dict[str, str]] = {
    "Mandatory": "yes",
    "Optional": "no",
    "Strict": "strict",
}


class _SQLServerConnectionDetailsBase(FluentBaseModel):
    """Base class with common connection fields."""

    host: str
    port: int = 1433
    database: str
    schema_: str = Field(..., alias="schema")
    driver: str = "ODBC Driver 18 for SQL Server"
    encrypt: Literal["Mandatory", "Optional", "Strict"] = "Mandatory"

    class Config:
        allow_population_by_field_name = (
            True  # this allows us to use the alias "schema" for the "schema_" field
        )


class SQLServerAuthConnectionDetails(_SQLServerConnectionDetailsBase):
    """SQL Server authentication (username/password)."""

    authentication: Literal["SQL Server"] = "SQL Server"
    username: str
    password: Union[ConfigStr, str]


class SQLServerDatasource(SQLDatasource):
    """Adds a SQL Server datasource to the data context.

    Args:
        name: The name of this SQL Server datasource.
        connection_string: Structured connection details for SQL Server.
        assets: An optional dictionary whose keys are TableAsset or QueryAsset names and whose
            values are TableAsset or QueryAsset objects.
    """

    type: Literal["sql_server"] = "sql_server"  # type: ignore[assignment]
    connection_string: SQLServerAuthConnectionDetails  # type: ignore[assignment]  # Raw connection strings are not supported

    @property
    def schema_(self) -> str:
        return self.connection_string.schema_

    @override
    def _create_engine(self) -> sqlalchemy.Engine:
        url = self._build_connection_string()
        return sa.create_engine(url, **self.kwargs)

    def _build_connection_string(self) -> SqlServerDsn:
        """Convert connection details to a validated ``mssql+pyodbc://`` URL."""
        details = self.connection_string
        password = details.password
        if isinstance(password, ConfigStr) and self._config_provider:
            resolved_password = password.get_config_value(self._config_provider)
        else:
            resolved_password = str(password)

        # quote() for userinfo (spaces → %20), quote_plus() for query params (spaces → +)
        username = quote(details.username, safe="")
        encoded_password = quote(resolved_password, safe="")
        driver = quote_plus(details.driver)
        encrypt = _ENCRYPT_VALUE_MAP.get(details.encrypt, "yes")

        url = (
            f"mssql+pyodbc://{username}:{encoded_password}"
            f"@{details.host}:{details.port}/{details.database}"
            f"?driver={driver}&Encrypt={encrypt}"
        )
        return SqlServerDsn.from_url(url)
