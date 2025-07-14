import logging
import sys

from great_expectations.compatibility.pydantic import BaseSettings
from great_expectations.compatibility.sqlalchemy import TextClause, create_engine

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))


class SnowflakeConnectionConfig(BaseSettings):
    """Environment variables for Snowflake connection.
    These are injected in via CI, but when running locally, you may use your own credentials.
    """

    SNOWFLAKE_CI_USER_PASSWORD: str
    SNOWFLAKE_CI_ACCOUNT: str

    @property
    def connection_string(self) -> str:
        return (
            f"snowflake://ci:{self.SNOWFLAKE_CI_USER_PASSWORD}@oca29081.us-east-1/ci?"
            f"warehouse=ci&role=ci"
        )


SCHEMA_FORMAT = "^test_[a-z]{10}$"


def cleanup_snowflake(config: SnowflakeConnectionConfig) -> None:
    engine = create_engine(url=config.connection_string)
    with engine.connect() as conn, conn.begin():
        results = conn.execute(
            TextClause(
                """
                SELECT 'DROP SCHEMA IF EXISTS ' || schema_name || ' CASCADE;' as drop_statement
                FROM INFORMATION_SCHEMA.SCHEMATA
                WHERE REGEXP_LIKE(schema_name, :schema_format)
                AND created < DATEADD(hour, -2, CURRENT_TIMESTAMP())
                """
            ),
            {"schema_format": SCHEMA_FORMAT},
        ).fetchall()

        if results:
            for row in results:
                drop_statement = row[0]
                try:
                    conn.execute(TextClause(drop_statement))
                    logger.info(f"Executed: {drop_statement}")
                except Exception as e:
                    logger.error(f"Failed to execute {drop_statement}: {e}")

            logger.info(f"Cleaned up {len(results)} Snowflake schema(s)")
        else:
            logger.info("No Snowflake schemas to clean up!")

    engine.dispose()


if __name__ == "__main__":
    config = SnowflakeConnectionConfig()  # type: ignore[call-arg]  # pydantic populates from env vars
    cleanup_snowflake(config)
