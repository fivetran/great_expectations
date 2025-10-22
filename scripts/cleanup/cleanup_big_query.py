import logging
import sys

from great_expectations.compatibility.pydantic import BaseSettings
from great_expectations.compatibility.sqlalchemy import TextClause, create_engine

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))


class BigQueryConnectionConfig(BaseSettings):
    """Environment variables for BigQuery connection.
    These are injected in via CI, but when running locally, you may use your own credentials.
    GOOGLE_APPLICATION_CREDENTIALS must be kept secret
    """

    GE_TEST_GCP_PROJECT: str
    GE_TEST_BIGQUERY_DATASET: str
    GOOGLE_APPLICATION_CREDENTIALS: str

    @property
    def connection_string(self) -> str:
        return f"bigquery://{self.GE_TEST_GCP_PROJECT}/{self.GE_TEST_BIGQUERY_DATASET}?credentials_path={self.GOOGLE_APPLICATION_CREDENTIALS}"


# Schema patterns for different test types
SCHEMA_PATTERN_TEST = "^test_[a-z]{10}$"  # General SQL testing framework
SCHEMA_PATTERN_PY_VERSION = "^py3[0-9]{1,2}_i[a-f0-9]{32}$"  # Python version-specific test schemas
SCHEMA_FORMAT = f"{SCHEMA_PATTERN_TEST}|{SCHEMA_PATTERN_PY_VERSION}"


def cleanup_big_query(config: BigQueryConnectionConfig) -> None:
    engine = create_engine(url=config.connection_string)
    with engine.connect() as conn, conn.begin():
        results = conn.execute(
            TextClause(
                """
                SELECT 'DROP SCHEMA ' || schema_name || ' CASCADE;'
                FROM INFORMATION_SCHEMA.SCHEMATA
                WHERE REGEXP_CONTAINS(schema_name, :schema_format)
                AND creation_time < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR);
                """
            ),
            {"schema_format": SCHEMA_FORMAT},
        ).fetchall()
        if results:
            to_run = TextClause("\n".join([row[0] for row in results]))
            conn.execute(to_run)
            logger.info(f"Cleaned up {len(results)} BigQuery schema(s)")
        else:
            logger.info("No BigQuery schemas to clean up!")
    engine.dispose()


if __name__ == "__main__":
    config = BigQueryConnectionConfig()  # type: ignore[call-arg]  # pydantic populates from env vars
    cleanup_big_query(config)
