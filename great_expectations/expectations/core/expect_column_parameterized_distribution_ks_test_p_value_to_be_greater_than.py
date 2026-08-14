from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Optional, Type, Union

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
    "Expect the p-value of a one-sample Kolmogorov-Smirnov test comparing the column to a "
    "named, parameterized theoretical distribution to be greater than or equal to a threshold."
)
DISTRIBUTION_DESCRIPTION = (
    "The name of the scipy.stats continuous distribution to test against "
    "(e.g. 'norm', 'expon', 'beta', 'gamma', 'uniform', 'chi2', 'lognorm')."
)
P_VALUE_DESCRIPTION = (
    "The threshold p-value. The Expectation succeeds when the observed Kolmogorov-Smirnov "
    "p-value is greater than or equal to this value. Must be strictly between 0 and 1. Defaults to 0.05."  # noqa: E501 # FIXME CoP
)
PARAMS_DESCRIPTION = (
    "The parameters of the theoretical distribution, supplied either positionally as a list "
    "or by name as a dict (e.g. {'mean': 0, 'std_dev': 1} for 'norm')."
)
SUPPORTED_DATA_SOURCES = [
    SupportedDataSources.PANDAS.value,
]
DATA_QUALITY_ISSUES = [DataQualityIssues.NUMERIC.value]


class ExpectColumnParameterizedDistributionKsTestPValueToBeGreaterThan(ColumnAggregateExpectation):
    __doc__ = f"""{EXPECTATION_SHORT_DESCRIPTION}

    ExpectColumnParameterizedDistributionKsTestPValueToBeGreaterThan is a \
    Column Aggregate Expectation.

    Column Aggregate Expectations are one of the most common types of Expectation.
    They are evaluated for a single column, and produce an aggregate Metric, such as a mean, standard deviation, number of unique values, column type, etc.
    If that Metric meets the conditions you set, the Expectation considers that data valid.

    The Kolmogorov-Smirnov test compares the empirical distribution of the column with the \
    cumulative distribution function of the named theoretical distribution. A large p-value \
    indicates that the data are consistent with having been drawn from that distribution.

    Args:
        column (str): \
            {COLUMN_DESCRIPTION}
        distribution (str): \
            {DISTRIBUTION_DESCRIPTION}
        p_value (float): \
            {P_VALUE_DESCRIPTION}
        params (list or dict or None): \
            {PARAMS_DESCRIPTION}

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
          p-value of the Kolmogorov-Smirnov test.
        * The Expectation succeeds when the observed p-value is greater than or equal to p_value.

    Supported Data Sources:
        [{SUPPORTED_DATA_SOURCES[0]}](https://docs.greatexpectations.io/docs/application_integration_support/)

    Data Quality Issues:
        {DATA_QUALITY_ISSUES[0]}

    Example Data:
                test
            0 	0.1
            1 	-0.2
            2 	0.4
            3   -0.5
            4   0.3

    Code Examples:
        Passing Case:
            Input:
                ExpectColumnParameterizedDistributionKsTestPValueToBeGreaterThan(
                    column="test",
                    distribution="norm",
                    p_value=0.05,
                    params={{"mean": 0, "std_dev": 1}}
            )

            Output:
                {{
                  "exception_info": {{
                    "raised_exception": false,
                    "exception_traceback": null,
                    "exception_message": null
                  }},
                  "result": {{
                    "observed_value": 0.9
                  }},
                  "meta": {{}},
                  "success": true
                }}

        Failing Case:
            Input:
                ExpectColumnParameterizedDistributionKsTestPValueToBeGreaterThan(
                    column="test",
                    distribution="expon",
                    p_value=0.05
            )

            Output:
                {{
                  "exception_info": {{
                    "raised_exception": false,
                    "exception_traceback": null,
                    "exception_message": null
                  }},
                  "result": {{
                    "observed_value": 0.0001
                  }},
                  "meta": {{}},
                  "success": false
                }}
    """  # noqa: E501 # FIXME CoP

    distribution: str = pydantic.Field(description=DISTRIBUTION_DESCRIPTION)
    p_value: Union[float, SuiteParameterDict] = pydantic.Field(
        default=0.05, description=P_VALUE_DESCRIPTION
    )
    params: Union[List[float], Dict[str, float], SuiteParameterDict, None] = pydantic.Field(
        default=None, description=PARAMS_DESCRIPTION
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

    metric_dependencies = ("column.parameterized_distribution_ks_test_p_value",)
    success_keys = (
        "distribution",
        "p_value",
        "params",
    )
    args_keys = (
        "column",
        "distribution",
        "p_value",
        "params",
    )

    class Config:
        title = "Expect column parameterized distribution KS test p-value to be greater than"

        @staticmethod
        def schema_extra(
            schema: Dict[str, Any],
            model: Type[ExpectColumnParameterizedDistributionKsTestPValueToBeGreaterThan],
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
            ("distribution", RendererValueType.STRING),
            ("p_value", RendererValueType.NUMBER),
        )
        for name, param_type in add_param_args:
            renderer_configuration.add_param(name=name, param_type=param_type)

        template_str = (
            "Kolmogorov-Smirnov test p-value against the $distribution distribution "
            "must be greater than or equal to $p_value."
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
                "distribution",
                "p_value",
                "row_condition",
                "condition_parser",
            ],
        )

        template_str = (
            "Kolmogorov-Smirnov test p-value against the $distribution distribution "
            "must be greater than or equal to $p_value."
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
        p_value = configuration.kwargs.get("p_value", self._get_default_value("p_value"))

        ks_result = metrics["column.parameterized_distribution_ks_test_p_value"]
        # scipy returns a KstestResult (statistic, pvalue) named tuple.
        observed_statistic = float(ks_result[0])
        observed_p_value = float(ks_result[1])

        # Success is inclusive at the boundary (p-value == p_value passes), matching the legacy V2
        # behavior of this expectation. (The sibling chi-square and bootstrapped-KS expectations use
        # a strict comparison, each preserving its own legacy behavior.)
        return {
            "success": bool(observed_p_value >= p_value),
            "result": {
                "observed_value": observed_p_value,
                "details": {
                    "observed_ks_result": {
                        "statistic": observed_statistic,
                        "pvalue": observed_p_value,
                    },
                },
            },
        }
