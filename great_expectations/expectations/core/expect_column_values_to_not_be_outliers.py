from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Dict, Literal, Type, Union

from great_expectations.compatibility import pydantic
from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.suite_parameters import (
    SuiteParameterDict,  # noqa: TC001 # FIXME CoP
)
from great_expectations.expectations.expectation import ColumnMapExpectation
from great_expectations.expectations.metadata_types import DataQualityIssues, SupportedDataSources
from great_expectations.expectations.model_field_descriptions import (
    COLUMN_DESCRIPTION,
    FAILURE_SEVERITY_DESCRIPTION,
    MOSTLY_DESCRIPTION,
)
from great_expectations.render.renderer_configuration import (
    RendererConfiguration,
    RendererValueType,
)

if TYPE_CHECKING:
    from great_expectations.render.renderer_configuration import AddParamArgs

EXPECTATION_SHORT_DESCRIPTION = "Expect numeric column values to not be statistical outliers."
METHOD_DESCRIPTION = (
    'The outlier detection method: "iqr" uses the quartiles and the interquartile range, '
    'as Tukey\'s fences do; "std" uses the mean and sample standard deviation.'
)
MULTIPLIER_DESCRIPTION = "The threshold multiplier applied to the selected spread statistic."
DEFAULT_METHOD = "iqr"
DEFAULT_MULTIPLIER = 1.5
DATA_QUALITY_ISSUES = [DataQualityIssues.NUMERIC.value]
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


