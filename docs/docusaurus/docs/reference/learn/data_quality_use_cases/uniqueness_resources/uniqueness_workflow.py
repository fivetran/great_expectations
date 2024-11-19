"""
To run this test locally, use the postgresql database docker container.

1. From the repo root dir, run:
cd assets/docker/postgresql
docker compose up

2. Run the following command from the repo root dir in a second terminal:
pytest --postgresql --docs-tests -k "data_quality_use_case_uniqueness_workflow" tests/integration/test_script_runner.py
"""

# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/uniqueness_resources/uniqueness_workflow.py full workflow">
import great_expectations as gx

# Create Data Context.
context = gx.get_context()

# Connect to data.
# Create Data Source, Data Asset, Batch Definition, and Batch.
CONNECTION_STRING = "postgresql+psycopg2://try_gx:try_gx@postgres.workshops.greatexpectations.io/gx_learn_data_quality"

data_source = context.data_sources.add_postgres(
    "postgres database", connection_string=CONNECTION_STRING
)
data_asset = data_source.add_table_asset(
    name="purchases", table_name="uniqueness_customers"
)

batch_definition = data_asset.add_batch_definition_whole_table("batch definition")
batch = batch_definition.get_batch()

# Create an Expectation Suite containing distribution Expectations.
expectation_suite = context.suites.add(gx.ExpectationSuite(name="expectation suite"))

# Validate Batch using Expectation.
validation_result = batch.validate(expectation_suite)
# </snippet>
