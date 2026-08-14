from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional, Type, Union

import pandas as pd
from scipy import stats

from great_expectations.compatibility import pydantic
from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.suite_parameters import (
    SuiteParameterDict,  # noqa: TC001 # FIXME CoP
)
from great_expectations.execution_engine.util import (
    is_valid_categorical_partition_object,
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
    "Expect the p-value of a Chi-square goodness-of-fit test comparing the observed categorical "
    "frequencies of the column to an expected partition object to be greater than a threshold."
)
PARTITION_OBJECT_DESCRIPTION = (
    "The expected categorical partition object, with ``values`` and normalized ``weights``."
)
P_DESCRIPTION = (
    "The threshold p-value. The Expectation succeeds when the observed Chi-square p-value is "
    "greater than this value. Defaults to 0.05."
)
TAIL_WEIGHT_HOLDOUT_DESCRIPTION = (
    "The amount of weight to split uniformly among values observed in the data but absent from "
    "the partition object. Provides a mechanism to make the test less strict. Defaults to 0."
)
SUPPORTED_DATA_SOURCES = [
    SupportedDataSources.PANDAS.value,
]
DATA_QUALITY_ISSUES = [DataQualityIssues.NUMERIC.value]


class ExpectColumnChisquareTestPValueToBeGreaterThan(ColumnAggregateExpectation):
    __doc__ = f"""{EXPECTATION_SHORT_DESCRIPTION}

    ExpectColumnChisquareTestPValueToBeGreaterThan is a \
    Column Aggregate Expectation.

    Column Aggregate Expectations are one of the most common types of Expectation.
    They are evaluated for a single column, and produce an aggregate Metric, such as a mean, standard deviation, number of unique values, column type, etc.
    If that Metric meets the conditions you set, the Expectation considers that data valid.

    The Chi-square goodness-of-fit test compares the observed value counts of the column with the \
    expected counts implied by the partition object. A large p-value indicates that the observed \
    distribution is consistent with the expected one.

    Args:
        column (str): \
            {COLUMN_DESCRIPTION}
        partition_object (dict): \
            {PARTITION_OBJECT_DESCRIPTION} See [partition_object](https://docs.greatexpectations.io/docs/reference/expectations/distributional_expectations/#partition-objects).
        p (float): \
            {P_DESCRIPTION}
        tail_weight_holdout (float): \
            {TAIL_WEIGHT_HOLDOUT_DESCRIPTION}

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
          p-value of the Chi-square test.
        * details.observed_partition and details.expected_partition are customized for this \
          expectation to be dicts representing the observed and expected partitions.
        * The Expectation succeeds when the observed p-value is greater than ``p``.

    Supported Data Sources:
        [{SUPPORTED_DATA_SOURCES[0]}](https://docs.greatexpectations.io/docs/application_integration_support/)

    Data Quality Issues:
        {DATA_QUALITY_ISSUES[0]}

    Example Data:
                test
            0 	"A"
            1 	"A"
            2 	"B"
            3   "B"
            4   "C"

    Code Examples:
        Passing Case:
            Input:
                ExpectColumnChisquareTestPValueToBeGreaterThan(
                    column="test",
                    partition_object={{"values": ["A", "B", "C"], "weights": [0.4, 0.4, 0.2]}},
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
                    "observed_value": 1.0
                  }},
                  "meta": {{}},
                  "success": true
                }}

        Failing Case:
            Input:
                ExpectColumnChisquareTestPValueToBeGreaterThan(
                    column="test",
                    partition_object={{"values": ["A", "B", "C"], "weights": [0.05, 0.05, 0.9]}},
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
                    "observed_value": 0.0001
                  }},
                  "meta": {{}},
                  "success": false
                }}
    """  # noqa: E501 # FIXME CoP

    partition_object: Union[dict, SuiteParameterDict] = pydantic.Field(
        description=PARTITION_OBJECT_DESCRIPTION
    )
    p: Union[float, SuiteParameterDict] = pydantic.Field(default=0.05, description=P_DESCRIPTION)
    tail_weight_holdout: Union[float, SuiteParameterDict] = pydantic.Field(
        default=0, ge=0, le=1, description=TAIL_WEIGHT_HOLDOUT_DESCRIPTION
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

    success_keys = (
        "partition_object",
        "p",
        "tail_weight_holdout",
    )
    args_keys = (
        "column",
        "partition_object",
        "p",
        "tail_weight_holdout",
    )

    class Config:
        title = "Expect column Chi-square test p-value to be greater than"

        @staticmethod
        def schema_extra(
            schema: Dict[str, Any],
            model: Type[ExpectColumnChisquareTestPValueToBeGreaterThan],
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

        template_str = "Chi-square test p-value must be greater than $p."
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

        template_str = "Chi-square test p-value must be greater than $p."
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
    def get_validation_dependencies(
        self,
        execution_engine: Optional[ExecutionEngine] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> ValidationDependencies:
        validation_dependencies: ValidationDependencies = super().get_validation_dependencies(
            execution_engine, runtime_configuration
        )
        domain_kwargs = self.configuration.get_domain_kwargs()
        validation_dependencies.set_metric_configuration(
            metric_name="column.value_counts",
            metric_configuration=MetricConfiguration(
                metric_name="column.value_counts",
                metric_domain_kwargs=domain_kwargs,
                metric_value_kwargs={"sort": "value"},
            ),
        )
        validation_dependencies.set_metric_configuration(
            metric_name="column_values.nonnull.count",
            metric_configuration=MetricConfiguration(
                metric_name="column_values.nonnull.count",
                metric_domain_kwargs=domain_kwargs,
                metric_value_kwargs=None,
            ),
        )
        return validation_dependencies

    @override
    def _validate(
        self,
        metrics: Dict,
        runtime_configuration: Optional[dict] = None,
        execution_engine: Optional[ExecutionEngine] = None,
    ):
        configuration = self.configuration
        partition_object = configuration.kwargs.get(
            "partition_object", self._get_default_value("partition_object")
        )
        p = configuration.kwargs.get("p", self._get_default_value("p"))
        tail_weight_holdout = configuration.kwargs.get(
            "tail_weight_holdout", self._get_default_value("tail_weight_holdout")
        )

        if not is_valid_categorical_partition_object(partition_object):
            raise ValueError("Invalid categorical partition object.")  # noqa: TRY003 # FIXME CoP

        element_count = metrics["column_values.nonnull.count"]
        observed_frequencies = metrics["column.value_counts"]
        # Convert to Series object to allow joining on index values
        expected_column = (
            pd.Series(
                partition_object["weights"],
                index=partition_object["values"],
                name="expected",
            )
            * element_count
        )
        # Join along the indices to allow proper comparison of both types of possible missing values
        test_df = pd.concat([expected_column, observed_frequencies], axis=1)

        na_counts = test_df.isnull().sum()

        # Handle NaN: if we expected something that's not there, it's just not there.
        test_df["count"] = test_df["count"].fillna(0)
        # Handle NaN: if something's there that was not expected, substitute the relevant value
        # for tail_weight_holdout
        if na_counts["expected"] > 0:
            # Scale existing expected values
            test_df["expected"] *= 1 - tail_weight_holdout
            # Fill NAs with holdout.
            test_df["expected"] = test_df["expected"].fillna(
                element_count * (tail_weight_holdout / na_counts["expected"])
            )

        test_result = float(stats.chisquare(test_df["count"], test_df["expected"])[1])

        # Normalize the outputs so they can be used as partitions into other expectations
        expected_weights = (test_df["expected"] / test_df["expected"].sum()).tolist()
        observed_weights = (test_df["count"] / test_df["count"].sum()).tolist()

        return {
            "success": bool(test_result > p),
            "result": {
                "observed_value": test_result,
                "details": {
                    "observed_partition": {
                        "values": test_df.index.tolist(),
                        "weights": observed_weights,
                    },
                    "expected_partition": {
                        "values": test_df.index.tolist(),
                        "weights": expected_weights,
                    },
                },
            },
        }
