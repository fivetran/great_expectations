# ruff: noqa: I001
"""
This is an example script for how to connect GX Cloud to Microsoft SQL Server.

To test, run:
pytest --docs-tests -k "cloud_docs_connect_sqlserver" tests/integration/test_script_runner.py
"""

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
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_sqlserver.py - full code example">
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_sqlserver.py - get cloud context">
import great_expectations as gx

context = gx.get_context(mode="cloud")
# </snippet>

# Add a Microsoft SQL Server Data Source
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_sqlserver.py - define source">
datasource_name = "Self-hosted SQL Server"
host = "sql-server.example.com"
database = "production"
schema = "sales"
port = 1433
encrypt = "Mandatory"
authentication = "SQL Server"
username = "${SQL_SERVER_USER}"
password = "${SQL_SERVER_PASSWORD}"
# </snippet>

# Hide start
host = SQL_SERVER_HOST
port = SQL_SERVER_PORT
database = SQL_SERVER_DATABASE
schema = SQL_SERVER_SCHEMA
encrypt = SQL_SERVER_ENCRYPT
username = SQL_SERVER_USERNAME
password = SQL_SERVER_PASSWORD
# Hide end

# <snippet name="docs/docusaurus/docs/cloud/connect/connect_sqlserver.py - add source">
data_source = context.data_sources.add_sql_server(
    name=datasource_name,
    host=host,
    database=database,
    schema=schema,
    port=port,
    encrypt=encrypt,
    authentication=authentication,
    username=username,
    password=password,
)
# </snippet>

# Add a Table Data Asset
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_sqlserver.py - define table data asset">
data_asset_name = "my_table_asset"
table_name = "my_table"
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/connect/connect_sqlserver.py - add table data asset">
table_data_asset = data_source.add_table_asset(
    table_name=table_name, name=data_asset_name
)
# </snippet>

# Get the updated Data Source
data_source = context.data_sources.get(datasource_name)

# Add a Query Data Asset
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_sqlserver.py - define query data asset">
data_asset_name = "my_query_asset"
query = "SELECT * from my_table WHERE column1 = 'value' AND column2 > 20"
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/connect/connect_sqlserver.py - add query data asset">
query_data_asset = data_source.add_query_asset(query=query, name=data_asset_name)
# </snippet>

# </snippet>
