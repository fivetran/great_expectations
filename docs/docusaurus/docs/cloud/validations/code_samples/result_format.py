"""
This is an example script for how to choose a Result Format.

To test, run:
pytest --docs-tests -k "cloud_docs_example_choose_result_format" tests/integration/test_script_runner.py
"""

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
suite = context.suites.add(gx.ExpectationSuite(name=suite_name))

context = gx.get_context(mode="cloud")

batch_definition = (
    context.data_sources.get(data_source_name)
    .get_asset(data_asset_name)
    .get_batch_definition(batch_definition_name)
)

definition_name = "my_validation_definition"
validation_definition = gx.ValidationDefinition(
    data=batch_definition, suite=suite, name=definition_name
)
context.validation_definitions.add(validation_definition)

checkpoint_name = "my_checkpoint"
checkpoint_config = gx.Checkpoint(
    name=checkpoint_name, validation_definitions=[validation_definition]
)

checkpoint = context.checkpoints.add(checkpoint_config)

# BOOLEAN_ONLY Result Format
# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/result_format.py - boolean_only Result Format">
boolean_result_format_dict = {"result_format": "BOOLEAN_ONLY"}
# </snippet>
batch_parameters = {"dataframe": test_df}
validation_definition.run(
    result_format=boolean_result_format_dict, batch_parameters=batch_parameters
)
# checkpoint.run(result_format=boolean_result_format_dict)

# BASIC Result Format
# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/result_format.py - basic Result Format">
basic_result_format_dict = {"result_format": "BASIC"}
# </snippet>
batch_parameters = {"dataframe": test_df}
validation_definition.run(
    result_format=basic_result_format_dict, batch_parameters=batch_parameters
)
# checkpoint.run(result_format=basic_result_format_dict)

# SUMMARY Result Format
# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/result_format.py - summary Result Format">
summary_result_format_dict = {"result_format": "SUMMARY"}
# </snippet>
batch_parameters = {"dataframe": test_df}
validation_definition.run(
    result_format=summary_result_format_dict, batch_parameters=batch_parameters
)
# checkpoint.run(result_format=summary_result_format_dict)

# COMPLETE Result Format
# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/result_format.py - complete Result Format">
complete_result_format_dict = {"result_format": "COMPLETE"}
# </snippet>
batch_parameters = {"dataframe": test_df}
validation_definition.run(
    result_format=complete_result_format_dict, batch_parameters=batch_parameters
)
# checkpoint.run(result_format=complete_result_format_dict)


# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/result_format.py - apply to Checkpoint">
import great_expectations as gx

context = gx.get_context(mode="cloud")

# Define the Result Format
result_format_dict = {
    "result_format": "COMPLETE",
    "unexpected_index_column_names": ["my_indentifying_column"],
    "partial_unexpected_count": 25,
    "include_unexpected_rows": True,
}

# Retrieve the Checkpoint
checkpoint = context.checkpoints.get("my_checkpoint")

# Update the Checkpoint's configuration
checkpoint.result_format = result_format_dict
checkpoint.save()

# Run the Checkpoint
# If you are working with a SQL or filesystem Data Asset, omit the batch_parameters.
batch_parameters = {"dataframe": test_df}
checkpoint.run(batch_parameters=batch_parameters)
# </snippet>


# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/result_format.py - apply to Validation Definition">
import great_expectations as gx

context = gx.get_context(mode="cloud")

# Define the Result Format
result_format_dict = {
    "result_format": "COMPLETE",
    "unexpected_index_column_names": ["my_indentifying_column"],
    "partial_unexpected_count": 25,
    "include_unexpected_rows": True,
}

# Retrieve the Validation Definition
validation_definition = context.validation_definitions.get("my_validation_definition")

# Run the Validation Definition with a Result Format configuration
# If you are working with a SQL or filesystem Data Asset, omit the batch_parameters.
batch_parameters = {"dataframe": test_df}
validation_results = validation_definition.run(
    result_format=result_format_dict, batch_parameters=batch_parameters
)

# Review the Validation Results
print(validation_results)
# </snippet>
