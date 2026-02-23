import enum


class BackendDependencies(enum.Enum):
    AWS = "AWS"
    AWS_GLUE = "AWS_GLUE"
    ATHENA = "ATHENA"
    AZURE = "AZURE"
    BIGQUERY = "BIGQUERY"
    GCS = "GCS"
    MYSQL = "MYSQL"
    SQL_SERVER = "SQL_SERVER"
    PANDAS = "PANDAS"
    POSTGRESQL = "POSTGRESQL"
    REDSHIFT = "REDSHIFT"
    SPARK = "SPARK"
    SQLALCHEMY = "SQLALCHEMY"
    SNOWFLAKE = "SNOWFLAKE"
    TRINO = "TRINO"
    CLOUD = "CLOUD"
