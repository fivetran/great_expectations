# ruff: noqa: I001
"""
This is an example script for how to connect GX Cloud to BigQuery.

To test, run:
pytest --docs-tests --cloud --bigquery -k "cloud_docs_connect_bigquery" tests/integration/test_script_runner.py
"""

import os

import sqlalchemy as sa

from tests.test_utils import get_bigquery_connection_url

# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_bigquery.py - full code example">
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_bigquery.py - get cloud context">
import great_expectations as gx

context = gx.get_context(mode="cloud")
# </snippet>

# Add a BigQuery Data Source
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_bigquery.py - define source">
data_source_name = "my_bigquery_datasource"
connection_string = (
    "bigquery://my_project/my_dataset?credentials_path=/my/credentials.json"
)
# </snippet>

# Hide start
try:
    context.data_sources.delete(data_source_name)
except Exception:
    pass
_bq_url = get_bigquery_connection_url()
_goog_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
if _goog_creds:
    _sep = "&" if "?" in _bq_url else "?"
    connection_string = f"{_bq_url}{_sep}credentials_path={_goog_creds}"
else:
    connection_string = _bq_url
# Hide end

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

# Hide start
_bq_engine = sa.create_engine(connection_string)
with _bq_engine.begin() as _conn:
    _conn.execute(
        sa.text(f"CREATE TABLE IF NOT EXISTS `{table_name}` (`column` STRING)")
    )
_bq_engine.dispose()
# Hide end

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
query = "SELECT * FROM my_table WHERE column = 'value'"
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/connect/connect_bigquery.py - add query asset">
query_data_asset = data_source.add_query_asset(query=query, name=data_asset_name)
# </snippet>

# </snippet>

# Hide start
context.data_sources.delete(data_source_name)
_bq_engine = sa.create_engine(connection_string)
with _bq_engine.begin() as _conn:
    _conn.execute(sa.text(f"DROP TABLE IF EXISTS `{table_name}`"))
_bq_engine.dispose()
# Hide end
