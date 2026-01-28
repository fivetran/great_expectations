from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Optional, Type, Union

import altair as alt
import pandas as pd

from great_expectations.compatibility import pydantic
from great_expectations.compatibility.typing_extensions import override
from great_expectations.expectations.expectation import (
    ColumnAggregateExpectation,
    _style_row_condition,
    render_suite_parameter_string,
)
from great_expectations.expectations.metadata_types import DataQualityIssues, SupportedDataSources
from great_expectations.expectations.model_field_descriptions import (
    COLUMN_DESCRIPTION,
    FAILURE_SEVERITY_DESCRIPTION,
    VALUE_SET_DESCRIPTION,
)
from great_expectations.expectations.model_field_types import (
    ValueSetField,  # noqa: TC001  # type needed in pydantic validation
)
from great_expectations.expectations.registry import get_metric_kwargs
from great_expectations.render import (
    AtomicDiagnosticRendererType,
    LegacyDescriptiveRendererType,
    LegacyRendererType,
    RenderedAtomicContent,
    RenderedGraphContent,
    RenderedStringTemplateContent,
    renderedAtomicValueSchema,
)
from great_expectations.render.renderer.renderer import renderer
from great_expectations.render.renderer_configuration import (
    RendererConfiguration,
    RendererValueType,
)
from great_expectations.render.util import (
    parse_row_condition_string,
    substitute_none_for_missing,
)
from great_expectations.validator.metric_configuration import MetricConfiguration

if TYPE_CHECKING:
    from great_expectations.core import (
        ExpectationValidationResult,
    )
    from great_expectations.execution_engine import ExecutionEngine
    from great_expectations.expectations.expectation_configuration import (
        ExpectationConfiguration,
    )
    from great_expectations.render.renderer_configuration import AddParamArgs
    from great_expectations.validator.validator import ValidationDependencies

EXPECTATION_SHORT_DESCRIPTION = (
    "Expect the set of distinct column values to be contained by a given set."
)
SUPPORTED_DATA_SOURCES = [
    SupportedDataSources.PANDAS.value,
    SupportedDataSources.SPARK.value,
    SupportedDataSources.SQLITE.value,
    SupportedDataSources.POSTGRESQL.value,
    SupportedDataSources.AURORA.value,
    SupportedDataSources.CITUS.value,
    SupportedDataSources.ALLOY.value,
    SupportedDataSources.NEON.value,
    SupportedDataSources.MYSQL.value,
    SupportedDataSources.MSSQL.value,
    SupportedDataSources.BIGQUERY.value,
    SupportedDataSources.SNOWFLAKE.value,
    SupportedDataSources.DATABRICKS.value,
    SupportedDataSources.REDSHIFT.value,
]
DATA_QUALITY_ISSUES = [DataQualityIssues.UNIQUENESS.value]


