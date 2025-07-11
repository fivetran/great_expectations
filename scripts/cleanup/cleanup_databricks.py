import logging
import sys

from great_expectations.compatibility.pydantic import BaseSettings
from great_expectations.compatibility.sqlalchemy import TextClause, create_engine

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))


# SQL LIKE doesn't support regex quantifiers like {10}, so we expand it manually
# This is the SQL LIKE equivalent of the regex pattern SCHEMA_PATTERN = r"^test_[a-z]{10}$"
SCHEMA_LIKE_PATTERN = "test_" + "[a-z]" * 10
CATALOG_NAME = "ci"


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
        # Get schemas that match the test pattern using LIKE clause
        results = conn.execute(
            TextClause(
                f"""
                SHOW SCHEMAS FROM {CATALOG_NAME} LIKE '{SCHEMA_LIKE_PATTERN}'
                """
            )
        ).fetchall()

        if results:
            for row in results:
                schema_name = f"{CATALOG_NAME}.{row[0]}"
                try:
                    conn.execute(TextClause(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
                    logger.info(f"Dropped schema: {schema_name}")
                except Exception as e:
                    logger.error(f"Failed to drop schema {schema_name}: {e}")

            logger.info(f"Cleaned up {len(results)} Databricks schema(s)")
        else:
            logger.info("No Databricks schemas to clean up!")

    engine.dispose()


if __name__ == "__main__":
    config = DatabricksConnectionConfig()  # type: ignore[call-arg]  # pydantic populates from env vars
    cleanup_databricks(config)
