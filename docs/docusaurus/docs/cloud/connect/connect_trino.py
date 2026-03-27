"""
This is an example script for how to connect GX Cloud to Trino.

To test, run:
pytest --docs-tests -k "cloud_docs_connect_trino" tests/integration/test_script_runner.py
"""

# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_trino.py - full code example">
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_trino.py - get cloud context">
import great_expectations as gx

context = gx.get_context(mode="cloud")
# </snippet>

# Hide this
assert type(context).__name__ == "CloudDataContext"
# Hide this

# Add a Trino Data Source
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_trino.py - define source">
data_source_name = "my_trino_datasource"
connection_string = "trino://my_user:@my_host:my_port/my_catalog/my_database"
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/connect/connect_trino.py - add source">
data_source = context.data_sources.add_sql(
   name=data_source_name, connection_string=connection_string
)
# </snippet>

# Add a Data Asset
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_trino.py - define asset">
data_asset_name = "my_table_asset"
table_name = "my_table"
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/connect/connect_trino.py - add asset">
data_asset = data_source.add_table_asset(
   table_name=table_name, name=data_asset_name
)
# </snippet>

# </snippet>