"""
This is an example script for how to use SQL to define a custom Expectation.

To test, run:
pytest --docs-tests -k "docs_example_use_sql_to_define_a_custom_expectation" tests/integration/test_script_runner.py
"""


def set_up_context_for_example(context):
    # Create the Data Source
    connection_string = "sqlite:///data/yellow_tripdata.db"
    data_source_name = "my_sql_data_source"
    data_source = context.data_sources.add_sqlite(
        name=data_source_name, connection_string=connection_string
    )
    assert data_source.name == data_source_name

    # Add a Data Asset
    asset_name = "my_data_asset"
    database_table_name = "yellow_tripdata_sample_2019_01"
    data_asset = data_source.add_table_asset(
        table_name=database_table_name, name=asset_name
    )
    assert data_asset.name == asset_name

    # Add a Batch Definition
    batch_definition_name = "my_batch_definition"
    batch_definition = data_asset.add_batch_definition_whole_table(
        batch_definition_name
    )
    assert batch_definition.name == batch_definition_name


# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/use_sql_to_define_a_custom_expectation.py - full code example">
import great_expectations as gx

# Define your custom SQL query.
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/use_sql_to_define_a_custom_expectation.py - define query">
my_query = """
    SELECT
        *
    FROM
        {batch}
    WHERE
        passenger_count > 6 or passenger_count < 0
    """
# </snippet>

# Customize how the Expectation renders in Data Docs.
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/use_sql_to_define_a_custom_expectation.py - define description">
my_description = "There should be no more than **6** passengers."
# </snippet>

# Create an Expectation using the UnexpectedRowsExpectation class and your parameters.
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/use_sql_to_define_a_custom_expectation.py - create Expectation">
expect_passenger_count_to_be_legal = gx.expectations.UnexpectedRowsExpectation(
    unexpected_rows_query=my_query,
    description=my_description,
)
# </snippet>

# Test the Expectation.
context = gx.get_context()
# Hide this
set_up_context_for_example(context)

data_source_name = "my_sql_data_source"
data_asset_name = "my_data_asset"
batch_definition_name = "my_batch_definition"
batch = (
    context.data_sources.get(data_source_name)
    .get_asset(data_asset_name)
    .get_batch_definition(batch_definition_name)
    .get_batch()
)

batch.validate(expect_passenger_count_to_be_legal)
# </snippet>

# TEMPLATE EXAMPLE:
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/use_sql_to_define_a_custom_expectation.py - full template example">
import great_expectations as gx

# Define a reusable SQL query with template variables.
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/use_sql_to_define_a_custom_expectation.py - define template query">
my_template_query = """
    SELECT
        *
    FROM
        {batch}
    WHERE
        {column} > {max_value} or {column} < {min_value}
    """

# Define the template dictionary with column name and threshold values
my_template_dict = {"column": "passenger_count", "max_value": "6", "min_value": "0"}
# </snippet>

# Create an Expectation with template variables
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/use_sql_to_define_a_custom_expectation.py - create template Expectation">
expect_column_values_in_range = gx.expectations.UnexpectedRowsExpectation(
    unexpected_rows_query=my_template_query,
    template_dict=my_template_dict,
    description="Values should be within the specified range.",
)
# </snippet>

# Test the template-based Expectation
context = gx.get_context()
# Hide this
set_up_context_for_example(context)

batch = (
    context.data_sources.get("my_sql_data_source")
    .get_asset("my_data_asset")
    .get_batch_definition("my_batch_definition")
    .get_batch()
)

# Validate with the template-based expectation
result = batch.validate(expect_column_values_in_range)

# You can also create another expectation for a different column using the same query template
expect_fare_amount_reasonable = gx.expectations.UnexpectedRowsExpectation(
    unexpected_rows_query=my_template_query,
    template_dict={"column": "fare_amount", "max_value": "500", "min_value": "0"},
    description="Fare amounts should be reasonable.",
)

# Validate with the new expectation
result2 = batch.validate(expect_fare_amount_reasonable)
# </snippet>

# ADVANCED TEMPLATE EXAMPLE WITH MULTIPLE COLUMNS:
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/use_sql_to_define_a_custom_expectation.py - advanced template example">
# Example: Check consistency between two related columns
consistency_query = """
    SELECT
        *
    FROM
        {batch}
    WHERE
        {column_a} IS NOT NULL AND {column_b} IS NULL
        OR
        {column_a} IS NULL AND {column_b} IS NOT NULL
"""

# Create an expectation to ensure pickup and dropoff times are both present or both missing
expect_datetime_consistency = gx.expectations.UnexpectedRowsExpectation(
    unexpected_rows_query=consistency_query,
    template_dict={"column_a": "pickup_datetime", "column_b": "dropoff_datetime"},
    description="Pickup and dropoff times should be both present or both null.",
)

# Example: Dynamic threshold checking
threshold_query = """
    SELECT
        *
    FROM
        {batch}
    WHERE
        {metric_column} / NULLIF({base_column}, 0) > {threshold}
"""

# Create an expectation to check if tips exceed a certain percentage of fare
expect_reasonable_tip_percentage = gx.expectations.UnexpectedRowsExpectation(
    unexpected_rows_query=threshold_query,
    template_dict={
        "metric_column": "tip_amount",
        "base_column": "fare_amount",
        "threshold": "0.5",  # Flag if tip is more than 50% of fare
    },
    description="Tips should not exceed 50% of the fare amount.",
)
# </snippet>
