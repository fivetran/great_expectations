"""
To run this test locally, use the postgresql database docker container.

1. From the repo root dir, run:
cd assets/docker/postgresql
docker compose up

2. Run the following command from the repo root dir in a second terminal:
pytest --postgresql --docs-tests -k "data_quality_use_case_freshness_workflow" tests/integration/test_script_runner.py
"""

# ruff: noqa: DTZ005, DTZ001

# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/freshness_resources/freshness_workflow.py full workflow">
import datetime

import great_expectations as gx
import great_expectations.expectations as gxe

# Create Data Context.
context = gx.get_context()

# Connect to sample data and create Data Source, Data Asset, Batch Definition, and Batch.
CONNECTION_STRING = "postgresql+psycopg2://try_gx:try_gx@postgres.workshops.greatexpectations.io/gx_learn_data_quality"

data_source = context.data_sources.add_postgres(
    "postgres database", connection_string=CONNECTION_STRING
)
data_asset = data_source.add_table_asset(
    name="sensor readings", table_name="freshness_sensor_readings"
)
batch_definition = data_asset.add_batch_definition_whole_table("batch definition")
batch = batch_definition.get_batch()


# Define the custom Expectation class by subclassing the built-in ExpectColumnMaxToBeBetween Expectation.
class ExpectSensorDataToBeFresh(gxe.ExpectColumnMaxToBeBetween):
    """Custom Expectation class to validate the freshness of sensor readings in the database."""

    column: str = "created_at"
    min_value: datetime.datetime = datetime.datetime.now() - datetime.timedelta(
        minutes=5
    )
    description: str = "New sensor readings should have arrived in the database within the last 5 minutes."


# Validate the sample data with the custom freshness Expectation.
validation_result = batch.validate(ExpectSensorDataToBeFresh())

print(f"Freshness check passed: {validation_result['success']}")
print(f"Most recent reading timestamp: {validation_result['result']['observed_value']}")
# </snippet>

assert validation_result["success"] is False
assert validation_result["result"]["observed_value"] == datetime.datetime(
    2024, 11, 22, 14, 49
)
