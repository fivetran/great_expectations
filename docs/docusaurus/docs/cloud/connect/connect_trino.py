"""
This is an example script for how to connect GX Cloud to Trino.

To test, run:
pytest --docs-tests --cloud --trino -k "cloud_docs_connect_trino" tests/integration/test_script_runner.py
"""

import sqlalchemy as sa

# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_trino.py - full code example">
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_trino.py - get cloud context">
import great_expectations as gx

# Hide start
from tests.test_utils import get_default_trino_url

# Hide end

context = gx.get_context(mode="cloud")
# </snippet>

# Add a Trino Data Source
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_trino.py - define source">
data_source_name = "my_trino_datasource"
connection_string = "trino://my_user:@my_host:my_port/my_catalog/my_database"
# </snippet>

# Hide start
try:
    context.data_sources.delete(data_source_name)
except Exception:
    pass
connection_string = get_default_trino_url()
# Hide end

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

# Hide start
_trino_engine = sa.create_engine(connection_string)
with _trino_engine.begin() as _conn:
    _conn.execute(
        sa.text(
            f"CREATE TABLE IF NOT EXISTS {table_name} "
            f"(column1 VARCHAR(255), column2 INTEGER)"
        )
    )
_trino_engine.dispose()
# Hide end

# <snippet name="docs/docusaurus/docs/cloud/connect/connect_trino.py - add asset">
data_asset = data_source.add_table_asset(table_name=table_name, name=data_asset_name)
# </snippet>

# </snippet>

# Hide start
context.data_sources.delete(data_source_name)
_trino_engine = sa.create_engine(connection_string)
with _trino_engine.begin() as _conn:
    _conn.execute(sa.text(f"DROP TABLE IF EXISTS {table_name}"))
_trino_engine.dispose()
# Hide end
