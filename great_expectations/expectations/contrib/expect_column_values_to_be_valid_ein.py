import pandas as pd
import numpy as np
import great_expectations as gx

# Core GX imports
from great_expectations.execution_engine import PandasExecutionEngine
from great_expectations.expectations.expectation import ColumnMapExpectation
from great_expectations.expectations.metrics import (
    ColumnMapMetricProvider,
    column_condition_partial,
)
from great_expectations.render.components import RenderedStringTemplateContent
from great_expectations.render.renderer.renderer import renderer
from great_expectations.expectations.registry import register_expectation

# --- 1. THE METRIC PROVIDER ---
class ColumnValuesValidEin(ColumnMapMetricProvider):
    condition_metric_name = "column_values.valid_ein"

    @column_condition_partial(engine=PandasExecutionEngine)
    def _pandas_condition(cls, column, **kwargs):
        return column.astype(str).str.match(r"^\d{2}-\d{7}$")

# --- 2. THE EXPECTATION ---
class ExpectColumnValuesToBeValidEin(ColumnMapExpectation):
    """Expect column values to follow the standard EIN format (XX-XXXXXXX)."""
    map_metric = "column_values.valid_ein"
    success_keys = ("mostly",)
    default_kwarg_values = {"mostly": 1}

    @classmethod
    @renderer(renderer_type="renderer.prescriptive")
    def _prescriptive_renderer(cls, configuration=None, result=None, language=None, runtime_configuration=None):
        return [
            RenderedStringTemplateContent(
                **{
                    "content": "values must be valid EINs (format: XX-XXXXXXX).",
                    "styling": {"classes": ["badge", "badge-info"]},
                }
            )
        ]

# --- 3. REGISTRATION ---
# This is critical: it attaches your logic to the Validator class
register_expectation(ExpectColumnValuesToBeValidEin)

# --- 4. THE TEST SUITE ---
if __name__ == "__main__":
    # 1. Setup Sample Data
    data = {"ein_col": ["12-3456789", "00-0000000", "invalid-ein", "123456789"]}
    df = pd.DataFrame(data)

    # 2. Initialize Context
    context = gx.get_context()

    # 3. Create Datasource
    datasource = context.data_sources.add_pandas(name="my_pandas_datasource")
    
    # 4. Get the Batch
    # read_dataframe returns a Batch object in GX 1.x
    batch = datasource.read_dataframe(df, asset_name="my_ein_data")

    # 5. THE CRITICAL FIX: Wrap the Batch in a Validator
    # The Validator is the object that actually has the 'expect_...' methods
    validator = context.get_validator(batch=batch)

    # 6. Run Validation
    print("Running EIN Validation (Final Fix)...")
    result = validator.expect_column_values_to_be_valid_ein(
        column="ein_col", 
        mostly=0.5
    )

    # 7. Output Results
    print("-" * 30)
    print(f"Success: {result.success}")
    print(f"Unexpected values: {result.result.get('unexpected_list')}")
    print("-" * 30)
    
    if result.success:
        print("✅ FINAL VICTORY: Valid EINs passed, invalid ones caught.")
    else:
        print("❌ Logic Failure: Check your regex or threshold.")