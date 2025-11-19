"""
This is an example script for how to validate GX-managed Expectations for an entire Data Asset.

To test, run:
pytest --docs-tests -k "cloud_docs_gx_expectations_entire_asset" tests/integration/test_script_runner.py
"""

# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_entire_asset.py - define asset">
data_asset_name = "my_data_asset"
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_entire_asset.py - retrieve checkpoint">
import great_expectations as gx

context = gx.get_context(mode="cloud")

checkpoint_names = [checkpoint.name for checkpoint in context.checkpoints.all()]
for name in checkpoint_names:
    if "GX-Managed" in name and data_asset_name in name:
        my_checkpoint = name
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_entire_asset.py - run checkpoint">
checkpoint = context.checkpoints.get(my_checkpoint)

checkpoint.run()
# </snippet>
