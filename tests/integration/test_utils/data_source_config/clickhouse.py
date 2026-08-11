from typing import TYPE_CHECKING, Mapping, Optional, Sequence

import pandas as pd
import pytest

from great_expectations.compatibility.sqlalchemy import TextClause
from great_expectations.compatibility.typing_extensions import override
from great_expectations.data_context import AbstractDataContext
from great_expectations.datasource.fluent.sql_datasource import TableAsset
from tests.integration.sql_session_manager import SessionSQLEngineManager
from tests.integration.test_utils.data_source_config.backend_spec import (
    BackendProvisioning,
    CiLaneRef,
    SqlBackendSpec,
    TableSchemaItemFactory,
    TransactionMode,
)
from tests.integration.test_utils.data_source_config.base import BatchTestSetup
from tests.integration.test_utils.data_source_config.registry import register_sql_backend
from tests.integration.test_utils.data_source_config.sql import SQLBatchTestSetup
from tests.integration.test_utils.data_source_config.sql_config import SqlDatasourceTestConfig

if TYPE_CHECKING:
    import sqlalchemy as sa  # type-only, exactly as `sql.py` and `backend_spec.py` do it


def _clickhouse_table_engines() -> Sequence["sa.sql.schema.SchemaItem"]:
    from clickhouse_sqlalchemy import engines

    return (engines.MergeTree(order_by=TextClause("tuple()")),)


# Alias-conformance binding: this is the value the record declares, and its annotation is the
# framework's alias rather than a restatement of the signature.
_CLICKHOUSE_TABLE_SCHEMA_ITEMS: TableSchemaItemFactory = _clickhouse_table_engines


@register_sql_backend
class ClickHouseDatasourceTestConfig(SqlDatasourceTestConfig):
    BACKEND_SPEC = SqlBackendSpec(
        label="clickhouse",
        marker="clickhouse",
        provisioning=BackendProvisioning.LOCAL_CONTAINER,
        ci_lane=CiLaneRef(workflow_job="marker-tests", marker_token="clickhouse"),
        # ClickHouse has no `CREATE SCHEMA`; the database is carried in the connection string,
        # as MySQL's is.
        uses_schema=False,
        # ClickHouse has no standard transactions; its rollback is a no-op and its DBAPI commit
        # is a no-op.
        transaction_mode=TransactionMode.AUTOCOMMIT,
        table_schema_items=_CLICKHOUSE_TABLE_SCHEMA_ITEMS,
        dev_requirements_file="reqs/requirements-dev-clickhouse.txt",
        task_runner_marker="clickhouse",
        container_service="clickhouse",
    )

    @override
    def create_batch_setup(
        self,
        request: pytest.FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
        engine_manager: Optional[SessionSQLEngineManager] = None,
    ) -> BatchTestSetup:
        return ClickHouseBatchTestSetup(
            data=data,
            config=self,
            extra_data=extra_data,
            table_name=self.table_name,
            context=context,
            engine_manager=engine_manager,
        )


class ClickHouseBatchTestSetup(SQLBatchTestSetup[ClickHouseDatasourceTestConfig]):
    # Native driver on port 9000, carrying the container's test database. A bare `clickhouse://`
    # scheme resolves to the HTTP driver, which serialises through tab-separated text rather than
    # typed binary values, so the scheme is always written out explicitly.
    _BASE_CONNECTION_STRING = "clickhouse+native://localhost:9000/test_ci"

    @override
    def build_connection_string(self, schema: str | None = None) -> str:
        # This backend declares no schema support, so `schema` is unused; the signature is the
        # shared abstract one.
        return self._BASE_CONNECTION_STRING

    @override
    def make_asset(self) -> TableAsset:
        # No ClickHouse-specific fluent datasource type exists, so this reaches its datasource
        # through the dialect-agnostic SQL datasource instead.
        return self.context.data_sources.add_sql(
            name=self._random_resource_name(),
            connection_string=self.build_connection_string(),
        ).add_table_asset(
            name=self._random_resource_name(),
            table_name=self.table_name,
        )
