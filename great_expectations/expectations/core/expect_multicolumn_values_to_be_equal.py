from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Literal, Optional, Type, Union

from great_expectations.compatibility import pydantic
from great_expectations.core.suite_parameters import SuiteParameterDict  # noqa: TC001 # FIXME CoP
from great_expectations.expectations.expectation import MulticolumnMapExpectation
from great_expectations.expectations.metadata_types import DataQualityIssues, SupportedDataSources
from great_expectations.expectations.model_field_descriptions import (
    COLUMN_LIST_DESCRIPTION,
    FAILURE_SEVERITY_DESCRIPTION,
    IGNORE_ROW_IF_DESCRIPTION,
    MOSTLY_DESCRIPTION,
)
from great_expectations.render import RenderedStringTemplateContent
from great_expectations.render.components import LegacyRendererType
from great_expectations.render.renderer.renderer import renderer
from great_expectations.render.renderer_configuration import (
    RendererConfiguration,
    RendererValueType,
)
from great_expectations.render.util import num_to_str, substitute_none_for_missing

if TYPE_CHECKING:
    from great_expectations.core import ExpectationValidationResult
    from great_expectations.expectations.expectation_configuration import ExpectationConfiguration
    from great_expectations.render.renderer_configuration import AddParamArgs

EXPECTATION_SHORT_DESCRIPTION = (
    "Expect the values in each row of the specified columns to be equal."
)
DATA_QUALITY_ISSUES = [DataQualityIssues.VALIDITY.value]
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


class ExpectMulticolumnValuesToBeEqual(MulticolumnMapExpectation):
    __doc__ = f"""{EXPECTATION_SHORT_DESCRIPTION}

    ExpectMulticolumnValuesToBeEqual is a Multicolumn Map Expectation.

    Multicolumn Map Expectations evaluate a set of columns row by row and calculate the
    percentage of rows that meet the condition. Nulls compare safely: a row of null values
    is equal, while a null and a non-null value are not equal.

    Args:
        column_list (tuple or list): {COLUMN_LIST_DESCRIPTION}

    Other Parameters:
        ignore_row_if (str): {IGNORE_ROW_IF_DESCRIPTION} Default "never".
        mostly (None or a float between 0 and 1): {MOSTLY_DESCRIPTION}
        result_format (str or None): Which output mode to use: BOOLEAN_ONLY, BASIC,
            COMPLETE, or SUMMARY.
        catch_exceptions (boolean or None): If True, include exceptions in the result.
        meta (dict or None): A JSON-serializable dictionary included in the output.
        severity (str or None): {FAILURE_SEVERITY_DESCRIPTION}

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
            source  copy  archive
        0   A       A     A
        1   B       B     C
        2   null    null  null

    Code Examples:
        Passing Case:
            ExpectMulticolumnValuesToBeEqual(
                column_list=["source", "copy", "archive"], mostly=0.66
            )

        Failing Case:
            ExpectMulticolumnValuesToBeEqual(
                column_list=["source", "copy", "archive"]
            )
    """

    ignore_row_if: Union[
        Literal["all_values_are_missing", "any_value_is_missing", "never"],
        SuiteParameterDict,
    ] = pydantic.Field(default="never", description=IGNORE_ROW_IF_DESCRIPTION)

    library_metadata: ClassVar[Dict[str, Union[str, list, bool]]] = {
        "maturity": "production",
        "tags": ["core expectation", "multi-column expectation"],
        "contributors": ["@karthigaiselvanm", "@jayamnatraj", "@AtomicGlance"],
        "requirements": [],
        "has_full_test_suite": True,
        "manually_reviewed_code": True,
    }
    _library_metadata = library_metadata

    map_metric = "multicolumn_values.equal"
    success_keys = ("column_list", "ignore_row_if", "mostly")
    args_keys = ("column_list",)

    class Config:
        title = "Expect multicolumn values to be equal"

        @staticmethod
        def schema_extra(
            schema: Dict[str, Any], model: Type[ExpectMulticolumnValuesToBeEqual]
        ) -> None:
            MulticolumnMapExpectation.Config.schema_extra(schema, model)
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
    def _prescriptive_template(
        cls, renderer_configuration: RendererConfiguration
    ) -> RendererConfiguration:
        add_param_args: AddParamArgs = (
            ("column_list", RendererValueType.ARRAY),
            ("mostly", RendererValueType.NUMBER),
            ("ignore_row_if", RendererValueType.STRING),
        )
        for name, param_type in add_param_args:
            renderer_configuration.add_param(name=name, param_type=param_type)

        template_str = "Values across columns "
        if renderer_configuration.params.column_list:
            renderer_configuration = cls._add_array_params(
                array_param_name="column_list",
                param_prefix="column_list_",
                renderer_configuration=renderer_configuration,
            )
            template_str += cls._get_array_string(
                array_param_name="column_list",
                param_prefix="column_list_",
                renderer_configuration=renderer_configuration,
            )
        if (
            renderer_configuration.params.mostly
            and renderer_configuration.params.mostly.value < 1.0
        ):
            renderer_configuration = cls._add_mostly_pct_param(renderer_configuration)
            template_str += " must be equal, at least $mostly_pct % of the time."
        else:
            template_str += " must be equal."
        renderer_configuration.template_str = template_str
        return renderer_configuration

    @classmethod
    @renderer(renderer_type=LegacyRendererType.PRESCRIPTIVE)
    def _prescriptive_renderer(
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
        **kwargs,
    ) -> List[RenderedStringTemplateContent]:
        runtime_configuration = runtime_configuration or {}
        params = substitute_none_for_missing(configuration.kwargs, ["column_list", "mostly"])
        mostly_str = ""
        if params["mostly"] is not None:
            params["mostly_pct"] = num_to_str(params["mostly"] * 100, no_scientific=True)
            mostly_str = ", at least $mostly_pct % of the time"

        column_list_str = ""
        for index, column_name in enumerate(params["column_list"]):
            if index:
                column_list_str += ", "
            column_list_str += f"$column_list_{index}"
            params[f"column_list_{index}"] = column_name

        return [
            RenderedStringTemplateContent(
                **{
                    "content_block_type": "string_template",
                    "string_template": {
                        "template": (
                            f"Values across columns {column_list_str} must be equal{mostly_str}."
                        ),
                        "params": params,
                        "styling": runtime_configuration.get("styling"),
                    },
                }
            )
        ]
