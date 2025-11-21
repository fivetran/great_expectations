"""
This is an example script for how to validate API-managed Expectations for an entire Data Asset.

To test, run:
pytest --docs-tests -k "cloud_docs_api_expectations_entire_asset" tests/integration/test_script_runner.py
"""

# EXAMPLE SCRIPT STARTS HERE:
import pandas as pd

import great_expectations as gx
from great_expectations.datasource.fluent import PandasDatasource

# Setup test entities (outside snippet for testing)
context = gx.get_context(mode="cloud")
data_source_name = "my_data_source"
data_asset_name = "my_data_asset"
batch_definition_name = f"{data_asset_name} - GX-Managed Batch Definition"


# Helper to delete entities if they exist
def safe_delete(collection, name):
    try:
        collection.delete(name=name)
    except Exception:
        pass


# Delete any existing entities from previous runs (in dependency order)
safe_delete(context.checkpoints, "my_checkpoint")
safe_delete(context.validation_definitions, "my_validation_definition")
safe_delete(context.suites, "my_expectation_suite")
safe_delete(context.data_sources, data_source_name)

# Create datasource
ds = context.data_sources.add_or_update_pandas(PandasDatasource(name=data_source_name))

# Create asset with test data
test_df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
asset = ds.add_dataframe_asset(name=data_asset_name)

# Create batch definition
asset.add_batch_definition_whole_dataframe(batch_definition_name)

# Create expectation suite
suite_name = "my_expectation_suite"
context.suites.add(gx.ExpectationSuite(name=suite_name))

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_entire_asset.py - retrieve batch definition">
import great_expectations as gx

context = gx.get_context(mode="cloud")

data_source_name = "my_data_source"
data_asset_name = "my_data_asset"
batch_definition_name = f"{data_asset_name} - GX-Managed Batch Definition"

batch_definition = (
    context.data_sources.get(data_source_name)
    .get_asset(data_asset_name)
    .get_batch_definition(batch_definition_name)
)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_entire_asset.py - retrieve suite">
suite_name = "my_expectation_suite"
suite = context.suites.get(name=suite_name)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_entire_asset.py - create validation definition">
definition_name = "my_validation_definition"
validation_definition = gx.ValidationDefinition(
    data=batch_definition, suite=suite, name=definition_name
)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_entire_asset.py - run validation definition">
# The following is an example of running a Validation Definition for an in-memory dataframe Data Asset.
# If you are working with a SQL or filesystem Data Asset, omit the batch_parameters.
batch_parameters = {"dataframe": test_df}
validation_definition.run(batch_parameters=batch_parameters)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_entire_asset.py - create checkpoint">
# Retrieve the Validation Definition
validation_definition = context.validation_definitions.get("my_validation_definition")

# Create a Checkpoint
checkpoint_name = "my_checkpoint"
checkpoint_config = gx.Checkpoint(
    name=checkpoint_name, validation_definitions=[validation_definition]
)

# Save the Checkpoint to the data context
checkpoint = context.checkpoints.add(checkpoint_config)

# Run the Checkpoint
# The following is an example of running a Checkpoint for an in-memory dataframe Data Asset.
# If you are working with a SQL or filesystem Data Asset, omit the batch_parameters.
checkpoint.run(batch_parameters=batch_parameters)
# </snippet>

# Cleanup test entities (outside snippet for testing)
context.checkpoints.delete(name=checkpoint_name)
context.validation_definitions.delete(name=definition_name)
context.suites.delete(name=suite_name)
context.data_sources.delete(name=data_source_name)
