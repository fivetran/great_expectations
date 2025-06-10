from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Type

from great_expectations.compatibility import pydantic
from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.types import (
    Comparable,  # noqa: TC001 # pydantic instantiates this type at runtime
)
from great_expectations.expectations.expectation import (
    COLUMN_DESCRIPTION,
    ColumnAggregateExpectation,
    render_suite_parameter_string,
)
from great_expectations.expectations.metadata_types import DataQualityIssues, SupportedDataSources
from great_expectations.render import LegacyRendererType
from great_expectations.render.renderer.renderer import renderer

if TYPE_CHECKING:
    from great_expectations.core import (
        ExpectationValidationResult,
    )
    from great_expectations.execution_engine import ExecutionEngine
    from great_expectations.expectations.expectation_configuration import (
        ExpectationConfiguration,
    )
    from great_expectations.render import RenderedStringTemplateContent
    from great_expectations.render.renderer_configuration import RendererConfiguration

EXPECTATION_SHORT_DESCRIPTION = (
    "Expect the proportion of non-null values to be between a minimum value and a maximum value."
)
MIN_VALUE_DESCRIPTION = (
    "The minimum proportion of non-null values (proportions are on the range 0 to 1)."
)
MAX_VALUE_DESCRIPTION = (
    "The maximum proportion of non-null values (proportions are on the range 0 to 1)."
)
STRICT_MIN_DESCRIPTION = (
    "If True, the minimum proportion of non-null values must be strictly larger than min_value."
)
STRICT_MAX_DESCRIPTION = (
    "If True, the maximum proportion of non-null values must be strictly smaller than max_value."
)
DATA_QUALITY_ISSUES = [DataQualityIssues.COMPLETENESS.value]
SUPPORTED_DATA_SOURCES = [
    SupportedDataSources.PANDAS.value,
    SupportedDataSources.SPARK.value,
    SupportedDataSources.SQLITE.value,
    SupportedDataSources.POSTGRESQL.value,
    SupportedDataSources.MYSQL.value,
    SupportedDataSources.MSSQL.value,
    SupportedDataSources.BIGQUERY.value,
    SupportedDataSources.SNOWFLAKE.value,
    SupportedDataSources.DATABRICKS.value,
    SupportedDataSources.REDSHIFT.value,
]


