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
    logger.info(f"Connecting to Snowflake with connection string: {config.connection_string}")
    engine = create_engine(url=config.connection_string)
    with engine.connect() as conn, conn.begin():
        logger.info("Connected successfully!")

        # Debug: Check current database and schema context
        current_context = conn.execute(
            TextClause(
                "SELECT CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_ROLE(), CURRENT_USER()"
            )
        ).fetchone()
        if current_context:
            db, schema, role, user = current_context
            logger.info(
                f"Current context - Database: {db}, Schema: {schema}, Role: {role}, User: {user}"
            )

        # Debug: List all schemas in the database
        logger.info("Listing all schemas in current database...")
        all_schemas = conn.execute(
            TextClause(
                "SELECT schema_name, created FROM INFORMATION_SCHEMA.SCHEMATA ORDER BY created DESC LIMIT 20"
            )
        ).fetchall()

        logger.info(f"Found {len(all_schemas)} total schemas:")
        for row in all_schemas:
            schema_name, created = row
            logger.info(f"  {schema_name} (created: {created})")

        # Debug: Check schemas that start with 'test_'
        test_schemas = conn.execute(
            TextClause(
                "SELECT schema_name, created FROM INFORMATION_SCHEMA.SCHEMATA WHERE schema_name LIKE 'test_%' ORDER BY created DESC"
            )
        ).fetchall()

        logger.info(f"Found {len(test_schemas)} schemas starting with 'test_':")
        for row in test_schemas:
            schema_name, created = row
            logger.info(f"  {schema_name} (created: {created})")

        # Debug: Test the regex pattern
        logger.info(f"Testing regex pattern: {SCHEMA_FORMAT}")
        regex_test = conn.execute(
            TextClause(
                """
                SELECT schema_name, created
                FROM INFORMATION_SCHEMA.SCHEMATA
                WHERE REGEXP_LIKE(schema_name, :schema_format)
                ORDER BY created DESC
                """
            ),
            {"schema_format": SCHEMA_FORMAT},
        ).fetchall()

        logger.info(f"Found {len(regex_test)} schemas matching regex pattern:")
        for row in regex_test:
            schema_name, created = row
            logger.info(f"  {schema_name} (created: {created})")

        # Debug: Check time filtering
        logger.info("Checking time filtering (schemas older than 2 hours)...")
        time_filtered = conn.execute(
            TextClause(
                """
                SELECT schema_name, created, CURRENT_TIMESTAMP() as now,
                       DATEADD(hour, -2, CURRENT_TIMESTAMP()) as cutoff_time,
                       CASE WHEN created < DATEADD(hour, -2, CURRENT_TIMESTAMP()) THEN 'OLD' ELSE 'NEW' END as age_status
                FROM INFORMATION_SCHEMA.SCHEMATA
                WHERE REGEXP_LIKE(schema_name, :schema_format)
                ORDER BY created DESC
                """
            ),
            {"schema_format": SCHEMA_FORMAT},
        ).fetchall()

        logger.info("Schema age analysis:")
        for row in time_filtered:
            schema_name, created, now, cutoff_time, age_status = row
            logger.info(
                f"  {schema_name} - Created: {created}, Cutoff: {cutoff_time}, Status: {age_status}"
            )

        # Now run the original query
        logger.info("Running final cleanup query...")
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
            logger.info(f"Found {len(results)} schemas to clean up:")
            for row in results:
                drop_statement = row[0]
                logger.info(f"  Will execute: {drop_statement}")
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
