"""
To run this test locally, use the postgresql database docker container.

1. From the repo root dir, run:
cd assets/docker/postgresql
docker compose up

2. Run the following command from the repo root dir in a second terminal:
pytest --postgresql --docs-tests -k "data_quality_use_case_integrity_expectations" tests/integration/test_script_runner.py
"""

# This section loads sample data to use for CI testing of the script.
import pathlib

import great_expectations as gx
import great_expectations.expectations as gxe
from tests.test_utils import load_data_into_test_database

CONNECTION_STRING = "postgresql+psycopg2://postgres:@localhost/test_ci"

GX_ROOT_DIR = pathlib.Path(gx.__file__).parent.parent


def load_sample_data(sample_dataset_name: str):
    """Add sample data to database for testing."""
    load_data_into_test_database(
        table_name=sample_dataset_name,
        csv_path=str(
            GX_ROOT_DIR
            / f"tests/test_sets/learn_data_quality_use_cases/{sample_dataset_name}.csv"
        ),
        connection_string=CONNECTION_STRING,
    )


for sample_data in [
    "integrity_transfers",
    "integrity_transfer_balance",
    "integrity_transfer_transaction",
]:
    load_sample_data(sample_data)

context = gx.get_context()

datasource = context.data_sources.add_postgres(
    "postgres database", connection_string=CONNECTION_STRING
)

# Define transfer transaction data.
data_asset_transfer_transaction = datasource.add_table_asset(
    name="transfer transaction", table_name="integrity_transfer_transaction"
)
batch_definition_transfer_transaction = (
    data_asset_transfer_transaction.add_batch_definition_whole_table("batch definition")
)
batch_transfer_transaction = batch_definition_transfer_transaction.get_batch()

# Define transfer balance data.
data_asset_transfer_balance = datasource.add_table_asset(
    name="transfer balance", table_name="integrity_transfer_transaction"
)
batch_definition_transfer_balance = (
    data_asset_transfer_balance.add_batch_definition_whole_table("batch definition")
)
batch_transfer_balance = batch_definition_transfer_balance.get_batch()

# Create Expectation Suites.
suite_transfer_transaction = context.suites.add(
    gx.ExpectationSuite(name="transfer transaction: integrity expectations")
)

suite_transfer_balance = context.suites.add(
    gx.ExpectationSuite(name="transfer balance: integrity expectations")
)


#############################
# Start Expectation snippets.

suite_transfer_transaction.add_expectation(
    # <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/integrity_resources/integrity_expectations.py ExpectColumnPairValuesToBeEqual">
    gxe.ExpectColumnPairValuesToBeEqual(
        column_A="sender_ref_no", column_B="recipient_conf_code"
    )
    # </snippet>
)

suite_transfer_transaction.add_expectation(
    # <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/integrity_resources/integrity_expectations.py ExpectColumnPairValuesAToBeGreaterThanB">
    gxe.ExpectColumnPairValuesAToBeGreaterThanB(
        column_A="received_ts", column_B="sent_ts", or_equal=True
    )
    # </snippet>
)

suite_transfer_balance.add_expectation(
    # <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/integrity_resources/integrity_expectations.py ExpectMulticolumnSumToEqual">
    gxe.ExpectMulticolumnSumToEqual(
        column_list=["adjustment", "sender_debit", "recipient_credit"], sum_total=0
    )
    # </snippet>
)

# Test that Expectations run.
batch_transfer_transaction.validate(suite_transfer_transaction)
batch_transfer_balance.validate(suite_transfer_balance)
