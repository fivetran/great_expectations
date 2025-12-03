"""
This is an example script for how to validate GX-managed Expectations for a time-based subset of a SQL Data Asset.

To test, run:
pytest --docs-tests -k "cloud_docs_gx_expectations_batch_sql" tests/integration/test_script_runner.py
"""

# Setup code for testing (not shown in documentation)
import shutil
import sqlite3
import tempfile
from pathlib import Path

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
column_name = "my_date_or_datetime_column"
suite_name = "my_expectation_suite"
definition_name = "my_validation_definition"
checkpoint_name = f"{data_asset_name} - GX-Managed Checkpoint"
batch_definition_name = f"{data_asset_name} - GX-Managed Batch Definition"

# Delete any existing entities from previous runs (in dependency order)
safe_delete(context.checkpoints, checkpoint_name)
safe_delete(context.validation_definitions, definition_name)
safe_delete(context.suites, suite_name)
safe_delete(context.data_sources, data_source_name)

# Create temporary SQLite database with datetime column
temp_dir = tempfile.mkdtemp()
db_path = Path(temp_dir) / "test.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute(
    f"""CREATE TABLE organizations (
        id INTEGER PRIMARY KEY,
        {column_name} TEXT
    )"""
)
cursor.execute(
    f"""INSERT INTO organizations (id, {column_name}) VALUES
    (1, '2019-01-30 10:00:00'),
    (2, '2019-02-15 14:30:00'),
    (3, '2019-03-20 09:15:00')
    """
)
conn.commit()
conn.close()

# Create SQL datasource and asset
connection_string = f"sqlite:///{db_path}"
data_source = context.data_sources.add_sqlite(
    name=data_source_name, connection_string=connection_string
)
asset = data_source.add_table_asset(name=data_asset_name, table_name="organizations")
batch_definition = asset.add_batch_definition_daily(
    name=batch_definition_name, column=column_name
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
# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_sql.py - define asset">
data_source_name = "my_data_source"
data_asset_name = "my_data_asset"
column_name = "my_date_or_datetime_column"
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_sql.py - partition data">
import great_expectations as gx
from great_expectations.core.partitioners import ColumnPartitionerDaily

context = gx.get_context(mode="cloud")
ds = context.data_sources.get(data_source_name)
asset = ds.get_asset(data_asset_name)

for bd in asset.batch_definitions:
    if "GX-Managed" in bd.name:
        bd.partitioner = ColumnPartitionerDaily(
            method_name="partition_on_year_and_month_and_day",
            column_name=column_name,
            sort_ascending=True,
        )

context.update_datasource(ds)
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_sql.py - retrieve checkpoint name">
import great_expectations as gx

context = gx.get_context()

data_asset_name = "my_data_asset"

my_checkpoint = None
checkpoint_names = [checkpoint.name for checkpoint in context.checkpoints.all()]
for name in checkpoint_names:
    if "GX-Managed" in name and data_asset_name in name:
        my_checkpoint = name
        break
# </snippet>

# <snippet name="docs/docusaurus/docs/cloud/validations/code_samples/gx_expectations_batch_sql.py - run checkpoint">
checkpoint = context.checkpoints.get(my_checkpoint)
batch_parameters_daily = {"year": 2019, "month": 1, "day": 30}

checkpoint.run(batch_parameters=batch_parameters_daily)
# </snippet>

# Cleanup test entities (outside snippet for testing)
context.checkpoints.delete(name=checkpoint_name)
context.validation_definitions.delete(name=definition_name)
context.suites.delete(name=suite_name)
context.data_sources.delete(name=data_source_name)
shutil.rmtree(temp_dir, ignore_errors=True)
