from __future__ import annotations

import os
import random
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa
from sqlalchemy.sql import text

from great_expectations.datasource.fluent import (
    SnowflakeDatasource,
    TestConnectionError,
)

if TYPE_CHECKING:
    from sqlalchemy.engine.reflection import Inspector

    from great_expectations.data_context import AbstractDataContext as DataContext


def _ci_snowflake_datasource(context: DataContext, name: str, role: str) -> SnowflakeDatasource:
    return context.data_sources.add_snowflake(
        name,
        account=os.environ["SNOWFLAKE_CI_ACCOUNT"],
        user=os.environ["SNOWFLAKE_CI_USER"],
        private_key=os.environ["SNOWFLAKE_CI_PRIVATE_KEY"],
        database=os.environ["SNOWFLAKE_CI_DATABASE"],
        schema=os.environ["SNOWFLAKE_CI_SCHEMA"],
        warehouse=os.environ["SNOWFLAKE_CI_WAREHOUSE"],
        role=role,
    )


@pytest.mark.snowflake
class TestSnowflake:
    @pytest.mark.xfail(
        raises=AssertionError,
    )  # inspector.get_table_names() fails with this role
    def test_un_queryable_asset_should_raise_error(self, context: DataContext):
        """
        If we try to add an asset that is not queryable with the current datasource
        connection details, then we should expect a TestConnectionError.
        https://docs.snowflake.com/en/developer-guide/python-connector/sqlalchemy#connection-parameters
        """
        snowflake_ds = _ci_snowflake_datasource(
            context, "my_ds", role=os.environ["SNOWFLAKE_CI_ROLE_NO_SELECT"]
        )

        ci_schema = os.environ["SNOWFLAKE_CI_SCHEMA"]
        inspector: Inspector = sa.inspection.inspect(snowflake_ds.get_engine())
        inspector_tables: list[str] = list(inspector.get_table_names(schema=ci_schema))
        print(f"tables: {len(inspector_tables)}\n{inspector_tables}")
        random.shuffle(inspector_tables)

        unqueryable_table: str = ""
        for table_name in inspector_tables:
            try:
                # query the asset, if it fails then we should expect a TestConnectionError
                # expect the sql ProgrammingError to be raised
                # we are only testing the failure case here
                with snowflake_ds.get_engine().connect() as conn:
                    conn.execute(text(f"SELECT * FROM {table_name} LIMIT 1;"))
                print(f"{table_name} is queryable")
            except sa.exc.ProgrammingError:
                print(f"{table_name} is not queryable")
                unqueryable_table = table_name
                break
        assert unqueryable_table, "no unqueryable tables found, cannot run test"

        with pytest.raises(TestConnectionError) as exc_info:
            asset = snowflake_ds.add_table_asset(
                name="un-reachable asset", table_name=unqueryable_table
            )
            print(f"\n  Uh oh, asset should not have been created...\n{asset!r}")
        print(f"\n  TestConnectionError was raised as expected.\n{exc_info.exconly()}")

    def test_queryable_asset_should_pass_test_connection(self, context: DataContext):
        snowflake_ds = _ci_snowflake_datasource(
            context, "my_ds", role=os.environ["SNOWFLAKE_CI_ROLE"]
        )

        inspector: Inspector = sa.inspection.inspect(snowflake_ds.get_engine())
        inspector_tables = list(inspector.get_table_names())
        print(f"tables: {len(inspector_tables)}\n{inspector_tables}")

        table_name = random.choice(inspector_tables)

        # query the table to make sure it is queryable
        with snowflake_ds.get_engine().connect() as conn:
            conn.execute(text(f"SELECT * FROM {table_name} LIMIT 1;"))

        # the table is queryable so the `add_table_asset()` should pass the test_connection step
        asset = snowflake_ds.add_table_asset(name="reachable asset", table_name=table_name)
        print(f"\n  Yay, asset was created!\n{asset!r}")


if __name__ == "__main__":
    pytest.main([__file__, "-vv"])
