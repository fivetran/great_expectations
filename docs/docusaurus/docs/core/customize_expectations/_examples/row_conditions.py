"""
This is an example script for how to use row conditions.

To test, run:
pytest --docs-tests -k "docs_example_row_conditions" tests/integration/test_script_runner.py
"""


def set_up_context_for_example(context):
    # Create the Data Source
    source_folder = "./data/folder_with_data"
    data_source_name = "my_data_source"
    data_source = context.data_sources.add_pandas_filesystem(
        name=data_source_name, base_directory=source_folder
    )
    assert data_source.name == data_source_name

    # Add a Data Asset
    asset_name = "my_data_asset"
    data_asset = data_source.add_csv_asset(name=asset_name)
    assert data_asset.name == asset_name

    # Add a Batch Definition
    batch_definition_name = "titantic_passengers"
    batch_definition_path = "titantic.csv"

    batch_definition = data_asset.add_batch_definition_path(
        name=batch_definition_name, path=batch_definition_path
    )
    assert batch_definition.name == batch_definition_name

    invoices_batch_definition = data_asset.add_batch_definition_path(
        name="invoices", path="invoices.csv"
    )
    assert invoices_batch_definition.name == "invoices"


# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/row_conditions.py - full code example">
import great_expectations as gx

context = gx.get_context()
# Hide this
set_up_context_for_example(context)

# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/row_conditions.py - determine expression">
from great_expectations.expectations.row_conditions import Column

# Create condition statements with column references and Python comparisons.
statement_1 = Column("tenure") > 2
statement_2 = Column("salary") <= 50000
statement_3 = Column("department") == "Sales"

# Combine condition statements with an AND relationship into condition blocks.
block_1 = statement_1 & statement_2
block_2 = statement_3

# Combine condition blocks with OR.
row_condition = block_1 | block_2
# </snippet>

# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/row_conditions.py - add Expectation">
# Add the `row_condition` parameter alongside the Expectation's other arguments.
expectation = gx.expectations.ExpectColumnValuesToBeBetween(
    column="bonus", min_value=5000, max_value=10000, row_condition=row_condition
)
# </snippet>
# </snippet>


# Get a Batch for testing the Expectations:
data_source_name = "my_data_source"
data_asset_name = "my_data_asset"
batch_definition_name = "titantic_passengers"
batch = (
    context.data_sources.get(data_source_name)
    .get_asset(data_asset_name)
    .get_batch_definition(batch_definition_name)
    .get_batch()
)

# An Expectation without conditions is defined without the `row_condition` parameter:
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/row_conditions.py - Expectation without row conditions">
expectation_without_row_conditions = (
    gx.expectations.ExpectColumnDistinctValuesToBeInSet(
        column="cycle_type", value_set=["unicycle", "bicycle", "tricycle"]
    )
)
# </snippet>

# Test the Expectation:
print(batch.validate(expectation_without_row_conditions))

# An Expectation with row conditions would be defined like this:
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/row_conditions.py - Expectation with row conditions">
expectation_with_row_conditions = gx.expectations.ExpectColumnValuesToBeInSet(
    column="cycle_type",
    value_set=["unicycle"],
    row_condition=(Column("wheels") == 1),
)
# </snippet>


# Test the Expectation condition:
print(batch.validate(expectation_with_row_conditions))

# common patterns for row conditions

# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/row_conditions.py - a and b">
# Two condition statements within a single condition block.

statement_1 = Column("A") == "a"
statement_2 = Column("B") == "b"

block_1 = statement_1 & statement_2

row_condition = block_1
# </snippet>

# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/row_conditions.py - a or b">
# Two condition statements, each in its own condition block.

statement_1 = Column("A") == "a"
statement_2 = Column("B") == "b"

block_1 = statement_1
block_2 = statement_2

row_condition = block_1 | block_2
# </snippet>

# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/row_conditions.py - a and b or c and d">
# Two condition statements in one condition block and two statements in another block.

statement_1 = Column("A") == "a"
statement_2 = Column("B") == "b"
statement_3 = Column("C") == "c"
statement_4 = Column("D") == "d"

block_1 = statement_1 & statement_2
block_2 = statement_3 & statement_4

row_condition = block_1 | block_2
# </snippet>

# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/row_conditions.py - a and b or c">
# Two condition statements in one condition block and two statements in another block.

statement_1 = Column("A") == "a"
statement_2 = Column("B") == "b"
statement_3 = Column("C") == "c"

block_1 = statement_1 & statement_2
block_2 = statement_1 & statement_3

row_condition = block_1 | block_2
# </snippet>

from datetime import datetime, timezone

# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/row_conditions.py - operators">
# Single value comparisons: ==, !=, >, <, >=, <=
statement_1 = Column("count") == 1
statement_2 = Column("date") > datetime(year=2025, month=1, day=31, tzinfo=timezone.utc)

# Column comparisons: ==, !=, >, <, >=, <= with another column on the right-hand side
statement_column_comparison = Column("end_date") > Column("start_date")

# Set comparisons: is_in, is_not_in
statement_3 = Column("department").is_in(["sales", "finance"])

# Nullity checks: is_null, is_not_null
statement_4 = Column("name").is_null()

# </snippet>


# The column comparison examples use a table of invoices.
invoices_batch = (
    context.data_sources.get(data_source_name)
    .get_asset(data_asset_name)
    .get_batch_definition("invoices")
    .get_batch()
)

# Compare the values in two columns of the same row.
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/row_conditions.py - compare two columns">
from great_expectations.expectations.row_conditions import Column

# Put a `Column` on the right-hand side to compare two columns row by row.
# An invoice that was paid less than it was billed for must not be marked as paid.
row_condition = Column("amount_paid") < Column("amount_due")

expectation_with_column_comparison = gx.expectations.ExpectColumnValuesToBeInSet(
    column="status",
    value_set=["unpaid", "partially_paid"],
    row_condition=row_condition,
)
# </snippet>

# Test the Expectation condition. Only the 4 of 10 invoices that were paid less than the
# amount due are validated.
column_comparison_result = invoices_batch.validate(expectation_with_column_comparison)
assert column_comparison_result.success
assert column_comparison_result.result["element_count"] == 4

# A row with a null in either column is left out of a column comparison.
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/row_conditions.py - include null rows in a column comparison">
from great_expectations.expectations.row_conditions import OrCondition

underpaid = Column("amount_paid") < Column("amount_due")

# An invoice with no payment recorded has a null `amount_paid`. To validate rows with a null
# in either column as well, add a null check for each column.
# Build the OR group with `OrCondition`. Chaining three conditions with `|` creates a
# nested OR, which is not allowed.
row_condition = OrCondition(
    conditions=[
        underpaid,
        Column("amount_paid").is_null(),
        Column("amount_due").is_null(),
    ]
)

expectation_with_null_rows = gx.expectations.ExpectColumnValuesToBeInSet(
    column="status",
    value_set=["unpaid", "partially_paid"],
    row_condition=row_condition,
)
# </snippet>

# Test the Expectations. The 2 invoices with a null `amount_paid` are validated only with the
# null checks.
without_nulls_result = invoices_batch.validate(
    gx.expectations.ExpectColumnValuesToBeInSet(
        column="status",
        value_set=["unpaid", "partially_paid"],
        row_condition=underpaid,
    )
)
assert without_nulls_result.success
assert without_nulls_result.result["element_count"] == 4

with_nulls_result = invoices_batch.validate(expectation_with_null_rows)
assert with_nulls_result.success
assert with_nulls_result.result["element_count"] == 6
