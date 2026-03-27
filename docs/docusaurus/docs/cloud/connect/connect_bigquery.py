"""
This is an example script for how to connect GX Cloud to BigQuery.

To test, run:
pytest --docs-tests -k "cloud_docs_connect_bigquery" tests/integration/test_script_runner.py
"""

# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_bigquery.py - full code example">
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_bigquery.py - get cloud context">
import great_expectations as gx

context = gx.get_context(mode="cloud")
# </snippet>

# Hide this
assert type(context).__name__ == "CloudDataContext"
# Hide this

# Add a Data Source
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_bigquery.py - define source">
data_source_name = "my_bigquery_datasource"
connection_string = (
    "bigquery://my_project/my_dataset?credentials_path=/my/credentials.json"
)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/connect/connect_bigquery.py - add source">
data_source = context.data_sources.add_bigquery(
    name=data_source_name, connection_string=connection_string
)
# </snippet>

# Add a Table Data Asset
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_bigquery.py - define table asset">
data_asset_name = "my_table_asset"
table_name = "my_table"
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/connect/connect_bigquery.py - add table asset">
table_data_asset = data_source.add_table_asset(
    table_name=table_name, name=data_asset_name
)
# </snippet>

# Get the updated Data Source
data_source = context.data_sources.get(data_source_name)

# Add a Query Data Asset
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_bigquery.py - define query asset">
data_asset_name = "my_query_asset"
query = "SELECT * from my_table WHERE column = 'value'"
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/connect/connect_bigquery.py - add query asset">
query_data_asset = data_source.add_query_asset(query=query, name=data_asset_name)
# </snippet>

# </snippet>
