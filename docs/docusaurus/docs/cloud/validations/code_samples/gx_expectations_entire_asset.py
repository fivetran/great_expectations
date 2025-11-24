"""
This is an example script for how to validate GX-managed Expectations for an entire Data Asset.

To test, run:
pytest --docs-tests -k "cloud_docs_gx_expectations_entire_asset" tests/integration/test_script_runner.py
"""

# Setup code for testing (not shown in documentation)
import pandas as pd

import great_expectations as gx

context = gx.get_context(mode="cloud")


# Helper to delete entities if they exist
def safe_delete(collection, name):
    try:
        collection.delete(name=name)
    except Exception:
        pass


# Define names
data_source_name = "my_data_source"
data_asset_name = "my_data_asset"
suite_name = "my_expectation_suite"
definition_name = "my_validation_definition"
checkpoint_name = f"{data_asset_name} - GX-Managed Checkpoint"

# Delete any existing entities from previous runs (in dependency order)
safe_delete(context.checkpoints, checkpoint_name)
safe_delete(context.validation_definitions, definition_name)
safe_delete(context.suites, suite_name)
safe_delete(context.data_sources, data_source_name)

# Create test dataframe
test_df = pd.DataFrame({"column_1": [1, 2, 3], "column_2": ["a", "b", "c"]})

# Create datasource and asset
data_source = context.data_sources.add_pandas(name=data_source_name)
asset = data_source.add_dataframe_asset(name=data_asset_name)
batch_definition = asset.add_batch_definition_whole_dataframe(
    name=f"{data_asset_name} - GX-Managed Batch Definition"
)

# Create expectation suite
context.suites.add(gx.ExpectationSuite(name=suite_name))

# Create validation definition
validation_definition = context.validation_definitions.add(
    gx.ValidationDefinition(
        name=definition_name,
        data=batch_definition,
        suite=context.suites.get(suite_name),
    )
)

# Create checkpoint with GX-Managed name pattern
context.checkpoints.add(
    gx.Checkpoint(
        name=checkpoint_name,
        validation_definitions=[validation_definition],
    )
)

# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_entire_asset.py - define asset">
data_asset_name = "my_data_asset"
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_entire_asset.py - retrieve checkpoint">
import great_expectations as gx

context = gx.get_context(mode="cloud")

my_checkpoint = None
checkpoint_names = [checkpoint.name for checkpoint in context.checkpoints.all()]
for name in checkpoint_names:
    if "GX-Managed" in name and data_asset_name in name:
        my_checkpoint = name
        break
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_entire_asset.py - run checkpoint">
checkpoint = context.checkpoints.get(my_checkpoint)

# The following is an example of running a Checkpoint for an in-memory dataframe Data Asset.
# If you are working with a SQL or filesystem Data Asset, omit the batch_parameters.
checkpoint.run(batch_parameters={"dataframe": test_df})
# </snippet>

# Cleanup test entities (outside snippet for testing)
context.checkpoints.delete(name=checkpoint_name)
context.validation_definitions.delete(name=definition_name)
context.suites.delete(name=suite_name)
context.data_sources.delete(name=data_source_name)
