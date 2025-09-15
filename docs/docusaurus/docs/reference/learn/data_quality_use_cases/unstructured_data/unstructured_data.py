"""
This is an example script for how to append an Action to a Checkpoint.

To test, run:
pytest --docs-tests -k "cloud_docs_example_create_a_checkpoint" tests/integration/test_script_runner.py
"""

# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/unstructured_data/unstructured_data.py - full code example">
# Import the libraries.
# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/unstructured_data/unstructured_data.py - import the libraries">

from datasets import load_dataset  # Load PDF OCR dataset from Hugging Face
import pandas as pd  # Data manipulation
from pdf2image import convert_from_bytes  # Convert PDF pages to images
import pytesseract  # OCR engine
from pytesseract import Output  # Structured OCR output
import great_expectations as gx  # Data validation
import great_expectations.expectations as gxe  # for Expectations
# </snippet>

# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/unstructured_data/unstructured_data.py - load the dataset">
ds = load_dataset("broadfield-dev/pdf-ocr-dataset", split="train[:5]")
# </snippet>

# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/unstructured_data/unstructured_data.py - iterate through the data">
records = []
import requests  # Add at the top with other imports

for sample in ds:
    # Download PDF from URL in 'urls' field
    pdf_url = None
    urls = sample.get("urls")
    if isinstance(urls, list) and urls:
        pdf_url = urls[0]
    elif isinstance(urls, str):
        pdf_url = urls

    if not pdf_url:
        print(f"No PDF URL found in sample: {list(sample.keys())}")
        continue

    response = requests.get(pdf_url)
    if response.status_code != 200:
        print(f"Failed to download PDF from {pdf_url}")
        continue

    pdf_bytes = response.content
    print(f"Processing PDF: {sample.get('ids', 'unknown')}")
    pages = convert_from_bytes(pdf_bytes, dpi=200)
    all_ocr_text = []
    all_confidences = []
    all_heights = []
    for image in pages:
        ocr_data = pytesseract.image_to_data(image, output_type=Output.DICT)
        ocr_text = pytesseract.image_to_string(image)
        all_ocr_text.append(ocr_text)
        # Collect confidences and heights for each page
        all_confidences.extend([
            float(c) for t, c in zip(ocr_data["text"], ocr_data["conf"])
            if t.strip() and c != "-1"
        ])
        all_heights.extend([
            int(h) for t, h in zip(ocr_data["text"], ocr_data["height"])
            if t.strip()
        ])

    full_text = "\n".join(all_ocr_text)
    avg_conf = sum(all_confidences) / len(all_confidences) if all_confidences else 0
    header_count = sum(1 for h in all_heights if h > 20)

    # Store metrics for validation
    records.append({
        "file_name": sample.get("ids", "unknown"),
        "text_length": len(full_text),
        "ocr_confidence": round(avg_conf, 2),
        "num_detected_headers": header_count
    })

# </snippet>

# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/unstructured_data/unstructured_data.py - convert the data into a dataframe">
df = pd.DataFrame(records)
# </snippet>

# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/unstructured_data/unstructured_data.py - create the GX entities">
context = gx.get_context(mode="cloud")
try:
    datasource = context.data_sources.get("PDF Scans")
except:
    datasource = context.data_sources.add_pandas("PDF Scans")

try:
    asset = datasource.get_asset("OCR Results")
except:
    asset = datasource.add_dataframe_asset("OCR Results")

try:
    batch_definition = asset.get_batch_definition("default")
except:
    batch_definition = asset.add_batch_definition_whole_dataframe("default")

# </snippet>

# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/unstructured_data/unstructured_data.py - create the expectation suite">
try:
    suite = context.suites.get(name="OCR Confidence")
except:
    suite = gx.ExpectationSuite("OCR Confidence")
    suite = context.suites.add(suite)
    suite.add_expectation(gxe.ExpectColumnValuesToBeBetween(column="text_length", min_value=500))         # at least 500 characters
    suite.add_expectation(gxe.ExpectColumnValuesToBeBetween(column="ocr_confidence", min_value=70))       # at least 70% confidence
    suite.add_expectation(gxe.ExpectColumnValuesToBeBetween(column="num_detected_headers", min_value=2))  # at least 2 headers
    suite.save()
# </snippet>

# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/unstructured_data/unstructured_data.py - create the vd and run the checkpoint">
try:
    vd = context.validation_definitions.get("OCR Results VD")
except:
    vd = gx.ValidationDefinition(data=batch_definition, suite=suite, name="OCR Results VD")
    context.validation_definitions.add(vd)
try:
    checkpoint = context.checkpoints.get("OCR Checkpoint")
except:
    checkpoint = gx.Checkpoint(name="OCR Checkpoint", validation_definitions=[vd])
    context.checkpoints.add(checkpoint)

checkpoint.run(batch_parameters={"dataframe": df})
# </snippet>
# </snippet>