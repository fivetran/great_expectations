from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional, Type, Union

from great_expectations.compatibility import pydantic
from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.suite_parameters import (
    SuiteParameterDict,  # noqa: TC001 # FIXME CoP
)
from great_expectations.expectations.expectation import (
    ColumnAggregateExpectation,
    _style_row_condition,
    render_suite_parameter_string,
)
from great_expectations.expectations.metadata_types import DataQualityIssues, SupportedDataSources
from great_expectations.expectations.model_field_descriptions import (
    COLUMN_DESCRIPTION,
    FAILURE_SEVERITY_DESCRIPTION,
)
from great_expectations.render import (
    LegacyRendererType,
    RenderedStringTemplateContent,
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

if TYPE_CHECKING:
    from great_expectations.core import (
        ExpectationValidationResult,
    )
    from great_expectations.execution_engine import ExecutionEngine
    from great_expectations.expectations.expectation_configuration import (
        ExpectationConfiguration,
    )
    from great_expectations.render.renderer_configuration import AddParamArgs

EXPECTATION_SHORT_DESCRIPTION = (
    "Expect the bootstrapped Kolmogorov-Smirnov test p-value statistic comparing the column to a "
    "continuous partition object to be greater than a threshold."
)
PARTITION_OBJECT_DESCRIPTION = (
    "The expected continuous partition object, with finite ``bins`` and normalized ``weights`` and "
    "no tail weights."
)
P_DESCRIPTION = (
    "The threshold below which a p-value counts as a failure. The Expectation succeeds when the "
    "bootstrapped statistic is greater than this value. Defaults to 0.05."
)
BOOTSTRAP_SAMPLES_DESCRIPTION = (
    "The number of bootstrap rounds to perform. Defaults to 1000 when not provided."
)
BOOTSTRAP_SAMPLE_SIZE_DESCRIPTION = (
    "The number of elements to draw (with replacement) in each bootstrap round. Defaults to "
    "twice the number of partition weights when not provided."
)
SUPPORTED_DATA_SOURCES = [
    SupportedDataSources.PANDAS.value,
]
DATA_QUALITY_ISSUES = [DataQualityIssues.NUMERIC.value]


class ExpectColumnBootstrappedKsTestPValueToBeGreaterThan(ColumnAggregateExpectation):
    __doc__ = f"""{EXPECTATION_SHORT_DESCRIPTION}

    ExpectColumnBootstrappedKsTestPValueToBeGreaterThan is a \
    Column Aggregate Expectation.

    Column Aggregate Expectations are one of the most common types of Expectation.
    They are evaluated for a single column, and produce an aggregate Metric, such as a mean, standard deviation, number of unique values, column type, etc.
    If that Metric meets the conditions you set, the Expectation considers that data valid.

    This Expectation repeatedly draws bootstrap samples from the column and runs a one-sample \
    Kolmogorov-Smirnov test against the cumulative distribution function implied by the provided \
    continuous partition object. The reported statistic is the fraction of bootstrap rounds whose \
    KS p-value is at least ``p``; a high value indicates the data are consistent with the partition.

    Args:
        column (str): \
            {COLUMN_DESCRIPTION}
        partition_object (dict): \
            {PARTITION_OBJECT_DESCRIPTION} See [partition_object](https://docs.greatexpectations.io/docs/reference/expectations/distributional_expectations/#partition-objects).
        p (float): \
            {P_DESCRIPTION}
        bootstrap_samples (int or None): \
            {BOOTSTRAP_SAMPLES_DESCRIPTION}
        bootstrap_sample_size (int or None): \
            {BOOTSTRAP_SAMPLE_SIZE_DESCRIPTION}

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
        * observed_value field in the result object is customized for this expectation to be the \
          bootstrapped p-value statistic (the fraction of bootstrap rounds whose KS p-value was at least ``p``).
        * The Expectation succeeds when the observed statistic is greater than ``p``.
        * Because the statistic is computed from random bootstrap samples, the observed_value may vary \
          slightly between runs.

    Supported Data Sources:
        [{SUPPORTED_DATA_SOURCES[0]}](https://docs.greatexpectations.io/docs/application_integration_support/)

    Data Quality Issues:
        {DATA_QUALITY_ISSUES[0]}

    Example Data:
                test
            0 	0.1
            1 	0.4
            2 	0.6
            3   0.9
            4   0.5

    Code Examples:
        Passing Case:
            Input:
                ExpectColumnBootstrappedKsTestPValueToBeGreaterThan(
                    column="test",
                    partition_object={{
                        "bins": [0.0, 0.25, 0.5, 0.75, 1.0],
                        "weights": [0.25, 0.25, 0.25, 0.25],
                    }},
                    p=0.05
            )

            Output:
                {{
                  "exception_info": {{
                    "raised_exception": false,
                    "exception_traceback": null,
                    "exception_message": null
                  }},
                  "result": {{
                    "observed_value": 0.8
                  }},
                  "meta": {{}},
                  "success": true
                }}

        Failing Case:
            Input:
                ExpectColumnBootstrappedKsTestPValueToBeGreaterThan(
                    column="test",
                    partition_object={{
                        "bins": [0.0, 0.25, 0.5, 0.75, 1.0],
                        "weights": [0.97, 0.01, 0.01, 0.01],
                    }},
                    p=0.05
            )

            Output:
                {{
                  "exception_info": {{
                    "raised_exception": false,
                    "exception_traceback": null,
                    "exception_message": null
                  }},
                  "result": {{
                    "observed_value": 0.0
                  }},
                  "meta": {{}},
                  "success": false
                }}
    """  # noqa: E501 # FIXME CoP

    partition_object: Union[dict, SuiteParameterDict] = pydantic.Field(
        description=PARTITION_OBJECT_DESCRIPTION
    )
    p: Union[float, SuiteParameterDict] = pydantic.Field(default=0.05, description=P_DESCRIPTION)
    bootstrap_samples: Union[int, SuiteParameterDict, None] = pydantic.Field(
        default=None, description=BOOTSTRAP_SAMPLES_DESCRIPTION
    )
    bootstrap_sample_size: Union[int, SuiteParameterDict, None] = pydantic.Field(
        default=None, description=BOOTSTRAP_SAMPLE_SIZE_DESCRIPTION
    )

    library_metadata: ClassVar[Dict[str, Union[str, list, bool]]] = {
        "maturity": "production",
        "tags": [
            "core expectation",
            "column aggregate expectation",
            "distributional expectation",
        ],
        "contributors": ["@great_expectations"],
        "requirements": [],
        "has_full_test_suite": True,
        "manually_reviewed_code": True,
    }
    _library_metadata = library_metadata

    metric_dependencies = ("column.bootstrapped_ks_test_p_value",)
    success_keys = (
        "partition_object",
        "p",
        "bootstrap_samples",
        "bootstrap_sample_size",
    )
    args_keys = (
        "column",
        "partition_object",
        "p",
        "bootstrap_samples",
        "bootstrap_sample_size",
    )

    class Config:
        title = "Expect column bootstrapped KS test p-value to be greater than"

        @staticmethod
        def schema_extra(
            schema: Dict[str, Any],
            model: Type[ExpectColumnBootstrappedKsTestPValueToBeGreaterThan],
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
    def _prescriptive_template(
        cls,
        renderer_configuration: RendererConfiguration,
    ) -> RendererConfiguration:
        add_param_args: AddParamArgs = (
            ("column", RendererValueType.STRING),
            ("p", RendererValueType.NUMBER),
        )
        for name, param_type in add_param_args:
            renderer_configuration.add_param(name=name, param_type=param_type)

        template_str = (
            "bootstrapped Kolmogorov-Smirnov test p-value statistic must be greater than $p."
        )
        if renderer_configuration.include_column_name:
            template_str = f"$column {template_str}"

        renderer_configuration.template_str = template_str
        return renderer_configuration

    @classmethod
    @override
    @renderer(renderer_type=LegacyRendererType.PRESCRIPTIVE)
    @render_suite_parameter_string
    def _prescriptive_renderer(  # type: ignore[override] # TODO: Fix this type ignore
        cls,
        configuration: ExpectationConfiguration,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
        **kwargs,
    ):
        runtime_configuration = runtime_configuration or {}
        include_column_name = runtime_configuration.get("include_column_name") is not False
        styling = runtime_configuration.get("styling")
        params = substitute_none_for_missing(
            configuration.kwargs,
            [
                "column",
                "p",
                "row_condition",
                "condition_parser",
            ],
        )

        template_str = (
            "bootstrapped Kolmogorov-Smirnov test p-value statistic must be greater than $p."
        )
        if include_column_name:
            template_str = f"$column {template_str}"

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
        configuration = self.configuration
        p = configuration.kwargs.get("p", self._get_default_value("p"))

        metric_result = metrics["column.bootstrapped_ks_test_p_value"]
        observed_value = float(metric_result["observed_value"])
        details = metric_result.get("details", {})

        # Forward the metric's details verbatim: alongside the bootstrap settings, they carry the
        # observed/expected partitions and CDFs, which are what a user needs to see why the test
        # failed (and which the legacy V2 result and the sibling chi-square expectation surface).
        return {
            "success": bool(observed_value > p),
            "result": {
                "observed_value": observed_value,
                "details": details,
            },
        }
