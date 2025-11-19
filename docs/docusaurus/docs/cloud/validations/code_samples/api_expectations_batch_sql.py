"""
This is an example script for how to validate API-managed Expectations for a time-based subset of a SQL Data Asset.

To test, run:
pytest --docs-tests -k "cloud_docs_api_expectations_batch_sql" tests/integration/test_script_runner.py
"""

# EXAMPLE SCRIPT STARTS HERE:
import sqlite3
import tempfile
from pathlib import Path

import pandas as pd

import great_expectations as gx

# Setup test entities (outside snippet for testing)
context = gx.get_context(mode="cloud")
data_source_name = "my_data_source"
data_asset_name = "my_data_asset"

# Create a temporary SQLite database
temp_dir = Path(tempfile.mkdtemp())
db_path = temp_dir / "test.db"
conn = sqlite3.connect(str(db_path))

# Create table with datetime column
test_df = pd.DataFrame(
    {
        "id": [1, 2, 3],
        "my_date_or_datetime_column": pd.to_datetime(
            ["2019-01-15", "2019-01-20", "2019-01-30"]
        ),
        "value": [10, 20, 30],
    }
)
test_df.to_sql("organizations", conn, index=False, if_exists="replace")
conn.close()

# Create SQL datasource
ds = context.data_sources.add_sqlite(
    name=data_source_name, connection_string=f"sqlite:///{db_path}"
)

# Add table asset
ds.add_table_asset(name=data_asset_name, table_name="organizations")

# Create expectation suite
suite_name = "my_expectation_suite"
context.suites.add(gx.ExpectationSuite(name=suite_name))
# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_sql.py - retrieve data asset">
data_source_name = "my_data_source"
data_asset_name = "my_data_asset"

import great_expectations as gx

context = gx.get_context(mode="cloud")
ds = context.data_sources.get(data_source_name)
data_asset = ds.get_asset(data_asset_name)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_sql.py - partition data">
batch_definition_name = "my_daily_batch_definition"
date_column = "my_date_or_datetime_column"
daily_batch_definition = data_asset.add_batch_definition_daily(
    name=batch_definition_name, column=date_column
)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_sql.py - retrieve suite">
suite_name = "my_expectation_suite"
suite = context.suites.get(name=suite_name)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_sql.py - create validation definition">
definition_name = "my_validation_definition"
validation_definition = gx.ValidationDefinition(
    data=daily_batch_definition, suite=suite, name=definition_name
)

validation_definition = context.validation_definitions.add(validation_definition)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_sql.py - run validation definition">
batch_parameters_daily = {"year": 2019, "month": 1, "day": 30}

validation_definition.run(batch_parameters=batch_parameters_daily)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/api_expectations_batch_sql.py - create checkpoint">
# Retrieve the Validation Definition
validation_definition = context.validation_definitions.get("my_validation_definition")

# Create a Checkpoint
checkpoint_name = "my_checkpoint"
checkpoint_config = gx.Checkpoint(
    name=checkpoint_name, validation_definitions=[validation_definition]
)

# Save the Checkpoint to the data context
checkpoint = context.checkpoints.add(checkpoint_config)

# When you run the Checkpoint, pass Batch Parameters as integers
batch_parameters_daily = {"year": 2019, "month": 1, "day": 30}

checkpoint.run(batch_parameters=batch_parameters_daily)
# </snippet>
