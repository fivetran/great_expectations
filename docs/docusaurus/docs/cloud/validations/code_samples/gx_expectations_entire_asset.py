"""
This is an example script for how to validate GX-managed Expectations for an entire Data Asset.

To test, run:
pytest --docs-tests -k "cloud_docs_gx_expectations_entire_asset" tests/integration/test_script_runner.py
"""


def set_up_context_for_example(context):
    # Create the Data Source
    source_folder = "./data/folder_with_data"
    data_source_name = "my_data_source"
    data_source = context.data_sources.add_pandas_filesystem(
        name=data_source_name, base_directory=source_folder
    )
    assert data_source.name == data_source_name

    # Add a Data Asset
    asset_name = "my_data_asset"
    data_asset = data_source.add_csv_asset(name=asset_name)
    assert data_asset.name == asset_name


# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_entire_asset.py - define asset">
data_asset_name = "my_data_asset"
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_entire_asset.py - retrieve checkpoint">
import great_expectations as gx

context = gx.get_context(mode="cloud")
# Hide this
set_up_context_for_example(context)

checkpoint_names = [checkpoint.name for checkpoint in context.checkpoints.all()]
for name in checkpoint_names:
    if "GX-Managed" in name and data_asset_name in name:
        my_checkpoint = name
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_entire_asset.py - run checkpoint">
checkpoint = context.checkpoints.get(my_checkpoint)

checkpoint.run()
# </snippet>
