"""
This is an example script for how to validate API-managed Expectations for a time-based subset of a filesystem Data Asset.

To test, run:
pytest --docs-tests -k "cloud_docs_api_expectations_batch_filesystem" tests/integration/test_script_runner.py
"""

# EXAMPLE SCRIPT STARTS HERE:
import tempfile
from pathlib import Path

import pandas as pd

import great_expectations as gx
from great_expectations.datasource.fluent import PandasFilesystemDatasource

# Setup test entities (outside snippet for testing)
context = gx.get_context(mode="cloud")
data_source_name = "my_data_source"
data_asset_name = "my_data_asset"


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

# Create test files with date-based naming
temp_dir = Path(tempfile.mkdtemp())
test_df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
test_df.to_csv(temp_dir / "my_filename_2019-01-30.csv", index=False)

# Create filesystem datasource
ds = context.data_sources.add_or_update_pandas_filesystem(
    PandasFilesystemDatasource(name=data_source_name, base_directory=temp_dir)
)

# Add CSV asset
ds.add_csv_asset(name=data_asset_name)

# Create expectation suite
suite_name = "my_expectation_suite"
context.suites.add(gx.ExpectationSuite(name=suite_name))
# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_filesystem.py - retrieve data asset">
data_source_name = "my_data_source"
data_asset_name = "my_data_asset"

import great_expectations as gx

context = gx.get_context(mode="cloud")
ds = context.data_sources.get(data_source_name)
data_asset = ds.get_asset(data_asset_name)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_filesystem.py - partition data">
batch_definition_name = "my_daily_batch_definition"

# Update this regex to match the pattern of your date-based filenames
# This example matches a name like my_filename_2019-01-30.csv
batching_regex = r"my_filename_(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\.csv"

batch_definition = data_asset.add_batch_definition_daily(
    name=batch_definition_name, regex=batching_regex
)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_filesystem.py - retrieve suite">
suite_name = "my_expectation_suite"
suite = context.suites.get(name=suite_name)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_filesystem.py - create validation definition">
definition_name = "my_validation_definition"
validation_definition = gx.ValidationDefinition(
    data=batch_definition, suite=suite, name=definition_name
)

validation_definition = context.validation_definitions.add(validation_definition)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_filesystem.py - run validation definition">
batch_parameters_daily = {"year": "2019", "month": "01", "day": "30"}

validation_definition.run(batch_parameters=batch_parameters_daily)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_filesystem.py - checkpoint">
# Retrieve the Validation Definition
validation_definition = context.validation_definitions.get("my_validation_definition")

# Create a Checkpoint
checkpoint_name = "my_checkpoint"
checkpoint_config = gx.Checkpoint(
    name=checkpoint_name, validation_definitions=[validation_definition]
)

# Save the Checkpoint to the data context
checkpoint = context.checkpoints.add(checkpoint_config)

# When you run the Checkpoint, pass Batch Parameters as strings
batch_parameters_daily = {"year": "2019", "month": "01", "day": "30"}

checkpoint.run(batch_parameters=batch_parameters_daily)
# </snippet>

# Cleanup test entities (outside snippet for testing)
context.checkpoints.delete(name=checkpoint_name)
context.validation_definitions.delete(name=definition_name)
context.suites.delete(name=suite_name)
context.data_sources.delete(name=data_source_name)

# Cleanup temporary directory
import shutil

shutil.rmtree(temp_dir, ignore_errors=True)