class ExpectColumnDistinctValuesToBeInSet(ColumnAggregateExpectation):
    __doc__ = f"""{EXPECTATION_SHORT_DESCRIPTION}

    ExpectColumnDistinctValuesToBeInSet is a \
    Column Aggregate Expectation.

    Column Aggregate Expectations are one of the most common types of Expectation.
    They are evaluated for a single column, and produce an aggregate Metric, such as a mean, standard deviation, number of unique values, column type, etc.
    If that Metric meets the conditions you set, the Expectation considers that data valid.

    Args:
        column (str): \
            {COLUMN_DESCRIPTION}
        value_set (set-like): \
            {VALUE_SET_DESCRIPTION}

    Other Parameters:
        result_format (str or None): \
            Which output mode to use: BOOLEAN_ONLY, BASIC, COMPLETE, or SUMMARY. \
            For more detail, see [result_format](https://docs.greatexpectations.io/docs/reference/expectations/result_format).
        catch_exceptions (boolean or None): \
            If True, then catch exceptions and include them as part of the result object. \
            For more detail, see [catch_exceptions](https://docs.greatexpectations.io/docs/reference/expectations/standard_arguments/#catch_exceptions).
        meta (dict or None): \
            A JSON-serializable dictionary (nesting allowed) that will be included in the output without \
            modification. For more detail, see [meta](https://docs.greatexpectations.io/docs/reference/expectations/standard_arguments/#meta).
        severity (str or None): \
            {FAILURE_SEVERITY_DESCRIPTION} \
            For more detail, see [failure severity](https://docs.greatexpectations.io/docs/cloud/expectations/expectations_overview/#failure-severity).

    Returns:
        An [ExpectationSuiteValidationResult](https://docs.greatexpectations.io/docs/terms/validation_result)

        Exact fields vary depending on the values passed to result_format, catch_exceptions, and meta.

    Notes:
        The success value for this expectation will match that of \
    [ExpectColumnValuesToBeInSet](https://greatexpectations.io/expectations/expect_column_values_to_be_in_set).

    See Also:
        [ExpectColumnDistinctValuesToContainSet](https://greatexpectations.io/expectations/expect_column_distinct_values_to_contain_set)
        [ExpectColumnDistinctValuesToEqualSet](https://greatexpectations.io/expectations/expect_column_distinct_values_to_equal_set)

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
        [{SUPPORTED_DATA_SOURCES[9]}](https://docs.greatexpectations.io/docs/application_integration_support/)
        [{SUPPORTED_DATA_SOURCES[10]}](https://docs.greatexpectations.io/docs/application_integration_support/)
        [{SUPPORTED_DATA_SOURCES[11]}](https://docs.greatexpectations.io/docs/application_integration_support/)
        [{SUPPORTED_DATA_SOURCES[12]}](https://docs.greatexpectations.io/docs/application_integration_support/)
        [{SUPPORTED_DATA_SOURCES[13]}](https://docs.greatexpectations.io/docs/application_integration_support/)

    Data Quality Issues:
        {DATA_QUALITY_ISSUES[0]}

    Example Data:
                test 	test2
            0 	1       1
            1 	2       1
            2 	4       1

    Code Examples:
        Passing Case:
            Input:
                ExpectColumnDistinctValuesToBeInSet(
                    column="test",
                    value_set=[1, 2, 3, 4, 5]
            )

            Output:
                {{
                  "exception_info": {{
                    "raised_exception": false,
                    "exception_traceback": null,
                    "exception_message": null
                  }},
                  "result": {{
                    "observed_value": [
                      1,
                      2,
                      4
                    ],
                    "details": {{
                      "value_counts": [
                        {{
                          "value": 1,
                          "count": 1
                        }},
                        {{
                          "value": 2,
                          "count": 1
                        }},
                        {{
                          "value": 4,
                          "count": 1
                        }}
                      ]
                    }}
                  }},
                  "meta": {{}},
                  "success": true
                }}

        Failing Case:
            Input:
                ExpectColumnDistinctValuesToBeInSet(
                    column="test2",
                    value_set=[3, 2, 4]
            )

            Output:
                {{
                  "exception_info": {{
                    "raised_exception": false,
                    "exception_traceback": null,
                    "exception_message": null
                  }},
                  "result": {{
                    "observed_value": [
                      1
                    ],
                    "details": {{
                      "value_counts": [
                        {{
                          "value": 1,
                          "count": 3
                        }}
                      ]
                    }}
                  }},
                  "meta": {{}},
                  "success": false
                }}
    """  # noqa: E501 # FIXME CoP

    value_set: ValueSetField

    library_metadata: ClassVar[Dict[str, Union[str, list, bool]]] = {
        "maturity": "production",
        "tags": ["core expectation", "column aggregate expectation"],
        "contributors": ["@great_expectations"],
        "requirements": [],
        "has_full_test_suite": True,
        "manually_reviewed_code": True,
    }
    _library_metadata = library_metadata

    # Setting necessary computation metric dependencies and defining kwargs, as well as assigning kwargs default values\  # noqa: E501 # FIXME CoP
    metric_dependencies = (
        "column.distinct_values.not_in_set.count",
        "column.distinct_values.not_in_set",
    )
    success_keys = ("value_set",)

    args_keys = (
        "column",
        "value_set",
    )

    class Config:
        title = "Expect column distinct values to be in set"

        @staticmethod
        def schema_extra(
            schema: Dict[str, Any], model: Type[ExpectColumnDistinctValuesToBeInSet]
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

    @pydantic.validator("value_set")
    def _validate_value_set(cls, value_set: ValueSetField) -> ValueSetField:
        if not value_set:
            raise ValueError("value_set must be a non-empty set-like object.")  # noqa: TRY003 # Error messaged gets swallowed by Pydantic
        return value_set

    @override
    def get_validation_dependencies(
        self,
        execution_engine: Optional[ExecutionEngine] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> ValidationDependencies:
        """Override to configure metrics with value_set and limit parameters."""

        validation_dependencies: ValidationDependencies = super().get_validation_dependencies(
            execution_engine=execution_engine,
            runtime_configuration=runtime_configuration,
        )

        # Get limit from result_format
        result_format = self._get_result_format(runtime_configuration)
        if isinstance(result_format, dict):
            limit = result_format.get("partial_unexpected_count", 20)
        else:
            limit = 20

        # Get value_set from expectation kwargs
        value_set = self._get_success_kwargs().get("value_set", [])

        # Configure metrics with value_set and limit
        for metric_name in self.metric_dependencies:
            metric_kwargs = get_metric_kwargs(
                metric_name=metric_name,
                configuration=self.configuration,
                runtime_configuration=runtime_configuration,
            )
            metric_value_kwargs = (
                dict(metric_kwargs["metric_value_kwargs"])
                if metric_kwargs["metric_value_kwargs"]
                else {}
            )
            metric_value_kwargs["value_set"] = value_set
            if metric_name == "column.distinct_values.not_in_set":
                metric_value_kwargs["limit"] = limit

            validation_dependencies.set_metric_configuration(
                metric_name=metric_name,
                metric_configuration=MetricConfiguration(
                    metric_name=metric_name,
                    metric_domain_kwargs=metric_kwargs["metric_domain_kwargs"],
                    metric_value_kwargs=metric_value_kwargs,
                ),
            )

        return validation_dependencies

    @classmethod
    def _prescriptive_template(
        cls,
        renderer_configuration: RendererConfiguration,
    ) -> RendererConfiguration:
        add_param_args: AddParamArgs = (
            ("column", RendererValueType.STRING),
            ("value_set", RendererValueType.ARRAY),
        )
        for name, param_type in add_param_args:
            renderer_configuration.add_param(name=name, param_type=param_type)

        params = renderer_configuration.params

        if not params.value_set or len(params.value_set.value) == 0:
            if renderer_configuration.include_column_name:
                template_str = "$column distinct values must belong to this set: [ ]"
            else:
                template_str = (
                    "distinct values must belong to a set, but that set is not specified."
                )
        else:
            array_param_name = "value_set"
            param_prefix = "v__"
            renderer_configuration = cls._add_array_params(
                array_param_name=array_param_name,
                param_prefix=param_prefix,
                renderer_configuration=renderer_configuration,
            )
            value_set_str: str = cls._get_array_string(
                array_param_name=array_param_name,
                param_prefix=param_prefix,
                renderer_configuration=renderer_configuration,
            )

            if renderer_configuration.include_column_name:
                template_str = f"$column distinct values must belong to this set: {value_set_str}."
            else:
                template_str = f"distinct values must belong to this set: {value_set_str}."

        renderer_configuration.template_str = template_str

        return renderer_configuration

    @classmethod
    @renderer(renderer_type=LegacyRendererType.PRESCRIPTIVE)
    @render_suite_parameter_string
    def _prescriptive_renderer(
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> List[RenderedStringTemplateContent]:
        renderer_configuration: RendererConfiguration = RendererConfiguration(
            configuration=configuration,
            result=result,
            runtime_configuration=runtime_configuration,
        )
        params = substitute_none_for_missing(
            renderer_configuration.kwargs,
            ["column", "value_set", "row_condition", "condition_parser"],
        )

        if params["value_set"] is None or len(params["value_set"]) == 0:
            if renderer_configuration.include_column_name:
                template_str = "$column distinct values must belong to this set: [ ]"
            else:
                template_str = (
                    "distinct values must belong to a set, but that set is not specified."
                )

        else:
            for i, v in enumerate(params["value_set"]):
                params[f"v__{i!s}"] = v
            values_string = " ".join([f"$v__{i!s}" for i, v in enumerate(params["value_set"])])

            if renderer_configuration.include_column_name:
                template_str = f"$column distinct values must belong to this set: {values_string}."
            else:
                template_str = f"distinct values must belong to this set: {values_string}."

        styling = runtime_configuration.get("styling", {}) if runtime_configuration else {}

        if params["row_condition"] is not None:
            conditional_template_str = parse_row_condition_string(params["row_condition"])

            template_str, styling = _style_row_condition(
                conditional_template_str,
                template_str,
                params,
                styling,
            )

        return [
            RenderedStringTemplateContent(
                **{
                    "content_block_type": "string_template",
                    "string_template": {
                        "template": template_str,
                        "params": params,
                        "styling": styling,
                    },
                }
            )
        ]

    @classmethod
    @renderer(renderer_type=LegacyDescriptiveRendererType.VALUE_COUNTS_BAR_CHART)
    def _descriptive_value_counts_bar_chart_renderer(
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> Optional[RenderedGraphContent]:
        assert result, "Must pass in result."
        value_count_dicts = result.result["details"]["value_counts"]
        if isinstance(value_count_dicts, pd.Series):
            values = value_count_dicts.index.tolist()
            counts = value_count_dicts.tolist()
        else:
            values = [value_count_dict["value"] for value_count_dict in value_count_dicts]
            counts = [value_count_dict["count"] for value_count_dict in value_count_dicts]

        df = pd.DataFrame(
            {
                "value": values,
                "count": counts,
            }
        )

        if len(values) > 60:  # noqa: PLR2004 # FIXME CoP
            return None
        else:
            chart_pixel_width = (len(values) / 60.0) * 500
            chart_pixel_width = max(chart_pixel_width, 250)
            chart_container_col_width = round((len(values) / 60.0) * 6)
            if chart_container_col_width < 4:  # noqa: PLR2004 # FIXME CoP
                chart_container_col_width = 4
            elif chart_container_col_width >= 5:  # noqa: PLR2004 # FIXME CoP
                chart_container_col_width = 6
            elif chart_container_col_width >= 4:  # noqa: PLR2004 # FIXME CoP
                chart_container_col_width = 5

        mark_bar_args = {}
        if len(values) == 1:
            mark_bar_args["size"] = 20

        bars = (
            alt.Chart(df)
            .mark_bar(**mark_bar_args)
            .encode(y="count:Q", x="value:O", tooltip=["value", "count"])
            .properties(height=400, width=chart_pixel_width, autosize="fit")
        )

        chart = bars.to_json()

        new_block = RenderedGraphContent(
            **{
                "content_block_type": "graph",
                "header": RenderedStringTemplateContent(
                    **{
                        "content_block_type": "string_template",
                        "string_template": {
                            "template": "Value Counts",
                            "tooltip": {"content": "expect_column_distinct_values_to_be_in_set"},
                            "tag": "h6",
                        },
                    }
                ),
                "graph": chart,
                "styling": {
                    "classes": [f"col-{chart_container_col_width!s}", "mt-1"],
                },
            }
        )

        return new_block

    def _validate(
        self,
        metrics: Dict,
        runtime_configuration: Optional[dict] = None,
        execution_engine: Optional[ExecutionEngine] = None,
    ):
        # Get violation count from the optimized metric (pushed to database)
        violation_count = metrics.get("column.distinct_values.not_in_set.count", 0)
        success = violation_count == 0

        # Get result_format settings
        result_format = self._get_result_format(runtime_configuration)
        partial_unexpected_count: int = 20
        if isinstance(result_format, dict):
            result_format_str = result_format.get("result_format", "SUMMARY")
            puc = result_format.get("partial_unexpected_count", 20)
            if isinstance(puc, int):
                partial_unexpected_count = puc
        else:
            result_format_str = result_format or "SUMMARY"

        # Build result
        result: Dict[str, Any] = {
            "success": success,
        }

        if result_format_str == "BOOLEAN_ONLY":
            result["result"] = {}
        else:
            # Get violations (values in column but not in value_set)
            # This is already limited by the metric's limit parameter
            violations = metrics.get("column.distinct_values.not_in_set", [])

            # observed_value is None - violations go in partial_unexpected_list
            result["result"] = {
                "observed_value": None,
                "unexpected_count": violation_count,
            }

            # Add partial_unexpected_list (limited sample of violations)
            if violations and partial_unexpected_count > 0:
                result["result"]["partial_unexpected_list"] = violations[:partial_unexpected_count]

        return result

    @classmethod
    @renderer(renderer_type=AtomicDiagnosticRendererType.OBSERVED_VALUE)
    def _atomic_diagnostic_observed_value(
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> RenderedAtomicContent:
        """Render observed value - returns None since violations are in partial_unexpected_list."""
        renderer_configuration = RendererConfiguration(
            configuration=configuration,
            result=result,
            runtime_configuration=runtime_configuration,
        )

        # observed_value is None for this expectation - violations are in partial_unexpected_list
        # Return a simple "N/A" or empty rendering
        renderer_configuration.template_str = "--"

        value_obj = renderedAtomicValueSchema.load(
            {
                "template": renderer_configuration.template_str,
                "params": renderer_configuration.params.dict(),
                "meta_notes": renderer_configuration.meta_notes,
                "schema": {"type": "com.superconductive.rendered.string"},
            }
        )
        return RenderedAtomicContent(
            name=AtomicDiagnosticRendererType.OBSERVED_VALUE,
            value=value_obj,
            value_type="StringValueType",
        )
