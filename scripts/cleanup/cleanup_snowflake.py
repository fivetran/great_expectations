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

    SNOWFLAKE_CI_PRIVATE_KEY: str
    SNOWFLAKE_CI_ACCOUNT: str
    SNOWFLAKE_CI_USER: str
    SNOWFLAKE_CI_DATABASE: str
    SNOWFLAKE_CI_WAREHOUSE: str
    SNOWFLAKE_CI_ROLE: str

    @property
    def connection_string(self) -> str:
        # Password omitted; private key is passed via connect_args
        return (
            f"snowflake://{self.SNOWFLAKE_CI_USER}:@{self.SNOWFLAKE_CI_ACCOUNT}/{self.SNOWFLAKE_CI_DATABASE}?"
            f"warehouse={self.SNOWFLAKE_CI_WAREHOUSE}&role={self.SNOWFLAKE_CI_ROLE}"
        )

    @property
    def connect_args(self) -> dict:
        return {"private_key": self.SNOWFLAKE_CI_PRIVATE_KEY}


# Regex to match uppercase schema names
# (Snowflake converts unquoted identifiers to uppercase)
SCHEMA_PATTERN_TEST = "^GX_CI_TEST_[A-F0-9]{10}$"  # General SQL testing framework
SCHEMA_PATTERN_PY_VERSION = "^PY3[0-9]{1,2}_I[A-F0-9]{32}$"  # Python version-specific test schemas
SCHEMA_FORMAT = f"{SCHEMA_PATTERN_TEST}|{SCHEMA_PATTERN_PY_VERSION}"


def cleanup_snowflake(config: SnowflakeConnectionConfig) -> None:
    engine = create_engine(url=config.connection_string, connect_args=config.connect_args)
    with engine.connect() as conn, conn.begin():
        results = conn.execute(
            TextClause(
                f"SELECT 'DROP SCHEMA IF EXISTS ' || schema_name || ' CASCADE;' as drop_statement "
                f"FROM INFORMATION_SCHEMA.SCHEMATA "
                f"WHERE REGEXP_LIKE(schema_name, '{SCHEMA_FORMAT}') "
                f"AND created < DATEADD(hour, -1, CURRENT_TIMESTAMP())"
            )
        ).fetchall()

        if results:
            for row in results:
                drop_statement = row[0]
                logger.info(f"Executing: {drop_statement}")
                conn.execute(TextClause(drop_statement))
            logger.info(f"Cleaned up {len(results)} Snowflake schema(s)")
        else:
            logger.info("No Snowflake schemas to clean up!")

    engine.dispose()


if __name__ == "__main__":
    config = SnowflakeConnectionConfig()  # type: ignore[call-arg]  # pydantic populates from env vars
    cleanup_snowflake(config)
