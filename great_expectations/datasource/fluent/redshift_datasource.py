from __future__ import annotations

from typing import Literal, Union

from great_expectations._docs_decorators import public_api
from great_expectations.compatibility.pydantic import PostgresDsn
from great_expectations.datasource.fluent.config_str import ConfigStr
from great_expectations.datasource.fluent.sql_datasource import SQLDatasource


@public_api
class RedshiftDatasource(SQLDatasource):
    """Adds a postgres datasource to the data context.

    Args:
        name: The name of this postgres datasource.
        connection_string: The SQLAlchemy connection string used to connect to the redshift database.
            This will use a postgres dsn type.
            For example: "postgresql+psycopg2://postgres:@localhost/test_database"
        assets: An optional dictionary whose keys are TableAsset or QueryAsset names and whose values
            are TableAsset or QueryAsset objects.
    """  # noqa: E501 # FIXME CoP

    type: Literal["redshift"] = "redshift"  # type: ignore[assignment] # FIXME CoP
    # We use the postgres dsn type here because redshift is a variant of postgres
    # and sqlalchemy-redshift uses pyscopg2 as the connector
    connection_string: Union[ConfigStr, PostgresDsn]


# Example connection using redshift pyscopg2
#               conn=psycopg2.connect(dbname = config['dbname'],
# host = config['host']
# port = config['port']
# user = config['user']
# password = config['password'])
# create_engine(f"postgresql://{REDSHIFT_USER}:{REDSHIFT_PASSWORD}@{REDSHIFT_HOST}:{REDSHIFT_PORT}/{REDSHIFT_DATABASE}")
# psycopg2.connect(f"postgresql://{REDSHIFT_USER}:{REDSHIFT_PASSWORD}@{REDSHIFT_HOST}:{REDSHIFT_PORT}/{REDSHIFT_DATABASE}")
