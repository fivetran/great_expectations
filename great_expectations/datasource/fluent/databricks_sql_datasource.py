from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, List, Literal, Type, Union, overload
from urllib import parse

from great_expectations._docs_decorators import public_api
from great_expectations.compatibility import pydantic
from great_expectations.compatibility.pydantic import AnyUrl
from great_expectations.compatibility.sqlalchemy import (
    sqlalchemy as sa,
)
from great_expectations.compatibility.typing_extensions import override
from great_expectations.datasource.fluent.config_str import ConfigStr
from great_expectations.datasource.fluent.interfaces import (
    DataAsset,
    TestConnectionError,
)
from great_expectations.datasource.fluent.sql_datasource import (
    QueryAsset as SqlQueryAsset,
)
from great_expectations.datasource.fluent.sql_datasource import (
    SQLDatasource,
)
from great_expectations.datasource.fluent.sql_datasource import (
    TableAsset as SqlTableAsset,
)

if TYPE_CHECKING:
    from sqlalchemy.sql import quoted_name  # noqa: TID251 # type-checking only

    from great_expectations.compatibility import sqlalchemy
    from great_expectations.compatibility.pydantic.networks import Parts
    from great_expectations.core.config_provider import _ConfigurationProvider


def _parse_param_from_query_string(param: str, query: str) -> str | None:
    url_components = parse.urlparse(query)
    path = str(url_components.path)
    parse_results: dict[str, list[str]] = parse.parse_qs(path)
    path_results = parse_results.get(param, [])

    if not path_results:
        return None
    if len(path_results) > 1:
        raise ValueError(f"Only one `{param}` query entry is allowed")  # noqa: TRY003 # FIXME CoP
    return path_results[0]


class _UrlQueryError(pydantic.UrlError):
    """
    Custom Pydantic error for missing query in DatabricksDsn.
    """

    code = "url.query"
    msg_template = "URL query is invalid or missing"


class _UrlHttpPathError(pydantic.UrlError):
    """
    Custom Pydantic error for missing http_path in DatabricksDsn query.
    """

    code = "url.query.http_path"
    msg_template = "'http_path' query param is invalid or missing"


class _UrlCatalogError(pydantic.UrlError):
    """
    Custom Pydantic error for missing catalog in DatabricksDsn query.
    """

    code = "url.query.catalog"
    msg_template = "'catalog' query param is invalid or missing"


class _UrlSchemaError(pydantic.UrlError):
    """
    Custom Pydantic error for missing schema in DatabricksDsn query.
    """

    code = "url.query.schema"
    msg_template = "'schema' query param is invalid or missing"


class DatabricksDsn(AnyUrl):
    allowed_schemes = {
        "databricks",
    }
    query: str  # if query is not provided, validate_parts() will raise an error

    @classmethod
    @override
    def validate_parts(cls, parts: Parts, validate_port: bool = True) -> Parts:
        """
        Overridden to validate additional fields outside of scheme (which is performed by AnyUrl).
        """
        query = parts["query"]
        if query is None:
            raise _UrlQueryError()

        http_path = _parse_param_from_query_string(param="http_path", query=query)
        if http_path is None:
            raise _UrlHttpPathError()

        catalog = _parse_param_from_query_string(param="catalog", query=query)
        if catalog is None:
            raise _UrlCatalogError()

        schema = _parse_param_from_query_string(param="schema", query=query)
        if schema is None:
            raise _UrlSchemaError()

        return AnyUrl.validate_parts(parts=parts, validate_port=validate_port)

    @overload
    @classmethod
    def parse_url(
        cls, url: ConfigStr, config_provider: _ConfigurationProvider = ...
    ) -> DatabricksDsn: ...

    @overload
    @classmethod
    def parse_url(
        cls, url: str, config_provider: _ConfigurationProvider | None = ...
    ) -> DatabricksDsn: ...

    @classmethod
    def parse_url(
        cls, url: ConfigStr | str, config_provider: _ConfigurationProvider | None = None
    ) -> DatabricksDsn:
        if isinstance(url, ConfigStr):
            assert config_provider, "`config_provider` must be provided"
            url = url.get_config_value(config_provider=config_provider)
        parsed_url = pydantic.parse_obj_as(DatabricksDsn, url)
        return parsed_url


