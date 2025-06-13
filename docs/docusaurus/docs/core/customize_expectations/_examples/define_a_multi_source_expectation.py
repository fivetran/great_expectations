"""
This is an example script for how to define a Multi-source Expectation.

To test, run:
pytest --docs-tests -k "docs_example_define_a_multi_source_expectation" tests/integration/test_script_runner.py
"""


def set_up_context_for_example(context):
    # Create the Data Source
    connection_string = "sqlite:///data/yellow_tripdata.db"
    data_source_name = "my_base_data_source"
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


def set_up_context2_for_example(context):
    # Create the Data Source
    connection_string2 = "sqlite:///data/yellow_tripdata.db"
    data_source_name2 = "my_comparison_data_source"
    data_source2 = context.data_sources.add_sqlite(
        name=data_source_name2, connection_string=connection_string2
    )
    assert data_source2.name == data_source_name2

    # Add a Data Asset
    asset_name2 = "my_data_asset2"
    database_table_name = "yellow_tripdata_sample_2019_01"
    data_asset2 = data_source2.add_table_asset(
        table_name=database_table_name, name=asset_name2
    )
    assert data_asset2.name == asset_name2


# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/define_a_multi_source_expectation.py - full code example">
import great_expectations as gx

# Define your comparison Data Source.
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/define_a_multi_source_expectation.py - define comparison Data Source">
my_upstream_source = "my_comparison_data_source"
# </snippet>


# Define your base and comparison SQL queries.
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/define_a_multi_source_expectation.py - define queries">
my_base_query = """
    SELECT
        *
    FROM
        my_downstream_table
    WHERE
        passenger_count > 0
    """

my_comparison_query = """
    SELECT
        *
    FROM
        my_upstream_table
    WHERE
        passenger_count > 0
    """
# </snippet>

# Customize how the Expectation renders in Data Docs.
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/define_a_multi_source_expectation.py - define description">
my_description = "Both tables should have the same rows with passengers."
# </snippet>

# Create an Expectation using the ExpectQueryResultsToMatchComparison class and your parameters.
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/define_a_multi_source_expectation.py - create Expectation">
expect_passenger_rows_to_match = gx.expectations.ExpectQueryResultsToMatchComparison(
    base_query=my_base_query,
    comparison_data_source_name=my_upstream_source,
    comparison_query=my_comparison_query,
    mostly=1,
    description=my_description,
)
# </snippet>

# Test the Expectation.
context = gx.get_context()
# Hide this
set_up_context_for_example(context)
# Hide this
set_up_context2_for_example(context)

data_source_name = "my_base_data_source"
data_asset_name = "my_data_asset"
batch_definition_name = "my_batch_definition"
batch = (
    context.data_sources.get(data_source_name)
    .get_asset(data_asset_name)
    .get_batch_definition(batch_definition_name)
    .get_batch()
)

batch.validate(expect_passenger_rows_to_match)
# </snippet>
