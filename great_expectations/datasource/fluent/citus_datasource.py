from __future__ import annotations

from typing import Literal, Union

from great_expectations._docs_decorators import public_api
from great_expectations.compatibility.pydantic import PostgresDsn
from great_expectations.datasource.fluent.config_str import ConfigStr
from great_expectations.datasource.fluent.sql_datasource import SQLDatasource


@public_api
class CitusDatasource(SQLDatasource):
    """Adds a citus datasource to the data context.

    Args:
        name: The name of this citus datasource.
        connection_string: The connection string used to connect to the postgres database.
            For example: "postgresql+psycopg2://<username>:<password>@<coordinator_hostname>:<port>/<database_name>"
        assets: An optional dictionary whose keys are TableAsset or QueryAsset names and whose
            values are TableAsset or QueryAsset objects.
    """

    type: Literal["citus"] = "citus"  # type: ignore[assignment]
    connection_string: Union[ConfigStr, PostgresDsn]
