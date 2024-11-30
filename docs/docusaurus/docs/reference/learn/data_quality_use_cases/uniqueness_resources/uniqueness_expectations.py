"""
To run this test locally, use the postgresql database docker container.

1. From the repo root dir, run:
cd assets/docker/postgresql
docker compose up

2. Run the following command from the repo root dir in a second terminal:
pytest --postgresql --docs-tests -k "data_quality_use_case_uniqueness_expectations" tests/integration/test_script_runner.py
"""

# This section loads sample data to use for CI testing of the script.
import pathlib

import great_expectations as gx
import great_expectations.expectations as gxe
from tests.test_utils import load_data_into_test_database

CONNECTION_STRING = "postgresql+psycopg2://postgres:@localhost/test_ci"

GX_ROOT_DIR = pathlib.Path(gx.__file__).parent.parent

# Add test data to database for testing.
load_data_into_test_database(
    table_name="uniqueness_customers",
    csv_path=str(
        GX_ROOT_DIR
        / "tests/test_sets/learn_data_quality_use_cases/uniqueness_customers.csv"
    ),
    connection_string=CONNECTION_STRING,
)

context = gx.get_context()

datasource = context.data_sources.add_postgres(
    "postgres database", connection_string=CONNECTION_STRING
)

data_asset = datasource.add_table_asset(
    name="data asset", table_name="uniqueness_customers"
)
batch_definition = data_asset.add_batch_definition_whole_table("batch definition")
batch = batch_definition.get_batch()

suite = context.suites.add(gx.ExpectationSuite(name="example uniqueness expectations"))

#############################
# Start Expectation snippets.

suite.add_expectation(
    # <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/uniqueness_resources/uniqueness_expectations.py ExpectColumnValuesToBeUnique">
    gxe.ExpectColumnValuesToBeUnique(column="customer_id")
    # </snippet>
)

suite.add_expectation(
    # <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/uniqueness_resources/uniqueness_expectations.py ExpectCompoundColumnsToBeUnique">
    gxe.ExpectCompoundColumnsToBeUnique(
        column_list=["country_code", "government_id"],
    )
    # </snippet>
)

suite.add_expectation(
    # <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/uniqueness_resources/uniqueness_expectations.py ExpectColumnProportionOfUniqueValuesToBeBetween">
    gxe.ExpectColumnProportionOfUniqueValuesToBeBetween(
        column="email_address", min_value=0.9, max_value=1.0
    )
    # </snippet>
)

suite.add_expectation(
    # <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/uniqueness_resources/uniqueness_expectations.py ExpectColumnUniqueValueCountToBeBetween">
    gxe.ExpectColumnUniqueValueCountToBeBetween(
        column="country_code", min_value=1, max_value=5
    )
    # </snippet>
)

suite.add_expectation(
    # <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/uniqueness_resources/uniqueness_expectations.py ExpectSelectColumnValuesToBeUniqueWithinRecord">
    gxe.ExpectSelectColumnValuesToBeUniqueWithinRecord(
        column_list=["email_address", "secondary_email"],
    )
    # </snippet>
)


results = batch.validate(suite)
