"""
This is an example script for how to retrieve all unexpected rows.

To test, run:
pytest --docs-tests -k "docs_example_retrieve_all_unexpected_rows" tests/integration/test_script_runner.py
"""


def set_up_context_for_example(context):
    connection_string = "sqlite:///data/yellow_tripdata.db"
    data_source = context.data_sources.add_sqlite(
        name="my_sql_data_source", connection_string=connection_string
    )

    data_asset = data_source.add_table_asset(
        table_name="yellow_tripdata_sample_2019_01", name="my_data_asset"
    )

    batch_definition = data_asset.add_batch_definition_whole_table(
        "my_batch_definition"
    )

    import great_expectations as gx
    from great_expectations.expectations import UnexpectedRowsExpectation

    class ExpectNoLongTrips(UnexpectedRowsExpectation):
        unexpected_rows_query: str = "SELECT * FROM {batch} WHERE trip_distance > 20"
        description = "No trip should exceed 20 miles."

    suite = context.suites.add(
        gx.ExpectationSuite(
            name="my_expectation_suite",
            expectations=[ExpectNoLongTrips()],
        )
    )

    context.validation_definitions.add(
        gx.ValidationDefinition(
            data=batch_definition,
            suite=suite,
            name="my_validation_definition",
        )
    )


# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/core/run_validations/_examples/retrieve_all_unexpected_rows.py - full code example">
import great_expectations as gx
from great_expectations.expectations import UnexpectedRowsExpectation

context = gx.get_context()
# Hide this
set_up_context_for_example(context)

# Retrieve your Validation Definition
# <snippet name="docs/docusaurus/docs/core/run_validations/_examples/retrieve_all_unexpected_rows.py - retrieve Validation Definition">
validation_definition_name = "my_validation_definition"
validation_definition = context.validation_definitions.get(validation_definition_name)
# </snippet>

# Run the Validation Definition
# <snippet name="docs/docusaurus/docs/core/run_validations/_examples/retrieve_all_unexpected_rows.py - run validation">
result = validation_definition.run()
# </snippet>

# Iterate over results and retrieve all unexpected rows for each failing UnexpectedRowsExpectation
# <snippet name="docs/docusaurus/docs/core/run_validations/_examples/retrieve_all_unexpected_rows.py - retrieve unexpected rows">
for evr in result.results:
    # Filter by status and type because get_unexpected_rows() supports only UnexpectedRowsExpectation
    if not evr.success and isinstance(evr.expectation, UnexpectedRowsExpectation):
        unexpected_rows = validation_definition.get_unexpected_rows(
            evr.expectation,
            batch_parameters=result.batch_parameters,
        )
        print(f"{len(unexpected_rows)} unexpected rows found")
# </snippet>
# </snippet>
