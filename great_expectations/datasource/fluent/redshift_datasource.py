from __future__ import annotations

import re
from typing import Final, Literal, Union

from great_expectations._docs_decorators import public_api
from great_expectations.datasource.fluent.config_str import ConfigStr
from great_expectations.datasource.fluent.sql_datasource import SQLDatasource

# from great_expectations.compatibility.pydantic.networks import MultiHostUrl, UrlConstraints

REDSHIFT_DSN_REGEX: Final[re.Pattern] = re.compile(r"redshift\+psycopg2://.*")


@public_api
class RedshiftDatasource(SQLDatasource):
    """Adds a redshift datasource to the data context.

    Args:
        name: The name of this redshift datasource.
        connection_string: The SQLAlchemy connection string used to connect to the redshift database.
            This will use a redshift dsn type.
            For example: "redshift+psycopg2://username@host.amazonaws.com:5439/database"
        assets: An optional dictionary whose keys are TableAsset or QueryAsset names and whose values
            are TableAsset or QueryAsset objects.
    """  # noqa: E501 # FIXME CoP

    type: Literal["redshift"] = "redshift"  # type: ignore[assignment] # FIXME CoP
    # TODO: add validation for connection string
    connection_string: Union[ConfigStr, str]


# Examples connecting using redshift pyscopg2
# See https://github.com/sqlalchemy-redshift/sqlalchemy-redshift
# conn=psycopg2.connect(
#   dbname = config['dbname'],
#   host = config['host']
#   port = config['port']
#   user = config['user']
#   password = config['password']
# )
# create_engine(f"postgresql://{REDSHIFT_USER}:{REDSHIFT_PASSWORD}@{REDSHIFT_HOST}:{REDSHIFT_PORT}/{REDSHIFT_DATABASE}")
# psycopg2.connect(f"postgresql://{REDSHIFT_USER}:{REDSHIFT_PASSWORD}@{REDSHIFT_HOST}:{REDSHIFT_PORT}/{REDSHIFT_DATABASE}")
