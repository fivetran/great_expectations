# ruff: noqa: I001
"""
This is an example script for how to connect GX Cloud to Microsoft Fabric.

To test, run:
pytest --docs-tests -k "cloud_docs_connect_fabric" tests/integration/test_script_runner.py
"""

from unittest.mock import patch

from great_expectations.datasource.fluent.fabric_datasource import FabricDatasource
from tests.test_utils import (
    SQL_SERVER_DATABASE,
    SQL_SERVER_ENCRYPT,
    SQL_SERVER_HOST,
    SQL_SERVER_PASSWORD,
    SQL_SERVER_PORT,
    SQL_SERVER_SCHEMA,
    SQL_SERVER_USERNAME,
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

host = SQL_SERVER_HOST  # Hide this
port = SQL_SERVER_PORT  # Hide this
database = SQL_SERVER_DATABASE  # Hide this
schema = SQL_SERVER_SCHEMA  # Hide this
encrypt = SQL_SERVER_ENCRYPT  # Hide this
tenant_id = "ci_placeholder"  # Hide this
client_id = "ci_placeholder"  # Hide this
client_secret = "ci_placeholder"  # Hide this

_patcher = patch.object(FabricDatasource, "test_connection")  # Hide this
_patcher.start()  # Hide this

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

_patcher.stop()  # Hide this

# Add a Table Data Asset
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_fabric.py - define table data asset">
data_asset_name = "my_table_asset"
table_name = "my_table"
# </snippet>

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
query = "SELECT * from my_table WHERE column1 = 'value' AND column2 > 20"
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/connect/connect_fabric.py - add query data asset">
query_data_asset = data_source.add_query_asset(query=query, name=data_asset_name)
# </snippet>

# </snippet>

context.data_sources.delete(datasource_name)
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
