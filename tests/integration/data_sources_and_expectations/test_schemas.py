from uuid import uuid4

import pandas as pd
import pytest

import great_expectations.expectations as gxe
from great_expectations import get_context
from tests.integration.test_utils.data_source_config.databricks import (
    DatabricksBatchTestSetup,
    DatabricksDatasourceTestConfig,
)
from tests.integration.test_utils.data_source_config.snowflake import (
    SnowflakeBatchTestSetup,
    SnowflakeDatasourceTestConfig,
)
from tests.integration.test_utils.data_source_config.sql_server import (
    SQLServerBatchTestSetup,
    SQLServerDatasourceTestConfig,
)

DATA_FRAME = pd.DataFrame(
    {
        "words": [
            "apple",
            "banana",
            "cherry",
        ],
    }
)

_SUFFIX = uuid4().hex[:8]
TEST_SCHEMAS = [f"regular_ol_lowercase_{_SUFFIX}", f"FANCY_UPPER_CASE_{_SUFFIX}", None]


class TestSchemaSupport:
    @pytest.mark.databricks
    @pytest.mark.parametrize("schema_name", TEST_SCHEMAS)
    def test_databricks(
        self,
        schema_name: str | None,
    ) -> None:
        batch_setup = DatabricksBatchTestSetup(
            config=DatabricksDatasourceTestConfig(
                schema_name=schema_name,
            ),
            data=DATA_FRAME,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            expectation = gxe.ExpectTableRowCountToEqual(value=3)

            result = batch.validate(expectation)

            assert result.success

    @pytest.mark.sql_server
    @pytest.mark.parametrize("schema_name", TEST_SCHEMAS)
    def test_sql_server(
        self,
        schema_name: str | None,
    ) -> None:
        batch_setup = SQLServerBatchTestSetup(
            config=SQLServerDatasourceTestConfig(schema_name=schema_name),
            data=DATA_FRAME,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            expectation = gxe.ExpectTableRowCountToEqual(value=3)

            result = batch.validate(expectation)

            assert result.success

    @pytest.mark.skip(
        "Cleanup fails for upper case schemas. TODO: determine if this is a test issue or something we need to address."  # noqa: E501
    )
    @pytest.mark.snowflake
    @pytest.mark.parametrize("schema_name", TEST_SCHEMAS)
    def test_snowflake(
        self,
        schema_name: str | None,
    ) -> None:
        batch_setup = SnowflakeBatchTestSetup(
            config=SnowflakeDatasourceTestConfig(
                schema_name=schema_name,
            ),
            data=DATA_FRAME,
            extra_data={},
            context=get_context(mode="ephemeral"),
        )
        with batch_setup.batch_test_context() as batch:
            expectation = gxe.ExpectTableRowCountToEqual(value=3)

            result = batch.validate(expectation)

            assert result.success
