"""
To run this test locally, use the postgresql database docker container.

1. From the repo root dir, run:
cd assets/docker/postgresql
docker compose up

2. Run the following command from the repo root dir in a second terminal:
pytest --postgresql --docs-tests -k "data_quality_use_case_integrity_workflow" tests/integration/test_script_runner.py
"""

# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/integrity_resources/integrity_workflow.py full workflow">
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

# Create Data Asset, Batch Definition, and Batch for each sample data table.

# integrity_transfer:
data_asset_transfers = data_source.add_table_asset(
    name="transfers", table_name="integrity_transfers"
)
batch_def_transfers = data_asset_transfers.add_batch_definition_whole_table(
    "transfers batch definition"
)
batch_transfers = batch_def_transfers.get_batch()

# integrity_transfer_balance:
data_asset_transfer_balance = data_source.add_table_asset(
    name="transfer balance", table_name="integrity_transfer_balance"
)
batch_def_transfer_balance = (
    data_asset_transfer_balance.add_batch_definition_whole_table(
        "transfer balance batch definition"
    )
)
batch_transfer_balance = batch_def_transfer_balance.get_batch()

# integrity_transfer_transaction:
data_asset_transfer_txn = data_source.add_table_asset(
    name="transfer transaction", table_name="integrity_transfer_transaction"
)
batch_def_transfer_txn = data_asset_transfer_txn.add_batch_definition_whole_table(
    "transfer transaction batch definition"
)
batch_transfer_txn = batch_def_transfer_txn.get_batch()


# Create custom SQL Expectations by subclassing gxe.UnexpectedRowsExpectation.
class ExpectTransferAmountsToMatch(gxe.UnexpectedRowsExpectation):
    """Expectation to validate that transfer amounts in `integrity_transfers` and `integrity_transfer_balance` tables match."""

    description = (
        "Transfer amounts in integrity_transfers and integrity_transfer_balance match."
        ""
    )

    unexpected_rows_query = """
        select *
        from {batch} t
        join integrity_transfer_balance b using (transfer_balance_id)
        where t.amount <> b.total_amount
    """


class ExpectRecipientCreditToEqualSenderDebitAndAdjustment(
    gxe.UnexpectedRowsExpectation
):
    """Expectation to validate that for each row in the `integrity_transfer_balance` table, `recipient_credit` is equal to the absolute value of the `sender_debit` and `adjustment`."""

    description = "recipient credit = abs(sender_credit + adjustment)" ""

    unexpected_rows_query = """
        select *
        from {batch}
        where recipient_credit <> abs(sender_debit + adjustment)
    """


class ExpectTransfersToArriveWithin1Minute(gxe.UnexpectedRowsExpectation):
    """Expectation to validate that transfers are sent (`sent_ts`) and received (`received_ts`) within 60 seconds."""

    description = "Transfers arrive within one minute" ""

    unexpected_rows_query = """
        select *
        from {batch}
        where extract(epoch from (age(received_ts, sent_ts))) > 60
    """


# Validate table (Batches) using custom SQL Expectations.
validation_result_1 = batch_transfers.validate(ExpectTransferAmountsToMatch())
validation_result_2 = batch_transfer_balance.validate(
    ExpectRecipientCreditToEqualSenderDebitAndAdjustment()
)
validation_result_3 = batch_transfer_txn.validate(
    ExpectTransfersToArriveWithin1Minute()
)
# </snippet>

for idx, result in enumerate(
    [validation_result_1, validation_result_2, validation_result_3]
):
    assert result["success"] is True
