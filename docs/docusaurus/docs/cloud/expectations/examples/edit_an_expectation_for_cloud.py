"""
This is an example script for editing the parameters of an expectation.

To test, run:
pytest --docs-tests -k "doc_example_edit_an_expectation_for_cloud" tests/integration/test_script_runner.py
"""


def set_up_context_for_example(context):
    expectation = gx.expectations.ExpectColumnMaxToBeBetween(
        column="passenger_count", min_value=1, max_value=6, severity="warning"
    )
    suite = context.suites.get(name="my_expectation_suite")
    suite.add_expectation(expectation)
    sql_expectation = gx.expectations.UnexpectedRowsExpectation(
        description="My custom SQL Expectation",
        unexpected_rows_query="select 1 from table",
    )
    suite.add_expectation(sql_expectation)
    suite.save()


# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/cloud/expectations/examples/edit_an_expectation_for_cloud.py - get cloud context">
import great_expectations as gx

context = gx.get_context()
# </snippet>
# Hide this
set_up_context_for_example(context)

# Get the Expectation Suite using its name
# <snippet name="docs/docusaurus/docs/cloud/expectations/examples/edit_an_expectation_for_cloud.py - get the expectation suite">
suite = context.suites.get(name="my_expectation_suite")
# </snippet>

# Find the Expectation to edit by matching on the type and column
# <snippet name="docs/docusaurus/docs/cloud/expectations/examples/edit_an_expectation_for_cloud.py - find the expectation">
expectation = [
    exp
    for exp in suite.expectations
    if type(exp).__name__ == "ExpectColumnMaxToBeBetween"
    and exp.column == "passenger_count"
][0]
# </snippet>

# Find the Expectation to edit by matching on the description
# <snippet name="docs/docusaurus/docs/cloud/expectations/examples/edit_an_expectation_for_cloud.py - find the custom sql expectation">
sql_expectation = [
    exp for exp in suite.expectations if exp.description == "My custom SQL Expectation"
][0]
# </snippet>

# Update the desired parameters in the Expectation
# <snippet name="docs/docusaurus/docs/cloud/expectations/examples/edit_an_expectation_for_cloud.py - edit the expectation">
expectation.min_value = 0
expectation.max_value = 9
# </snippet>

# Save the Expectation
# <snippet name="docs/docusaurus/docs/cloud/expectations/examples/edit_an_expectation_for_cloud.py - save the expectation">
expectation.save()
# </snippet>
