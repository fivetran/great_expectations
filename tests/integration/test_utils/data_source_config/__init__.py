from .backend_spec import (
    BackendProvisioning,
    BackendTier,
    CiLaneRef,
    SqlBackendSpec,
    TableSchemaItemFactory,
    TransactionMode,
)
from .base import DataSourceTestConfig
from .big_query import BigQueryDatasourceTestConfig
from .databricks import DatabricksDatasourceTestConfig
from .generic_sql import GenericSQLDatasourceTestConfig
from .mysql import MySQLDatasourceTestConfig
from .pandas_data_frame import PandasDataFrameDatasourceTestConfig
from .pandas_filesystem_csv import PandasFilesystemCsvDatasourceTestConfig
from .postgres import PostgreSQLDatasourceTestConfig
from .redshift import RedshiftDatasourceTestConfig
from .registry import (
    isolated_registry,
    iter_sql_backends,
    register_sql_backend,
    sql_backends_for_tier,
)
from .singlestore import SingleStoreDatasourceTestConfig
from .snowflake import SnowflakeDatasourceTestConfig
from .spark_filesystem_csv import SparkFilesystemCsvDatasourceTestConfig
from .sql_config import SqlDatasourceTestConfig
from .sql_server import SQLServerDatasourceTestConfig
from .sqlite import SqliteDatasourceTestConfig

# `tiers` derives its lists by reading the registry, so every module above whose import
# registers a backend must be imported before this one: importing a submodule always runs this
# package's `__init__` first, and any backend module not yet imported by the time `tiers` reads
# the registry has not run its registration decorator, so it would be silently absent from the
# derived lists. Alphabetical import order already places `tiers` last among these names, which
# is what makes that ordering hold without a special case.
#
# `isort: split` below asks the import sorter to treat this import as its own block and never
# merge a later addition into the block above it. That is defence in depth, not the guarantee
# itself: it only holds while a new backend import lands inside the block above, and does nothing
# if one is appended after this import instead — `tests/test_sql_backend_registry.py` has the
# regression test that catches the ordering violation regardless of where a new import lands.
# isort: split
from .tiers import (
    ALL_DATA_SOURCES,
    CURATED_SQL_DATA_SOURCES,
    PANDAS_DATA_SOURCES,
    SPARK_DATA_SOURCES,
    SQL_DATA_SOURCES,
    data_sources_for_tier_case,
)