class ExpectColumnValuesToNotBeOutliers(ColumnMapExpectation):
    __doc__ = f"""{EXPECTATION_SHORT_DESCRIPTION}

    The two methods draw the window of acceptable values differently. The "iqr" method
    uses Tukey's fences: with `Q1` and `Q3` the first and third quartiles and
    `IQR = Q3 - Q1`, a value is an outlier when it falls below `Q1 - multiplier * IQR` or
    above `Q3 + multiplier * IQR`. Each side is tested against its own quartile, so on
    skewed data the window reaches further out on the longer tail, and a value sitting
    exactly on a fence is not an outlier. The "std" method measures symmetrically around
    the mean instead: a value is an outlier when
    `|value - mean| >= multiplier * standard_deviation`. Null values are excluded from
    both the aggregate statistics and row-level evaluation.

    A column with no dispersion is a special case. Under "iqr", a zero multiplier - or a
    zero interquartile range - collapses the fences onto the quartiles themselves, leaving
    the closed interval from `Q1` to `Q3`, so a constant column reports no outliers. Under
    "std", a threshold of zero admits only values equal to the mean, so a constant column
    again reports none. When the batch cannot produce the statistics at all, as for an
    empty column or for a single value under a sample standard deviation, there is nothing
    to measure against and no value is reported as an outlier.

    ExpectColumnValuesToNotBeOutliers is a Column Map Expectation.

    Column Map Expectations are evaluated for a single column and ask a yes/no question for
    every non-null row. The percentage of rows that satisfy the condition is compared with
    the configured `mostly` value.

    Args:
        column (str): \
            {COLUMN_DESCRIPTION}

    Keyword Args:
        method (str): \
            {METHOD_DESCRIPTION} Default "iqr".
        multiplier (float): \
            {MULTIPLIER_DESCRIPTION} Default 1.5.

    Other Parameters:
        mostly (None or a float between 0 and 1): \
            {MOSTLY_DESCRIPTION} \
            For more detail, see [mostly](https://docs.greatexpectations.io/docs/reference/expectations/standard_arguments/#mostly). Default 1.
        result_format (str or None): \
            Which output mode to use: BOOLEAN_ONLY, BASIC, COMPLETE, or SUMMARY. \
            For more detail, see [result_format](https://docs.greatexpectations.io/docs/reference/expectations/result_format).
        catch_exceptions (boolean or None): \
            If True, catch exceptions and include them in the result.
        meta (dict or None): \
            A JSON-serializable dictionary included in the result without modification.
        severity (str or None): \
            {FAILURE_SEVERITY_DESCRIPTION}

    Returns:
        An [ExpectationSuiteValidationResult](https://docs.greatexpectations.io/docs/terms/validation_result)

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
                amount
            0   10
            1   11
            2   12
            3   13
            4   100

    Code Examples:
        Passing Case:
            Input:
                ExpectColumnValuesToNotBeOutliers(
                    column="amount",
                    method="std",
                    multiplier=3.0,
                )

            Output:
                {{
                  "exception_info": {{
                    "raised_exception": false,
                    "exception_traceback": null,
                    "exception_message": null
                  }},
                  "result": {{
                    "element_count": 5,
                    "unexpected_count": 0,
                    "unexpected_percent": 0.0,
                    "partial_unexpected_list": [],
                    "missing_count": 0,
                    "missing_percent": 0.0,
                    "unexpected_percent_total": 0.0,
                    "unexpected_percent_nonmissing": 0.0
                  }},
                  "meta": {{}},
                  "success": true
                }}

        Failing Case:
            Input:
                ExpectColumnValuesToNotBeOutliers(
                    column="amount",
                    method="iqr",
                    multiplier=1.5,
                )

            Output:
                {{
                  "exception_info": {{
                    "raised_exception": false,
                    "exception_traceback": null,
                    "exception_message": null
                  }},
                  "result": {{
                    "element_count": 5,
                    "unexpected_count": 1,
                    "unexpected_percent": 20.0,
                    "partial_unexpected_list": [
                      100
                    ],
                    "missing_count": 0,
                    "missing_percent": 0.0,
                    "unexpected_percent_total": 20.0,
                    "unexpected_percent_nonmissing": 20.0
                  }},
                  "meta": {{}},
                  "success": false
                }}
    """  # noqa: E501 # FIXME CoP

    method: Union[Literal["iqr", "std"], SuiteParameterDict] = pydantic.Field(
        default=DEFAULT_METHOD,
        description=METHOD_DESCRIPTION,
    )
    multiplier: Union[float, SuiteParameterDict] = pydantic.Field(
        default=DEFAULT_MULTIPLIER,
        ge=0,
        description=MULTIPLIER_DESCRIPTION,
    )

    library_metadata: ClassVar[Dict[str, Union[str, list, bool]]] = {
        "maturity": "production",
        "tags": ["core expectation", "column map expectation", "outlier detection"],
        "contributors": [
            "@chavalasantosh",
            "@rexboyce",
            "@lodeous",
            "@bragleg",
        ],
        "requirements": [],
        "has_full_test_suite": True,
        "manually_reviewed_code": True,
    }
    _library_metadata = library_metadata

    map_metric = "column_values.not_outliers"
    success_keys = ("mostly", "method", "multiplier")
    args_keys = ("column",)

    class Config:
        title = "Expect column values to not be outliers"

        @staticmethod
        def schema_extra(
            schema: Dict[str, Any], model: Type[ExpectColumnValuesToNotBeOutliers]
        ) -> None:
            ColumnMapExpectation.Config.schema_extra(schema, model)
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
            ("mostly", RendererValueType.NUMBER),
        )
        for name, param_type in add_param_args:
            renderer_configuration.add_param(name=name, param_type=param_type)

        # The template always names the method and the multiplier, but a configuration
        # that left either at its default does not carry it in kwargs - and add_param
        # drops a param it cannot find a value for, which would render the placeholder
        # itself. Supply the model defaults so the rendered sentence stays true.
        defaulted_param_args: AddParamArgs = (
            ("method", RendererValueType.STRING),
            ("multiplier", RendererValueType.NUMBER),
        )
        defaults: dict = {"method": DEFAULT_METHOD, "multiplier": DEFAULT_MULTIPLIER}
        for name, param_type in defaulted_param_args:
            renderer_configuration.add_param(
                name=name,
                param_type=param_type,
                value=renderer_configuration.kwargs.get(name, defaults[name]),
            )

        template_str = (
            "values must not be statistical outliers using the $method method "
            "with a multiplier of $multiplier"
        )
        params = renderer_configuration.params
        if params.mostly and params.mostly.value < 1.0:
            renderer_configuration = cls._add_mostly_pct_param(
                renderer_configuration=renderer_configuration
            )
            template_str += ", at least $mostly_pct % of the time."
        else:
            template_str += "."

        if renderer_configuration.include_column_name:
            template_str = f"$column {template_str}"

        renderer_configuration.template_str = template_str
        return renderer_configuration
