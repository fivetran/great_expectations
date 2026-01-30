"""
This is an example script for creating an expectation with preset parameters.

To test, run:
pytest --docs-tests -k "doc_example_create_an_expectation" tests/integration/test_script_runner.py
"""


def set_up_context_for_example(context):
    pass


# EXAMPLE SCRIPT STARTS HERE:
# <snippet name="docs/docusaurus/docs/cloud/expectations/examples/create_an_expectation.py - full code example">
import great_expectations as gx

context = gx.get_context()
# Hide this
set_up_context_for_example(context)

# All Expectations are found in the `gx.expectations` module.
# This Expectation has all values set in advance:
# <snippet name="docs/docusaurus/docs/cloud/expectations/examples/create_an_expectation.py - preset expectation">
expectation = gx.expectations.ExpectColumnMaxToBeBetween(
    column="passenger_count", min_value=1, max_value=6, severity="warning"
)
# </snippet>

# Expectations need to be added to an Expectation Suite before being associated with a Data Asset.
# Create the Expectation Suite and add it to your Data Context
# <snippet name="docs/docusaurus/docs/cloud/expectations/examples/create_an_expectation.py - create expectation suite">
suite_name = "my_expectation_suite"
suite = gx.ExpectationSuite(name=suite_name)
context.suites.add(suite)
# </snippet>

# Optional. If you have an existing Expectation Suite you'd like to use, get it from the Data Context.
# <snippet name="docs/docusaurus/docs/cloud/expectations/examples/create_an_expectation.py - get expectation suite">
existing_suite_name = (
    "my_expectation_suite"  # replace this with the name of your Expectation Suite
)
suite = context.suites.get(name=existing_suite_name)
# </snippet>

# Add the Expectation to the Expectation Suite.
# <snippet name="docs/docusaurus/docs/cloud/expectations/examples/create_an_expectation.py - add expectation to suite">
suite.add_expectation(expectation)
suite.save()
# </snippet>

# Optional. If you modify the Expectation after you have added it to your Expectation Suite, you must explicitly save those modifications.
# <snippet name="docs/docusaurus/docs/cloud/expectations/examples/create_an_expectation.py - save the expectation">
expectation.save()
# </snippet>

# </snippet>
