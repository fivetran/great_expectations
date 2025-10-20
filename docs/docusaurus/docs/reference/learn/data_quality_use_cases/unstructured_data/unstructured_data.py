"""
This is an example script for how to validate unstructured data.

To test, run:
pytest --docs-tests -k "unstructured_data_use_case" tests/integration/test_script_runner.py
"""

# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/unstructured_data/unstructured_data.py - import the libraries">

import pandas as pd  # Data manipulation

import great_expectations as gx  # Data validation
import great_expectations.exceptions.exceptions as gxexceptions  # For exceptions
import great_expectations.expectations as gxe  # For Expectations

# </snippet>

records = []

# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/unstructured_data/unstructured_data.py - convert the data into a dataframe">
df = pd.DataFrame(records)
# </snippet>

# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/unstructured_data/unstructured_data.py - create the GX entities">
context = gx.get_context()
try:
    datasource = context.data_sources.get("PDF Scans")
except KeyError:
    datasource = context.data_sources.add_pandas("PDF Scans")

try:
    asset = datasource.get_asset("OCR Results")
except LookupError:
    asset = datasource.add_dataframe_asset("OCR Results")

try:
    batch_definition = asset.get_batch_definition("default")
except KeyError:
    batch_definition = asset.add_batch_definition_whole_dataframe("default")

# </snippet>

# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/unstructured_data/unstructured_data.py - create the expectation suite">
try:
    suite = context.suites.get(name="OCR Metrics Suite")
except gxexceptions.DataContextError:
    suite = gx.ExpectationSuite("OCR Metrics Suite")
    suite = context.suites.add(suite)
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="text_length", min_value=500)
    )  # at least 500 characters
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="ocr_confidence", min_value=70)
    )  # at least 70% confidence
    suite.add_expectation(
        gxe.ExpectColumnValuesToBeBetween(column="num_detected_headers", min_value=2)
    )  # at least 2 headers
    suite.save()
# </snippet>

# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/unstructured_data/unstructured_data.py - create the vd">
try:
    vd = context.validation_definitions.get("OCR Results VD")
except gxexceptions.DataContextError:
    vd = gx.ValidationDefinition(
        data=batch_definition, suite=suite, name="OCR Results VD"
    )
    context.validation_definitions.add(vd)
# </snippet>
# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/unstructured_data/unstructured_data.py - create and run the checkpoint">
try:
    checkpoint = context.checkpoints.get("OCR Checkpoint")
except gxexceptions.DataContextError:
    checkpoint = gx.Checkpoint(name="OCR Checkpoint", validation_definitions=[vd])
    context.checkpoints.add(checkpoint)

checkpoint.run(batch_parameters={"dataframe": df})
# </snippet>
