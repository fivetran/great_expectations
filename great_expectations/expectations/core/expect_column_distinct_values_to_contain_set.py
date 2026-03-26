from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Optional, Type, Union

from great_expectations.compatibility.typing_extensions import override
from great_expectations.constants import MAX_DISTINCT_VALUES
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
from great_expectations.render import (
    AtomicDiagnosticRendererType,
    LegacyRendererType,
    RenderedAtomicContent,
    RenderedStringTemplateContent,
    renderedAtomicValueSchema,
)
from great_expectations.render.renderer.observed_value_renderer import ObservedValueRenderState
from great_expectations.render.renderer.renderer import renderer
from great_expectations.render.renderer_configuration import (
    RendererConfiguration,
    RendererValueType,
)
from great_expectations.render.util import (
    parse_row_condition_string,
    substitute_none_for_missing,
)

if TYPE_CHECKING:
    from great_expectations.core import (
        ExpectationValidationResult,
    )
    from great_expectations.execution_engine import ExecutionEngine
    from great_expectations.expectations.expectation_configuration import (
        ExpectationConfiguration,
    )
    from great_expectations.render.renderer_configuration import AddParamArgs

EXPECTATION_SHORT_DESCRIPTION = "Expect the set of distinct column values to contain a given set."
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
    SupportedDataSources.SQL_SERVER.value,
    SupportedDataSources.BIGQUERY.value,
    SupportedDataSources.SNOWFLAKE.value,
    SupportedDataSources.DATABRICKS.value,
    SupportedDataSources.REDSHIFT.value,
]
DATA_QUALITY_ISSUES = [DataQualityIssues.UNIQUENESS.value]


class ExpectColumnDistinctValuesToContainSet(ColumnAggregateExpectation):
    __doc__ = f"""{EXPECTATION_SHORT_DESCRIPTION}

    ExpectColumnDistinctValuesToContainSet is a \
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

    See Also:
        [ExpectColumnDistinctValuesToBeInSet](https://greatexpectations.io/expectations/expect_column_distinct_values_to_be_in_set)
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
                ExpectColumnDistinctValuesToContainSet(
                    column="test",
                    value_set=[1, 4]
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
                ExpectColumnDistinctValuesToContainSet(
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

    # This dictionary contains metadata for display in the public gallery
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
        "column.distinct_values.missing_from_column.count",
        "column.distinct_values.missing_from_column",
    )
    success_keys = ("value_set",)

    args_keys = (
        "column",
        "value_set",
    )

    class Config:
        title = "Expect column distinct values to contain set"

        @staticmethod
        def schema_extra(
            schema: Dict[str, Any], model: Type[ExpectColumnDistinctValuesToContainSet]
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

    @override
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
        template_str = ""

        if params.value_set:
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
            template_str = f"distinct values must contain this set: {value_set_str}."

        if renderer_configuration.include_column_name:
            template_str = f"$column {template_str}"

        renderer_configuration.template_str = template_str

        return renderer_configuration

    @override
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
        if renderer_configuration.configuration is None:
            raise ValueError("renderer_configuration.configuration is None.")  # noqa: TRY003 # FIXME CoP
        params = substitute_none_for_missing(
            renderer_configuration.configuration.kwargs,
            [
                "column",
                "value_set",
                "row_condition",
                "condition_parser",
            ],
        )

        if params["value_set"] is None or len(params["value_set"]) == 0:
            values_string = "[ ]"
        else:
            for i, v in enumerate(params["value_set"]):
                params[f"v__{i!s}"] = v

            values_string = " ".join([f"$v__{i!s}" for i, v in enumerate(params["value_set"])])

        template_str = f"distinct values must contain this set: {values_string}."

        if renderer_configuration.include_column_name:
            template_str = f"$column {template_str}"

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
                content_block_type="string_template",
                string_template={
                    "template": template_str,
                    "params": params,
                    "styling": styling,
                },
            )
        ]

    @override
    def _validate(
        self,
        metrics: Dict,
        runtime_configuration: Optional[dict] = None,
        execution_engine: Optional[ExecutionEngine] = None,
    ):
        # Get count of missing values (expected values not in column) - computed in database
        missing_count = metrics.get("column.distinct_values.missing_from_column.count", 0)

        # Get sample of missing values (expected values not in column) - limited by SQL LIMIT
        missing_values = metrics.get("column.distinct_values.missing_from_column", [])

        # Success if all expected values exist in the column
        success = missing_count == 0

        # Check partial_unexpected_count setting to determine if partial lists should be included
        # For distinct values Expectations, always use MAX_DISTINCT_VALUES as the limit
        # but respect partial_unexpected_count: 0 to exclude the list entirely
        result_format = (
            runtime_configuration.get("result_format", {}) if runtime_configuration else {}
        )
        partial_unexpected_count = result_format.get("partial_unexpected_count", 20)
        include_partial_lists = partial_unexpected_count > 0

        result_dict: Dict[str, Any] = {
            "observed_value": None,
            "missing_count": missing_count,
        }

        if include_partial_lists:
            result_dict["partial_missing_list"] = missing_values[:MAX_DISTINCT_VALUES]

        return {
            "success": success,
            "result": result_dict,
        }

    @classmethod
    @renderer(renderer_type=AtomicDiagnosticRendererType.OBSERVED_VALUE)
    @override
    def _atomic_diagnostic_observed_value(
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> RenderedAtomicContent:
        renderer_configuration: RendererConfiguration = RendererConfiguration(
            configuration=configuration,
            result=result,
            runtime_configuration=runtime_configuration,
        )
        ov_param_prefix = "ov__"
        ov_param_name = "observed_value"

        # Get missing values from partial_missing_list
        missing_values = result.get("result", {}).get("partial_missing_list", []) if result else []
        renderer_configuration.add_param(
            name=ov_param_name,
            param_type=RendererValueType.ARRAY,
            value=missing_values,
        )
        renderer_configuration = cls._add_array_params(
            array_param_name=ov_param_name,
            param_prefix=ov_param_prefix,
            renderer_configuration=renderer_configuration,
        )

        template_str_list = []
        for name, schema in renderer_configuration.params:
            if not name.startswith(ov_param_prefix):
                continue
            # All values in observed_value are now missing (expected values not in column)
            renderer_configuration.params.__dict__[
                name
            ].render_state = ObservedValueRenderState.MISSING.value
            template_str_list.append(f"${name}")

        renderer_configuration.template_str = " ".join(template_str_list)

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
