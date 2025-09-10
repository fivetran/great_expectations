"""
This is an example script for how to connect GX Cloud to Amazon s3.

To test, run:
pytest --docs-tests -k "cloud_docs_connect_s3" tests/integration/test_script_runner.py
"""

# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_s3.py - full code example">
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_python.py - get cloud context">
import great_expectations as gx

context = gx.get_context(mode="cloud")

# Optional. Specify a workspace ID.
# context = gx.get_context(mode="cloud", workspace_id="abc123")
# </snippet>
# <snippet name="docs/docusaurus/docs/cloud/connect/connect_python.py - verify context type">
print(type(context).__name__)
# </snippet>

# Hide this
assert type(context).__name__ == "CloudDataContext"
# Hide this

# <snippet name="docs/docusaurus/docs/cloud/connect/connect_python.py - list data sources">
print(context.list_datasources())
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/connect/connect_python.py - retrieve a data asset">
data_source_name = "my_data_source"
asset_name = "my_data_asset"
batch_definition_name = "my_batch_definition"
batch = (
    context.data_sources.get(data_source_name)
    .get_asset(asset_name)
    .get_batch_definition(batch_definition_name)
    .get_batch()
)
# </snippet>

# </snippet>