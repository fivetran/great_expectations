# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/unstructured_data/unstructured_data_process_files.py - load the dataset">
from datasets import load_dataset  # Load PDF OCR dataset from Hugging Face

ds = load_dataset("broadfield-dev/pdf-ocr-dataset", split="train[:5]")
# </snippet>

# <snippet name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/unstructured_data/unstructured_data_process_files.py - iterate through the data">
import pytesseract  # OCR engine
import requests
from pdf2image import convert_from_bytes  # Convert PDF pages to images
from pytesseract import Output  # Structured OCR output

records = []

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
        # Run OCR on the PDFs
        ocr_data = pytesseract.image_to_data(image, output_type=Output.DICT)
        ocr_text = pytesseract.image_to_string(image)
        all_ocr_text.append(ocr_text)
        # Collect confidences and heights for each page
        all_confidences.extend(
            [
                float(c)
                for t, c in zip(ocr_data["text"], ocr_data["conf"])
                if t.strip() and c != "-1"
            ]
        )
        all_heights.extend(
            [int(h) for t, h in zip(ocr_data["text"], ocr_data["height"]) if t.strip()]
        )

    full_text = "\n".join(all_ocr_text)
    avg_conf = sum(all_confidences) / len(all_confidences) if all_confidences else 0
    header_count = sum(1 for h in all_heights if h > 20)

    # Store metrics for validation
    records.append(
        {
            "file_name": sample.get("ids", "unknown"),
            "text_length": len(full_text),
            "ocr_confidence": round(avg_conf, 2),
            "num_detected_headers": header_count,
        }
    )
# </snippet>
