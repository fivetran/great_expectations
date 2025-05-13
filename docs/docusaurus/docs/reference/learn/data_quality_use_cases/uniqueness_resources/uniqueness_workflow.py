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
import great_expectations.expectations as gxe

# Create a Data Context.
context = gx.get_context(mode="ephemeral")

# Connect to data and create the Data Source, Data Asset, Batch Definition, and Batch.
CONNECTION_STRING = "postgresql+psycopg2://try_gx:try_gx@postgres.workshops.greatexpectations.io/gx_learn_data_quality"

data_source = context.data_sources.add_postgres(
    "postgres database", connection_string=CONNECTION_STRING
)
data_asset = data_source.add_table_asset(
    name="customers", table_name="uniqueness_customers"
)

batch_definition = data_asset.add_batch_definition_whole_table("batch definition")
batch = batch_definition.get_batch()

# Create an Expectation Suite containing uniqueness Expectations.
expectation_suite = context.suites.add(gx.ExpectationSuite(name="expectation suite"))


# Validate uniqueness of the primary key column.
expectation_suite.add_expectation(
    gxe.ExpectColumnValuesToBeUnique(
        column="customer_id",
    )
)

# Validate composite keys that potentially represent a single entity
# (the individual customer) for uniqueness.
expectation_suite.add_expectation(
    gxe.ExpectCompoundColumnsToBeUnique(column_list=["country_code", "government_id"])
)

expectation_suite.add_expectation(
    gxe.ExpectCompoundColumnsToBeUnique(column_list=["last_name", "phone_number"])
)

# Validate the Batch using the uniqueness Expectation Suite.
validation_result = batch.validate(expectation_suite)

# Parse the Validation Result for potential duplicate customers.
for expectation_result in validation_result["results"]:
    expectation = expectation_result["expectation_config"]["type"]
    result = expectation_result["success"]

    if result is False:
        unexpected_sample = expectation_result["result"]["partial_unexpected_list"]
        print(
            f"Expectation: {expectation}, Potential duplicates found:\n{unexpected_sample}\n"
        )
# </snippet>


# Test for expected output.
result_summary = []

for expectation_result in validation_result["results"]:
    expectation = expectation_result["expectation_config"]["type"]
    result = expectation_result["success"]

    if result is False:
        unexpected_sample = expectation_result["result"]["partial_unexpected_list"]
        result_summary.append(
            {"expectation": expectation, "potential duplicate": unexpected_sample}
        )

first_result = result_summary[0]
assert first_result["expectation"] == "expect_compound_columns_to_be_unique"
assert first_result["potential duplicate"][0]["country_code"] == "US"
assert first_result["potential duplicate"][0]["government_id"] == "123-45-6789"

second_result = result_summary[1]
assert second_result["expectation"] == "expect_compound_columns_to_be_unique"
assert second_result["potential duplicate"][0]["last_name"] == "Brown"
assert second_result["potential duplicate"][0]["phone_number"] == "+44 1224 587623"