class ExpectColumnProportionOfNonNullValuesToBeBetween(ColumnAggregateExpectation):
    __doc__ = f"""{EXPECTATION_SHORT_DESCRIPTION}

    For example, in a column containing [1, 2, None, 3, None, None, 4, 4, 4, 4], there are \
    7 non-null values and 10 total values for a proportion of 0.7.

    ExpectColumnProportionOfNonNullValuesToBeBetween is a \
    Column Aggregate Expectation.

    Column Aggregate Expectations are one of the most common types of Expectation.
    They are evaluated for a single column, and produce an aggregate Metric, such as a \
    mean, standard deviation, number of unique values, column type, etc.
    If that Metric meets the conditions you set, the Expectation considers that data valid.

    Args:
        column (str): \
            {COLUMN_DESCRIPTION}
        min_value (float or None): \
           {MIN_VALUE_DESCRIPTION}
        max_value (float or None): \
            {MAX_VALUE_DESCRIPTION}
        strict_min (boolean): \
            {STRICT_MIN_DESCRIPTION} default=False
        strict_max (boolean): \
            {STRICT_MAX_DESCRIPTION} default=False

    Other Parameters:
        result_format (str or None): \
            Which output mode to use: BOOLEAN_ONLY, BASIC, COMPLETE, or SUMMARY. \
            For more detail, see [result_format](https://docs.greatexpectations.io/docs/reference/expectations/result_format).
        catch_exceptions (boolean or None): \
            If True, then catch exceptions and include them as part of the result object. \
            For more detail, see [catch_exceptions](https://docs.greatexpectations.io/docs/reference/expectations/standard_arguments/#catch_exceptions).
        meta (dict or None): \
            A JSON-serializable dictionary (nesting allowed) that will be included in the \
            output without modification. For more detail, see [meta](https://docs.greatexpectations.io/docs/reference/expectations/standard_arguments/#meta).

    Returns:
        An [ExpectationSuiteValidationResult](https://docs.greatexpectations.io/docs/terms/validation_result)

        Exact fields vary depending on the values passed to \
        result_format, catch_exceptions, and meta.

    Notes:
        * min_value and max_value are both inclusive unless \
          strict_min or strict_max are set to True.
        * If min_value is None, then max_value is treated as an upper bound
        * If max_value is None, then min_value is treated as a lower bound
        * observed_value field in the result object is customized for this expectation to be \
          a float representing the proportion of non-null values in the column

    See Also:
        [ExpectColumnProportionOfUniqueValuesToBeBetween](https://greatexpectations.io/expectations/expect_column_proportion_of_unique_values_to_be_between)

    Supported Data Sources:
        [{SUPPORTED_DATA_SOURCES[0]}](https://docs.greatexpectations.io/docs/application_integration_support/)
        [{SUPPORTED_DATA_SOURCES[1]}](https://docs.greatexpectations.io/docs/application_integration_support/)
        [{SUPPORTED_DATA_SOURCES[2]}](https://docs.greatexpectations.io/docs/application_integration_support/)
        [{SUPPORTED_DATA_SOURCES[3]}](https://docs.greatexpectations.io/docs/application_integration_support/)
        [{SUPPORTED_DATA_SOURCES[4]}](https://docs.greatexpectations.io/docs/application_integration_support/)
        [{SUPPORTED_DATA_SOURCES[5]}](https://docs.greatexpectations.io/docs/application_integration_support/)
        [{SUPPORTED_DATA_SOURCES[6]}](https://docs.greatexpectations.io/docs/application_integration_support/)
        [{SUPPORTED_DATA_SOURCES[7]}](https://docs.greatexpectations.io/docs/application_integration_support/)
        [{SUPPORTED_DATA_SOURCES[8]}](https://docs.greatexpectations.io/docs/application_integration_support/)

    Data Quality Issues:
        {DATA_QUALITY_ISSUES[0]}

    Example Data:
                test 	test2
            0 	"aaa"   1
            1 	"abb"   None
            2 	"acc"   1
            3   None    3

    Code Examples:
        Passing Case:
            Input:
                ExpectColumnProportionOfNonNullValuesToBeBetween(
                    column="test",
                    min_value=0,
                    max_value=0.8
                )

            Output:
                {{
                  "exception_info": {{
                    "raised_exception": false,
                    "exception_traceback": null,
                    "exception_message": null
                  }},
                  "result": {{
                    "observed_value": 0.75
                  }},
                  "meta": {{}},
                  "success": true
                }}

        Failing Case:
            Input:
                ExpectColumnProportionOfNonNullValuesToBeBetween(
                    column="test2",
                    min_value=0.3,
                    max_value=0.5,
                    strict_min=False,
                    strict_max=True
                )

            Output:
                {{
                  "exception_info": {{
                    "raised_exception": false,
                    "exception_traceback": null,
                    "exception_message": null
                  }},
                  "result": {{
                    "observed_value": 0.75
                  }},
                  "meta": {{}},
                  "success": false
                }}
    """

    min_value: Optional[Comparable] = pydantic.Field(
        default=None, description=MIN_VALUE_DESCRIPTION
    )
    max_value: Optional[Comparable] = pydantic.Field(
        default=None, description=MAX_VALUE_DESCRIPTION
    )
    strict_min: bool = pydantic.Field(default=False, description=STRICT_MIN_DESCRIPTION)
    strict_max: bool = pydantic.Field(default=False, description=STRICT_MAX_DESCRIPTION)

    library_metadata = {
        "maturity": "production",
        "tags": ["core expectation", "column aggregate expectation"],
        "contributors": ["@great_expectations"],
        "requirements": [],
        "has_full_test_suite": True,
        "manually_reviewed_code": True,
    }

    _library_metadata = library_metadata

    metric_dependencies = ("column.nonnull_proportion",)
    success_keys = (
        "min_value",
        "max_value",
        "strict_min",
        "strict_max",
    )

    args_keys = (
        "column",
        "min_value",
        "max_value",
        "strict_min",
        "strict_max",
    )

    class Config:
        title = "Expect column proportion of non-null values to be between"

        @staticmethod
        def schema_extra(
            schema: Dict[str, Any], model: Type[ExpectColumnProportionOfNonNullValuesToBeBetween]
        ) -> None:
            ColumnAggregateExpectation.Config.schema_extra(schema, model)
            schema["properties"]["metadata"]["properties"].update(
                {
                    "data_quality_issues": {
                        "title": "Data Quality Issues",
                        "type": "array",
                        "const": DATA_QUALITY_ISSUES,
                    },
                    "library_metadata": {
                        "title": "Library Metadata",
                        "type": "object",
                        "const": model._library_metadata,
                    },
                    "short_description": {
                        "title": "Short Description",
                        "type": "string",
                        "const": EXPECTATION_SHORT_DESCRIPTION,
                    },
                    "supported_data_sources": {
                        "title": "Supported Data Sources",
                        "type": "array",
                        "const": SUPPORTED_DATA_SOURCES,
                    },
                }
            )

    @classmethod
    @override
    def _prescriptive_template(  # type: ignore[empty-body]  # TODO: remove this with impementation
        cls,
        renderer_configuration: RendererConfiguration,
    ) -> RendererConfiguration: ...

    @classmethod
    @override
    @renderer(renderer_type=LegacyRendererType.PRESCRIPTIVE)
    @render_suite_parameter_string
    def _prescriptive_renderer(  # type: ignore[empty-body]  # TODO: remove this with impementation
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
        **kwargs,
    ) -> list[RenderedStringTemplateContent]: ...

    @override
    def _validate(
        self,
        metrics: dict,
        runtime_configuration: Optional[dict] = None,
        execution_engine: Optional[ExecutionEngine] = None,
    ):
        return self._validate_metric_value_between(
            metric_name="column.nonnull_proportion",
            metrics=metrics,
            runtime_configuration=runtime_configuration,
            execution_engine=execution_engine,
        )
