"""
This is an example script for how to use Expectation conditions.

To test, run:
pytest --docs-tests -k "docs_example_expectation_conditions" tests/integration/test_script_runner.py
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


# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/expectation_conditions.py - full code example">
import great_expectations as gx

context = gx.get_context()
# Hide this
set_up_context_for_example(context)

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

# An Expectation without conditions is defined without the `row_condition` or `condition_parser` parameters:
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/expectation_conditions.py - example Expectation without conditions">
expectation = gx.expectations.ExpectColumnValuesToBeInSet(
    column="Survived", value_set=[0, 1]
)
# </snippet>

# Test the Expectation:
print(batch.validate(expectation))

# An Expectation condition for a pandas Data Source would be defined like this:
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/expectation_conditions.py - pandas example Expectation with conditions">
expectation_with_condition = gx.expectations.ExpectColumnValuesToBeInSet(
    column="Survived",
    value_set=[1],
    # <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/expectation_conditions.py - pandas example row_condition">
    condition_parser="pandas",
    row_condition='PClass=="1st"',
    # </snippet>
)
# </snippet>

# Test the Expectation condition:
print(batch.validate(expectation_with_condition))

# A Conditional Expectation for a Spark Data Source would be defined like this:
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/expectation_conditions.py - spark example Expectation with conditions">
expectation_with_condition = gx.expectations.ExpectColumnValuesToBeInSet(
    column="Survived",
    value_set=[1],
    # <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/expectation_conditions.py - spark example row_condition">
    condition_parser="great_expectations",
    row_condition='col("PClass")=="1st"',
    # </snippet>
)
# </snippet>

# A Conditional Expectation for a SQL Data Source would be defined like this:
# <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/expectation_conditions.py - sql example Expectation with conditions">
expectation_with_condition = gx.expectations.ExpectColumnValuesToBeInSet(
    column="Survived",
    value_set=[1],
    # <snippet name="docs/docusaurus/docs/core/customize_expectations/_examples/expectation_conditions.py - sql example row_condition">
    condition_parser="great_expectations",
    row_condition='col("PClass")=="1st"',
    # </snippet>
)
# </snippet>
# </snippet>
