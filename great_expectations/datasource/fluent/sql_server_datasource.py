from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, Literal, Union
from urllib.parse import quote, quote_plus

from typing_extensions import Annotated

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
    from great_expectations.execution_engine import SqlAlchemyExecutionEngine


class SqlServerDsn(pydantic.AnyUrl):
    allowed_schemes = {"mssql+pyodbc"}
    host_required = True

    @classmethod
    def from_url(cls, url: str) -> SqlServerDsn:
        """Validate and return a SqlServerDsn from a raw URL string."""

        class _Model(pydantic.BaseModel):
            url: SqlServerDsn

        return _Model(url=url).url  # type: ignore[arg-type] # pydantic coerces str to SqlServerDsn


_MUTUALLY_EXCLUSIVE_MSG: Final[str] = (
    "Provide either a connection_string object or individual keyword arguments, not both."
)

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

    def get_query_params(self) -> dict[str, str]:
        """Return query parameters for the connection URL."""
        return {
            "driver": quote_plus(self.driver),  # quote_plus (spaces → +)
            "Encrypt": _ENCRYPT_VALUE_MAP.get(self.encrypt, "yes"),
        }


class SQLServerAuthConnectionDetails(_SQLServerConnectionDetailsBase):
    """SQL Server authentication (username/password)."""

    authentication: Literal["SQL Server"] = "SQL Server"
    username: str
    password: Union[ConfigStr, str]


class AzureADPasswordAuthConnectionDetails(_SQLServerConnectionDetailsBase):
    """Azure AD Password authentication."""

    authentication: Literal["Azure AD Password"] = "Azure AD Password"
    username: str
    password: Union[ConfigStr, str]

    @override
    def get_query_params(self) -> dict[str, str]:
        params = super().get_query_params()
        params["Authentication"] = "ActiveDirectoryPassword"
        return params


# Discriminated union using the authentication field (Pydantic v1 syntax)
SQLServerConnectionDetails = Annotated[
    Union[
        SQLServerAuthConnectionDetails,
        AzureADPasswordAuthConnectionDetails,
    ],
    Field(discriminator="authentication"),
]


_CONNECTION_DETAIL_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "schema",  # alias for schema_
        *_SQLServerConnectionDetailsBase.__fields__.keys(),
        *SQLServerAuthConnectionDetails.__fields__.keys(),
        *AzureADPasswordAuthConnectionDetails.__fields__.keys(),
    }
)


class SQLServerDatasource(SQLDatasource):
    """Adds a SQL Server datasource to the data context.

    Args:
        name: The name of this SQL Server datasource.
        connection_string: Structured connection details for SQL Server.
            Alternatively, pass connection detail fields (host, database, schema,
            username, password, etc.) as keyword arguments directly.
        assets: An optional dictionary whose keys are TableAsset or QueryAsset names and whose
            values are TableAsset or QueryAsset objects.
    """

    type: Literal["sql_server"] = "sql_server"  # type: ignore[assignment]
    connection_string: SQLServerConnectionDetails  # type: ignore[assignment]  # Raw connection strings are not supported

    @pydantic.root_validator(pre=True)
    def _convert_root_connection_detail_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Pack top-level connection detail kwargs into ``connection_string``."""
        connection_string = values.get("connection_string")
        connection_details: dict[str, Any] = {}
        for field_name in list(values.keys()):
            if field_name in _CONNECTION_DETAIL_FIELDS:
                if connection_string is not None:
                    raise ValueError(_MUTUALLY_EXCLUSIVE_MSG)
                connection_details[field_name] = values.pop(field_name)
        if connection_details:
            connection_details.setdefault("authentication", "SQL Server")
            values["connection_string"] = connection_details
        return values

    @property
    def schema_(self) -> str:
        return self.connection_string.schema_

    @override
    def get_execution_engine(self) -> SqlAlchemyExecutionEngine:
        current_execution_engine_kwargs = self.dict(
            exclude=self._get_exec_engine_excludes(),
            config_provider=self._config_provider,
            exclude_unset=False,
        )
        if (
            current_execution_engine_kwargs != self._cached_execution_engine_kwargs
            or not self._execution_engine
        ):
            self._cached_execution_engine_kwargs = current_execution_engine_kwargs
            engine_kwargs = current_execution_engine_kwargs.pop("kwargs", {})
            current_execution_engine_kwargs.pop("connection_string", None)
            engine = self._create_engine()
            self._execution_engine = self._execution_engine_type()(
                engine=engine,
                **current_execution_engine_kwargs,
                **engine_kwargs,
            )
        return self._execution_engine

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

        # quote() for userinfo (spaces → %20)
        username = quote(details.username, safe="")
        password = quote(resolved_password, safe="")

        query_params = details.get_query_params()
        query_string = "&".join(f"{k}={v}" for k, v in query_params.items())

        url = (
            f"mssql+pyodbc://{username}:{password}"
            f"@{details.host}:{details.port}/{details.database}"
            f"?{query_string}"
        )
        return SqlServerDsn.from_url(url)
