from __future__ import annotations

from typing import Literal, Union

from great_expectations._docs_decorators import public_api
from great_expectations.datasource.fluent.config_str import ConfigStr
from great_expectations.datasource.fluent.sql_datasource import SQLDatasource


@public_api
class BigQueryDatasource(SQLDatasource):
    """Adds a bigquery datasource to the data context.
    Args:
        name: The name of this big query datasource.
        connection_string: The connection string used to connect to the database.
            For example: "bigquery://<gcp_project_name>/<bigquery_dataset>"
        assets: An optional dictionary whose keys are TableAsset or QueryAsset names and whose
            values are TableAsset or QueryAsset objects.
    """

    type: Literal["bigquery"] = "bigquery"  # type: ignore[assignment]
    connection_string: Union[ConfigStr, str]
