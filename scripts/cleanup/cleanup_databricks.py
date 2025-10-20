import logging
import sys

from great_expectations.compatibility.pydantic import BaseSettings
from great_expectations.compatibility.sqlalchemy import TextClause, create_engine

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

# Schema patterns for different test types
SCHEMA_PATTERN_10_CHAR = "test_[a-z]{10}"  # General SQL testing framework
SCHEMA_PATTERN_8_CHAR = "test_[a-f0-9]{8}"  # Databricks-specific tests
SCHEMA_PATTERN_PY_VERSION = "py3[0-9]{1,2}_i[a-f0-9]{32}"  # Python version-specific test schemas
SCHEMA_PATTERN = f"{SCHEMA_PATTERN_10_CHAR}|{SCHEMA_PATTERN_8_CHAR}|{SCHEMA_PATTERN_PY_VERSION}"

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
        return f"databricks://token:{self.DATABRICKS_TOKEN}@{self.DATABRICKS_HOST}?http_path={self.DATABRICKS_HTTP_PATH}&catalog=ci"


def cleanup_databricks(config: DatabricksConnectionConfig) -> None:
    engine = create_engine(url=config.connection_string)

    with engine.connect() as conn, conn.begin():
        results = conn.execute(
            TextClause(
                """
            SELECT catalog_name, schema_name, created
            FROM information_schema.schemata
            WHERE catalog_name = :catalog_name
            AND schema_name REGEXP :schema_pattern
            AND created < CURRENT_TIMESTAMP() - INTERVAL 2 HOUR
            ORDER BY created DESC
            """
            ),
            {"catalog_name": CATALOG_NAME, "schema_pattern": SCHEMA_PATTERN},
        ).fetchall()

        if not results:
            logger.info("No old schemas found to clean up")
            return

        for row in results:
            catalog_name, schema_name, _ = row
            full_schema_name = f"{catalog_name}.{schema_name}"

            try:
                conn.execute(TextClause(f"DROP SCHEMA IF EXISTS {full_schema_name} CASCADE"))
                logger.info(f"Dropped schema: {full_schema_name}")
            except Exception:
                logger.exception(f"Failed to drop schema {full_schema_name}")

        logger.info(f"Cleaned up {len(results)} Databricks schema(s)")

    engine.dispose()


if __name__ == "__main__":
    config = DatabricksConnectionConfig()  # type: ignore[call-arg]  # pydantic populates from env vars
    cleanup_databricks(config)
