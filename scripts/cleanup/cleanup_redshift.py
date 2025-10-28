import logging
import sys

from great_expectations.compatibility.pydantic import BaseSettings
from great_expectations.compatibility.sqlalchemy import TextClause, create_engine

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))


class RedshiftConnectionConfig(BaseSettings):
    """Environment variables for Redshift connection.
    These are injected in via CI, but when running locally, you may use your own credentials.
    """

    REDSHIFT_HOST: str
    REDSHIFT_PORT: int
    REDSHIFT_USERNAME: str
    REDSHIFT_PASSWORD: str
    REDSHIFT_DATABASE: str
    REDSHIFT_SSLMODE: str

    @property
    def connection_string(self) -> str:
        return (
            f"redshift+psycopg2://{self.REDSHIFT_USERNAME}:{self.REDSHIFT_PASSWORD}@"
            f"{self.REDSHIFT_HOST}:{self.REDSHIFT_PORT}/{self.REDSHIFT_DATABASE}?"
            f"sslmode={self.REDSHIFT_SSLMODE}"
        )


TABLE_PATTERN = "expectation_test_table_%"


def cleanup_redshift(config: RedshiftConnectionConfig) -> None:
    engine = create_engine(url=config.connection_string)
    with engine.connect() as conn, conn.begin():
        results = conn.execute(
            TextClause(
                """
                SELECT 'DROP TABLE IF EXISTS ' || t.schemaname || '.' || t.tablename || ';'
                FROM pg_tables t
                JOIN SVV_TABLE_INFO i ON t.schemaname = i.schema AND t.tablename = i.table
                WHERE t.tablename LIKE :table_pattern
                AND i.create_time < DATEADD(hour, -1, GETDATE())
                """
            ),
            {"table_pattern": TABLE_PATTERN},
        ).fetchall()

        if results:
            to_run = TextClause("\n".join([row[0] for row in results]))
            conn.execute(to_run)

            logger.info(f"Cleaned up {len(results)} Redshift tables older than 2 hours")
        else:
            logger.info("No Redshift tables older than 2 hours to clean up!")
    engine.dispose()


if __name__ == "__main__":
    config = RedshiftConnectionConfig()  # type: ignore[call-arg]  # pydantic populates from env vars
    cleanup_redshift(config)