class DatabricksTableAsset(SqlTableAsset):
    @pydantic.validator("table_name")
    @override
    def _resolve_quoted_name(cls, table_name: str) -> str | quoted_name:
        import re
        
        table_name_is_quoted: bool = cls._is_bracketed_by_quotes(table_name)

        from great_expectations.compatibility import sqlalchemy

        if sqlalchemy.quoted_name:  # type: ignore[truthy-function] # FIXME CoP
            if isinstance(table_name, sqlalchemy.quoted_name):
                return table_name

            # Check if the table name needs special escaping for Databricks
            # This includes names that start with digits or contain special characters
            table_name_str = str(table_name)
            needs_quoting = (
                table_name_is_quoted or 
                re.match(r"^\d", table_name_str) or 
                re.search(r"[.\s\-#@]", table_name_str)
            )

            if needs_quoting:
                # Remove any existing quotes and add them back using sqlalchemy.quoted_name
                clean_table_name = table_name_str.strip('"').strip("'").strip("`")
                return sqlalchemy.quoted_name(
                    value=clean_table_name,
                    quote=True,
                )
            else:
                # Standard table that doesn't need special escaping
                return sqlalchemy.quoted_name(
                    value=table_name,
                    quote=False,
                )
        return table_name

    @pydantic.validator("schema_name")
    def _resolve_quoted_schema_name(cls, schema_name: str | None) -> str | quoted_name | None:
        if schema_name is None:
            return schema_name
            
        import re
        
        schema_name_is_quoted: bool = cls._is_bracketed_by_quotes(schema_name)

        from great_expectations.compatibility import sqlalchemy

        if sqlalchemy.quoted_name:  # type: ignore[truthy-function] # FIXME CoP
            if isinstance(schema_name, sqlalchemy.quoted_name):
                return schema_name

            # Check if the schema name needs special escaping for Databricks
            # This includes names that start with digits or contain special characters
            schema_name_str = str(schema_name)
            needs_quoting = (
                schema_name_is_quoted or 
                re.match(r"^\d", schema_name_str) or 
                re.search(r"[.\s\-#@]", schema_name_str)
            )

            if needs_quoting:
                # Remove any existing quotes and add them back using sqlalchemy.quoted_name
                clean_schema_name = schema_name_str.strip('"').strip("'").strip("`")
                return sqlalchemy.quoted_name(
                    value=clean_schema_name,
                    quote=True,
                )
            else:
                # Standard schema that doesn't need special escaping
                return sqlalchemy.quoted_name(
                    value=schema_name,
                    quote=False,
                )
        return schema_name

    @staticmethod
    @override
    def _is_bracketed_by_quotes(target: str) -> bool:
        """Returns True if the target string is bracketed by quotes.

        Arguments:
            target: A string to check if it is bracketed by quotes.

        Returns:
            True if the target string is bracketed by quotes.
        """
        # TODO: what todo with regular quotes? Error? Warn? "Fix"?
        return target.startswith("`") and target.endswith("`")


@public_api
class DatabricksSQLDatasource(SQLDatasource):
    """Adds a DatabricksSQLDatasource to the data context.

    Args:
        name: The name of this DatabricksSQL datasource.
        connection_string: The SQLAlchemy connection string used to connect to the Databricks SQL database.
            For example: "databricks://token:<token>@<host>:<port>?http_path=<http_path>&catalog=<catalog>&schema=<schema>""
        assets: An optional dictionary whose keys are TableAsset or QueryAsset names and whose values
            are TableAsset or QueryAsset objects.
    """  # noqa: E501 # FIXME CoP

    # class var definitions
    asset_types: ClassVar[List[Type[DataAsset]]] = [DatabricksTableAsset, SqlQueryAsset]

    type: Literal["databricks_sql"] = "databricks_sql"  # type: ignore[assignment] # FIXME CoP
    connection_string: Union[ConfigStr, DatabricksDsn]

    # These are instance var because ClassVars can't contain Type variables. See
    # https://peps.python.org/pep-0526/#class-and-instance-variable-annotations
    _TableAsset: Type[SqlTableAsset] = pydantic.PrivateAttr(DatabricksTableAsset)

    @override
    def test_connection(self, test_assets: bool = True) -> None:
        try:
            super().test_connection(test_assets)
        except TestConnectionError as e:
            nested_exception = None
            if e.__cause__ and e.__cause__.__cause__:
                nested_exception = e.__cause__.__cause__

            # Raise specific error informing how to install dependencies only if relevant
            if isinstance(nested_exception, sa.exc.NoSuchModuleError):
                raise TestConnectionError(  # noqa: TRY003 # FIXME CoP
                    "Could not connect to Databricks - please ensure you've installed necessary dependencies with `pip install great_expectations[databricks]`."  # noqa: E501 # FIXME CoP
                ) from e
            raise e  # noqa: TRY201 # FIXME CoP

    @override
    def _create_engine(self) -> sqlalchemy.Engine:
        model_dict = self.dict(
            exclude=self._get_exec_engine_excludes(),
            config_provider=self._config_provider,
        )

        connection_string = model_dict.pop("connection_string")
        # is connection_string was a ConfigStr it's parts will not have been validated yet
        if not isinstance(connection_string, DatabricksDsn):
            connection_string = DatabricksDsn.parse_url(
                url=connection_string, config_provider=self._config_provider
            )

        kwargs = model_dict.pop("kwargs", {})

        http_path = _parse_param_from_query_string(param="http_path", query=connection_string.query)
        assert http_path, "Presence of http_path query string is guaranteed due to prior validation"

        # Databricks connection is a bit finicky - the http_path portion of the connection string needs to be passed in connect_args  # noqa: E501 # FIXME CoP
        connect_args = {"http_path": http_path}
        return sa.create_engine(connection_string, connect_args=connect_args, **kwargs)
