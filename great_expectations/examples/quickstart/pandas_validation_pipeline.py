"""
CI-Friendly Pandas Validation Pipeline (Great Expectations)
----------------------------------------------------------
Demonstrates:
- dataframe validation using Great Expectations
- expectation suite creation
- artifact output for CI usage
- non-zero exit on failure

Run:
    python examples/quickstart/pandas_validation_pipeline.py
"""

import json
import os
import pathlib
import sys
from datetime import datetime

import pandas as pd

import great_expectations as gx


def main():
    # Sample dataset (replace with real CSV/Parquet in production)
    df = pd.DataFrame(
        {
            "user_id": [101, 102, 103, 104, 105],
            "age": [21, 25, 18, 40, 32],
            "country": ["IN", "IN", "US", "IN", "UK"],
            "spend": [120.5, 300.0, 0.0, 99.99, 250.0],
        }
    )

    context = gx.get_context()

    # Create datasource
    datasource_name = "pandas_ci_ds"
    datasource = context.sources.add_pandas(datasource_name)

    asset_name = "demo_asset"
    asset = datasource.add_dataframe_asset(name=asset_name)
    batch_request = asset.build_batch_request(dataframe=df)

    # Suite
    suite_name = "pandas_ci_suite"
    suite = context.add_or_update_expectation_suite(expectation_suite_name=suite_name)

    validator = context.get_validator(batch_request=batch_request, expectation_suite=suite)

    # Expectations
    validator.expect_table_row_count_to_be_between(min_value=1, max_value=1_000_000)
    validator.expect_column_values_to_not_be_null("user_id")
    validator.expect_column_values_to_be_unique("user_id")
    validator.expect_column_values_to_be_between("age", min_value=0, max_value=120)
    validator.expect_column_values_to_be_in_set("country", ["IN", "US", "UK"])
    validator.expect_column_values_to_be_between("spend", min_value=0.0, max_value=10_000.0)

    validator.save_expectation_suite(discard_failed_expectations=False)

    # Validate
    result = validator.validate()

    # Write artifact
    out_dir = os.path.join("outputs", "ge_validation")
    pathlib.Path(out_dir).mkdir(exist_ok=True, parents=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(out_dir, f"validation_result_{timestamp}.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result.to_json_dict(), f, indent=2)

    print(f"\n✅ Validation done. Artifact: {out_path}")
    print(f"Success: {result.success}")

    # CI behavior
    if not result.success:
        print("❌ Validation failed. Exiting with non-zero code for CI.")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
