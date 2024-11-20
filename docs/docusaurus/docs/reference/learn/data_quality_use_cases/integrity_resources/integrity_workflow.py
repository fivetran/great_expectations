"""
To run this test locally, use the postgresql database docker container.

1. From the repo root dir, run:
cd assets/docker/postgresql
docker compose up

2. Run the following command from the repo root dir in a second terminal:
pytest --postgresql --docs-tests -k "data_quality_use_case_integrity_workflow" tests/integration/test_script_runner.py
"""


# ruff: noqa: I001
# Adding noqa rule so two import sections can be used for two examples.

# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/integrity_resources/integrity_workflow.py business logic workflow">
import great_expectations as gx
import great_expectations.expectations as gxe

# Create Data Context.
context = gx.get_context()

# Connect to data and create Data Source.
CONNECTION_STRING = """
postgresql+psycopg2://try_gx:try_gx@postgres.workshops.greatexpectations.io/gx_learn_data_quality
"""

data_source = context.data_sources.add_postgres(
    "postgres", connection_string=CONNECTION_STRING
)

# Create Data Asset, Batch Definition, and Batch.
data_asset_transfer_txn = data_source.add_table_asset(
    name="transfer transaction", table_name="integrity_transfer_transaction"
)
batch_def_transfer_txn = data_asset_transfer_txn.add_batch_definition_whole_table(
    "transfer transaction batch definition"
)
batch_transfer_txn = batch_def_transfer_txn.get_batch()

# Create an integrity check using a built-in Expectation.
built_in_expectation = gxe.ExpectColumnPairValuesAToBeGreaterThanB(
    column_A="received_ts", column_B="sent_ts"
)

validation_result_built_in_expectation = batch_transfer_txn.validate(
    built_in_expectation
)


# Create an integrity check with custom business logic using a custom SQL Expectation.
# (Create custom SQL Expectation by subclassing gxe.UnexpectedRowsExpectation).
class ExpectTransfersToArriveWithin45Seconds(gxe.UnexpectedRowsExpectation):
    """Expectation to validate that transfers are sent (`sent_ts`) and received (`received_ts`) within 45 seconds."""

    description = "Transfers arrive within 45 seconds"

    unexpected_rows_query = """
        select *
        from {batch}
        where extract(epoch from (age(received_ts, sent_ts))) > 45
    """


validation_result_custom_sql_expectation = batch_transfer_txn.validate(
    ExpectTransfersToArriveWithin45Seconds()
)
# </snippet>

assert validation_result_built_in_expectation["success"] is True
assert validation_result_custom_sql_expectation["success"] is False


# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/integrity_resources/integrity_workflow.py cross-table workflow">
import great_expectations as gx
import great_expectations.expectations as gxe

# Create Data Context.
context = gx.get_context()

# Connect to data and create Data Source.
CONNECTION_STRING = """
postgresql+psycopg2://try_gx:try_gx@postgres.workshops.greatexpectations.io/gx_learn_data_quality
"""

data_source = context.data_sources.add_postgres(
    "postgres", connection_string=CONNECTION_STRING
)

# Create Data Asset, Batch Definition, and Batch.
data_asset_transfers = data_source.add_table_asset(
    name="transfers", table_name="integrity_transfers"
)
batch_def_transfers = data_asset_transfers.add_batch_definition_whole_table(
    "transfers batch definition"
)
batch_transfers = batch_def_transfers.get_batch()


# Create custom SQL Expectation by subclassing gxe.UnexpectedRowsExpectation.
class ExpectTransferAmountsToMatch(gxe.UnexpectedRowsExpectation):
    """Expectation to validate that transfer amounts in `integrity_transfers` and `integrity_transfer_balance` tables match."""

    description = (
        "Transfer amounts in integrity_transfers and integrity_transfer_balance match."
    )

    unexpected_rows_query = """
        select *
        from {batch} t
        join integrity_transfer_balance b using (transfer_balance_id)
        where t.amount <> b.total_amount
    """


# Validate Batch using custom SQL Expectations.
validation_result = batch_transfers.validate(ExpectTransferAmountsToMatch())
# </snippet>

assert validation_result["success"] is True
