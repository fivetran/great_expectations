import logging
import re
import sys

from great_expectations.compatibility.pydantic import BaseSettings
from great_expectations.compatibility.sqlalchemy import TextClause, create_engine

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))


class DatabricksConnectionConfig(BaseSettings):
    """Environment variables for Databricks connection.
    These are injected in via CI, but when running locally, you may use your own credentials.
    """

    DATABRICKS_TOKEN: str
    DATABRICKS_HOST: str
    DATABRICKS_HTTP_PATH: str

    @property
    def connection_string(self) -> str:
        return f"databricks://token:{self.DATABRICKS_TOKEN}@{self.DATABRICKS_HOST}?http_path={self.DATABRICKS_HTTP_PATH}&catalog=hive_metastore"


def cleanup_databricks(config: DatabricksConnectionConfig) -> None:
    engine = create_engine(url=config.connection_string)
    with engine.connect() as conn, conn.begin():
        # First, get all schemas that match our test pattern and are older than 2 hours
        results = conn.execute(
            TextClause(
                """
                SHOW SCHEMAS from ci
                """
            )
        ).fetchall()

        # Filter schemas that match our pattern (we'll do this in Python since Databricks SQL syntax varies)
        schema_pattern = re.compile(r"^test_[a-z]{10}$")
        schemas_to_drop = []

        for row in results:
            schema_name = row[0]  # Schema name is typically the first column
            if schema_pattern.match(schema_name):
                schemas_to_drop.append(schema_name)

        if schemas_to_drop:
            for schema_name in schemas_to_drop:
                formatted_schema_name = f"ci.{schema_name}"
                try:
                    conn.execute(TextClause(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
                    logger.info(f"Dropped schema: {schema_name}")
                except Exception as e:
                    logger.error(f"Failed to drop schema {formatted_schema_name}: {e}")

            logger.info(f"Cleaned up {len(schemas_to_drop)} Databricks schema(s)")
        else:
            logger.info("No Databricks schemas to clean up!")

    engine.dispose()


if __name__ == "__main__":
    config = DatabricksConnectionConfig()  # type: ignore[call-arg]  # pydantic populates from env vars
    cleanup_databricks(config)
