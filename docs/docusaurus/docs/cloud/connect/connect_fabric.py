# ruff: noqa: I001
"""
This is an example script for how to connect GX Cloud to Microsoft Fabric.

To test, run:
pytest --docs-tests -k "cloud_docs_connect_fabric" tests/integration/test_script_runner.py
"""

from unittest.mock import patch

import sqlalchemy as sa
from great_expectations.datasource.fluent.fabric_datasource import FabricDatasource
from tests.test_utils import (
    SQL_SERVER_DATABASE,
    SQL_SERVER_ENCRYPT,
    SQL_SERVER_HOST,
    SQL_SERVER_PASSWORD,
    SQL_SERVER_PORT,
    SQL_SERVER_SCHEMA,
    SQL_SERVER_USERNAME,
    get_default_sql_server_url,
)

# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_fabric.py - full code example">
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_fabric.py - get cloud context">
import great_expectations as gx

context = gx.get_context(mode="cloud")
# </snippet>

# Add a Microsoft Fabric Data Source
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_fabric.py - define source">
datasource_name = "Fabric"
host = "myworkspace.datawarehouse.fabric.microsoft.com"
database = "production"
schema = "sales"
port = 1433
encrypt = "Mandatory"
tenant_id = "${ENTRA_ID_TENANT}"
client_id = "${ENTRA_ID_CLIENT_ID}"
client_secret = "${ENTRA_ID_CLIENT_SECRET}"
# </snippet>

# Hide start
try:
    context.data_sources.delete(datasource_name)
except Exception:
    pass
host = SQL_SERVER_HOST
port = SQL_SERVER_PORT
database = SQL_SERVER_DATABASE
schema = SQL_SERVER_SCHEMA
encrypt = SQL_SERVER_ENCRYPT
tenant_id = "ci_placeholder"
client_id = "ci_placeholder"
client_secret = "ci_placeholder"
_patcher = patch.object(FabricDatasource, "test_connection")
_patcher.start()
# Hide end

# <snippet name="docs/docusaurus/docs/cloud/connect/connect_fabric.py - add source">
data_source = context.data_sources.add_fabric(
    name=datasource_name,
    host=host,
    database=database,
    schema=schema,
    port=port,
    encrypt=encrypt,
    tenant_id=tenant_id,
    client_id=client_id,
    client_secret=client_secret,
)
# </snippet>

# Hide start
_patcher.stop()
context.data_sources.delete(datasource_name)
# We don't have Fabric infrastructure, so we use SQL Server as an analog
data_source = context.data_sources.add_sql_server(
    name=datasource_name,
    host=SQL_SERVER_HOST,
    port=SQL_SERVER_PORT,
    database=SQL_SERVER_DATABASE,
    schema=SQL_SERVER_SCHEMA,
    encrypt=SQL_SERVER_ENCRYPT,
    authentication="SQL Server",
    username=SQL_SERVER_USERNAME,
    password=SQL_SERVER_PASSWORD,
)
# Hide end

# Add a Table Data Asset
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_fabric.py - define table data asset">
data_asset_name = "my_table_asset"
table_name = "my_table"
# </snippet>

# Hide start
_engine = sa.create_engine(get_default_sql_server_url())
with _engine.connect() as _conn:
    _conn.execute(
        sa.text(
            f"IF NOT EXISTS (SELECT * FROM sys.tables WHERE name='{table_name}') "
            f"CREATE TABLE {table_name} (column1 VARCHAR(255), column2 INT)"
        )
    )
_engine.dispose()
# Hide end

# <snippet name="docs/docusaurus/docs/cloud/connect/connect_fabric.py - add table data asset">
table_data_asset = data_source.add_table_asset(
    table_name=table_name, name=data_asset_name
)
# </snippet>

# Get the updated Data Source
data_source = context.data_sources.get(datasource_name)

# Add a Query Data Asset
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_fabric.py - define query data asset">
data_asset_name = "my_query_asset"
query = "SELECT * FROM my_table WHERE column1 = 'value' AND column2 > 20"
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/connect/connect_fabric.py - add query data asset">
query_data_asset = data_source.add_query_asset(query=query, name=data_asset_name)
# </snippet>

# </snippet>

# Hide start
context.data_sources.delete(datasource_name)
_engine = sa.create_engine(get_default_sql_server_url())
with _engine.connect() as _conn:
    _conn.execute(sa.text(f"DROP TABLE IF EXISTS {table_name}"))
_engine.dispose()
# Hide end
