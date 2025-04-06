import re

from great_expectations.execution_engine import PandasExecutionEngine
from great_expectations.expectations.expectation import ColumnMapExpectation
from great_expectations.expectations.metrics import (
    ColumnMapMetricProvider,
    column_condition_partial,
)

SHA256_REGEX = r"^([a-fA-F\d]{64})$"


# This class defines a Metric to support your Expectation.
# For most ColumnMapExpectations, the main business logic for calculation will live in this class.
class ColumnValuesToBeValidSha256(ColumnMapMetricProvider):
    # This is the id string that will be used to reference your metric.
    condition_metric_name = "column_values.valid_sha256"

    # This method implements the core logic for the PandasExecutionEngine
    @column_condition_partial(engine=PandasExecutionEngine)
    def _pandas(cls, column, **kwargs):
        def matches_sha256_regex(x):
            return bool(re.match(SHA256_REGEX, str(x)))

        return column.apply(lambda x: matches_sha256_regex(x) if x else False)

    # This method defines the business logic for evaluating your metric when using a SqlAlchemyExecutionEngine
    # @column_condition_partial(engine=SqlAlchemyExecutionEngine)
    # def _sqlalchemy(cls, column, _dialect, **kwargs):
    #     raise NotImplementedError

    # This method defines the business logic for evaluating your metric when using a SparkDFExecutionEngine
    # @column_condition_partial(engine=SparkDFExecutionEngine)
    # def _spark(cls, column, **kwargs):
    #     raise NotImplementedError


# This class defines the Expectation itself
class ExpectColumnValuesToBeValidSha256(ColumnMapExpectation):
    """Expect column values to be valid SHA256 hashes."""

    # These examples will be shown in the public gallery.
    # They will also be executed as unit tests for your Expectation.
    examples = [
        {
            "data": {
                "well_formed_sha256": [
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "e93ac4c39c921632d9a237cd86452a3ba417e7e27b68fb6f0acef66f0e18f2ab",  # sha256 hash of "great_expectations" UTF-8
                    "E93AC4C39C921632D9A237CD86452A3BA417E7E27B68FB6F0ACEF66F0E18F2AB",
                    "e93ac4c39C921632d9a237cD86452a3Ba417e7e27B68fb6f0acef66f0e18F2aB",
                    "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
                ],
                "malformed_sha256": [
                    "",
                    "ab12",
                    "e93ac4c39c921632d9a237cd86452a3ba417e7e27b68fb6f0acef66f0e18f2abffff",
                    "e93ac4c39c921632d9a237cd86452a3ba417e7e27b68fb6f0acef66f0e18f2abxxxx",
                    "This is not valid sha256",
                ],
            },
            "tests": [
                {
                    "title": "basic_positive_test",
                    "exact_match_out": False,
                    "include_in_gallery": True,
                    "in": {"column": "well_formed_sha256"},
                    "out": {"success": True},
                },
                {
                    "title": "basic_negative_test",
                    "exact_match_out": False,
                    "include_in_gallery": True,
                    "in": {"column": "malformed_sha256"},
                    "out": {"success": False},
                },
            ],
        }
    ]

    # This is the id string of the Metric used by this Expectation.
    # For most Expectations, it will be the same as the `condition_metric_name` defined in your Metric class above.
    map_metric = "column_values.valid_sha256"

    # This is a list of parameter names that can affect whether the Expectation evaluates to True or False
    success_keys = ("mostly",)

    # This dictionary contains default values for any parameters that should have default values
    default_kwarg_values = {}

    # This object contains metadata for display in the public Gallery
    library_metadata = {
        "maturity": "experimental",
        "tags": ["experimental", "hackathon", "typed-entities"],
        "contributors": [
            "@voidforall",
        ],
    }


if __name__ == "__main__":
    ExpectColumnValuesToBeValidSha256().print_diagnostic_checklist()
