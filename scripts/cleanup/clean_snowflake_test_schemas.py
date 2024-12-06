from great_expectations.compatibility.pydantic import BaseSettings
from great_expectations.compatibility.sqlalchemy import create_engine


class SnowflakeConnectionConfig(BaseSettings):
    """This class retrieves these values from the environment.
    If you're testing locally, you can use your Snowflake creds
    and test against your own Snowflake account.
    """

    SNOWFLAKE_USER: str
    SNOWFLAKE_PW: str
    SNOWFLAKE_ACCOUNT: str
    SNOWFLAKE_DATABASE: str
    SNOWFLAKE_WAREHOUSE: str
    SNOWFLAKE_ROLE: str = "PUBLIC"

    @property
    def connection_string(self) -> str:
        # Note: we don't specify the schema here because it will be created dynamically, and we pass
        # it into the `data_sources.add_snowflake` call.
        return (
            f"snowflake://{self.SNOWFLAKE_USER}:{self.SNOWFLAKE_PW}"
            f"@{self.SNOWFLAKE_ACCOUNT}/{self.SNOWFLAKE_DATABASE}"
            f"?warehouse={self.SNOWFLAKE_WAREHOUSE}&role={self.SNOWFLAKE_ROLE}"
        )


HOURS_OLD_THRESHOLD = (
    2  # we don't want to risk removing anything that's part of a currently running test
)
TEST_SCHEMAS_QUERY = rf"""
SELECT 'DROP SCHEMA CI.' || schema_name || ';'
FROM CI.information_schema.schemata
WHERE REGEXP_LIKE(schema_name, '^((PY3\\d\\d?_)?[A-Z0-9]{{33}})|([a-z]{{10}})$')
AND created < DATEADD('hour', -{HOURS_OLD_THRESHOLD}, CURRENT_TIMESTAMP)
ORDER BY created;
"""


def cleanup_snowflake() -> None:
    config = SnowflakeConnectionConfig()  # type: ignore[call-arg]  # retrieves env vars
    engine = create_engine(url=config.connection_string)

    rows = engine.execute(TEST_SCHEMAS_QUERY).fetchall()
    statements = [row[0] for row in rows]
    breakpoint()
    for statement in statements:
        print("running: " + statement)
        engine.execute(statement)


if __name__ == "__main__":
    cleanup_snowflake()
