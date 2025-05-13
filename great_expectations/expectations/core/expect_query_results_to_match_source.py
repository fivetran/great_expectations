from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Literal, Optional, Tuple, Type, Union

from great_expectations.compatibility import pydantic
from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.result_format import ResultFormat
from great_expectations.expectations.expectation import (
    BatchExpectation,
    render_suite_parameter_string,
)
from great_expectations.expectations.metadata_types import DataQualityIssues, SupportedDataSources
from great_expectations.expectations.model_field_descriptions import MOSTLY_DESCRIPTION
from great_expectations.expectations.model_field_types import (
    MostlyField,  # noqa: TC001  # pydantic needs the actual type
)
from great_expectations.render import (
    AtomicPrescriptiveRendererType,
    RenderedAtomicContent,
    RenderedAtomicValue,
)
from great_expectations.render.renderer.renderer import renderer
from great_expectations.render.renderer_configuration import (
    AddParamArgs,
    CodeBlock,
    CodeBlockLanguage,
    RendererConfiguration,
    RendererValueType,
)

if TYPE_CHECKING:
    from great_expectations.core import ExpectationValidationResult
    from great_expectations.execution_engine import ExecutionEngine
    from great_expectations.expectations.expectation_configuration import ExpectationConfiguration


EXPECTATION_SHORT_DESCRIPTION = (
    "This Expectation will check if the results of a query "
    "matches the results of a query against another Data Source."
)
TARGET_QUERY_DESCRIPTION = "A SQL query to be executed for this Data Asset."
SOURCE_DATA_SOURCE_NAME_DESCRIPTION = (
    "The name of the source Data Source to compare this Asset against."
)
SOURCE_QUERY_DESCRIPTION = "A SQL query to be executed for the source Data Source."
SUPPORTED_DATA_SOURCES = [
    SupportedDataSources.POSTGRESQL.value,
    SupportedDataSources.SNOWFLAKE.value,
    SupportedDataSources.DATABRICKS.value,
    SupportedDataSources.REDSHIFT.value,
    SupportedDataSources.SQLITE.value,
]
DATA_QUALITY_ISSUES = [DataQualityIssues.MULTI_ASSET.value]


class ExpectQueryResultsToMatchSource(BatchExpectation):
    __doc__ = f"""{EXPECTATION_SHORT_DESCRIPTION}

    ExpectQueryResultsToMatchSource executes one SQL query for each of \
    two Data Sources and compares their results. It validates that the results from \
    the current Data Source's query matches those from the source Data Source's query, \
    above a specified threshold.

    - Each record returned by the `target_query` will be compared to each record \
      returned by the `source_query`.
    - The maximum number of records that will be returned for comparison from \
      each query is 200.
    - The order of records returned does not matter unless \
      the number of records returned would be greater than 200.
    - Column names do not matter, but the order of the columns does.

    Match Percentage (100% - `unexpected_percent`) is compared to the `mostly` threshold \
    to determine pass/fail.
        e.g. `unexpected_percent` = 10%, `mostly` = 80%, (100% - 10%) > 80% - pass
             `unexpected_percent` = 10%, `mostly` = 91%, (100% - 10%) < 91% - fail


    The Match Percentage is computed by dividing the number of matching records \
    by the maximum number of records in either the source result or the target result.
       e.g.

    | Source Row Count | Target Row Count | Matches | Match Percentage |
    | ---------------- | ---------------- | ------- | ---------------- |
    | 100              | 100              | 100     | 100%             |
    | 25               | 100              | 25      | 25%              |
    | 100              | 25               | 1       | 1%               |

    If both the target and source queries return 0 records, \
    it is considered a successful result.


    Args:
        target_query (str): {TARGET_QUERY_DESCRIPTION}
        source_data_source_name (str): {SOURCE_DATA_SOURCE_NAME_DESCRIPTION}
        source_query (str): {SOURCE_QUERY_DESCRIPTION}
        mostly (float): {MOSTLY_DESCRIPTION}

    Returns:
        An [ExpectationSuiteValidationResult](https://docs.greatexpectations.io/docs/terms/validation_result)

    Supported Data Sources:
        [{SUPPORTED_DATA_SOURCES[0]}](https://docs.greatexpectations.io/docs/application_integration_support/)
        [{SUPPORTED_DATA_SOURCES[1]}](https://docs.greatexpectations.io/docs/application_integration_support/)
        [{SUPPORTED_DATA_SOURCES[2]}](https://docs.greatexpectations.io/docs/application_integration_support/)
        [{SUPPORTED_DATA_SOURCES[3]}](https://docs.greatexpectations.io/docs/application_integration_support/)
        [{SUPPORTED_DATA_SOURCES[4]}](https://docs.greatexpectations.io/docs/application_integration_support/)
    Data Quality Issues:
        {DATA_QUALITY_ISSUES[0]}
    """

    target_query: str = pydantic.Field(description=TARGET_QUERY_DESCRIPTION)
    source_data_source_name: str = pydantic.Field(description=SOURCE_DATA_SOURCE_NAME_DESCRIPTION)
    source_query: str = pydantic.Field(description=SOURCE_QUERY_DESCRIPTION)
    mostly: MostlyField = 1

    metric_dependencies: ClassVar[Tuple[str, ...]] = (
        "target_query.table",
        "source_query.data_source_table",
    )
    success_keys: ClassVar[Tuple[str, ...]] = (
        "target_query",
        "source_data_source_name",
        "source_query",
        "mostly",
    )
    domain_keys: ClassVar[Tuple[str, ...]] = ("batch_id",)

    class Config:
        title = "Expect query results to match source"

        @staticmethod
        def schema_extra(
            schema: Dict[str, Any], model: Type[ExpectQueryResultsToMatchSource]
        ) -> None:
            BatchExpectation.Config.schema_extra(schema, model)
            schema["properties"]["metadata"]["properties"].update(
                {
                    "data_quality_issues": {
                        "title": "Data Quality Issues",
                        "type": "array",
                        "const": DATA_QUALITY_ISSUES,
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
    def _get_query_rendered_content(
        cls,
        renderer_configuration: RendererConfiguration,
        query_type: Literal["source", "target"],
        add_param_args: AddParamArgs,
        template_str: Optional[str] = None,
    ) -> RenderedAtomicContent:
        for name, param_type in add_param_args:
            renderer_configuration.add_param(name=name, param_type=param_type)

        renderer_configuration.template_str = template_str

        renderer_configuration.code_block = CodeBlock(
            code_template_str=f"${query_type}_query",
            language=CodeBlockLanguage.SQL,
        )

        return RenderedAtomicContent(
            name=AtomicPrescriptiveRendererType.SUMMARY,
            value=RenderedAtomicValue(
                template=template_str or renderer_configuration.template_str,
                params=renderer_configuration.params.dict(),
                code_block=renderer_configuration.code_block,
                meta_notes=renderer_configuration.meta_notes,
                schema={"type": "com.superconductive.rendered.string"},
            ),
            value_type="StringValueType",
        )

    @classmethod
    @override
    @renderer(renderer_type=AtomicPrescriptiveRendererType.SUMMARY)
    @render_suite_parameter_string
    def _prescriptive_summary(
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> list[RenderedAtomicContent]:
        target_query_block = cls._get_query_rendered_content(
            query_type="target",
            add_param_args=(("target_query", RendererValueType.STRING),),
            template_str=None,  # `description` should override this
            renderer_configuration=RendererConfiguration(
                configuration=configuration,
                result=result,
                runtime_configuration=runtime_configuration,
            ),
        )
        source_query_block = cls._get_query_rendered_content(
            query_type="source",
            add_param_args=(
                ("source_data_source_name", RendererValueType.STRING),
                ("source_query", RendererValueType.STRING),
            ),
            template_str="Compare with Data Source $source_data_source_name",
            renderer_configuration=RendererConfiguration(
                configuration=configuration,
                result=result,
                runtime_configuration=runtime_configuration,
            ),
        )
        return [target_query_block, source_query_block]

    @override
    def _validate(
        self,
        metrics: dict,
        runtime_configuration: dict | None = None,
        execution_engine: ExecutionEngine | None = None,
    ) -> Union[ExpectationValidationResult, dict]:
        result_format: str | dict[str, Any] = self._get_result_format(
            runtime_configuration=runtime_configuration
        )

        target_results = metrics["target_query.table"]
        target_result_count = len(target_results)
        source_results = metrics["source_query.data_source_table"]
        source_result_count = len(source_results)

        if target_result_count + source_result_count == 0:
            unexpected_count = 0
            unexpected_percent = 0.0
        else:
            # creates a hashmap with row values as key and count of duplicate rows as value
            target_results_frequency_map = Counter(tuple(row.values()) for row in target_results)
            source_results_frequency_map = Counter(tuple(row.values()) for row in source_results)
            # decrements source row count values by target row count values
            count_in_source_not_target = source_results_frequency_map.copy()
            count_in_source_not_target.subtract(target_results_frequency_map)

            # Get the matches: if we see a value X times in source, and Y times in target, min(X, Y)
            # is the number of matches.
            matching_counts = {
                k: min(
                    target_results_frequency_map.get(k, 0),
                    source_results_frequency_map.get(k, 0),
                )
                for k in source_results_frequency_map
            }
            match_count = sum(matching_counts.values())

            # see docstring for explanation of why we use max of source or target here
            unexpected_count = max(source_result_count, target_result_count) - match_count
            unexpected_percent = (
                1 - (match_count / max(source_result_count, target_result_count))
            ) * 100

        success_kwargs = self._get_success_kwargs()
        mostly = success_kwargs.get("mostly", 1)
        success = (100 - unexpected_percent) >= (mostly * 100)

        if result_format == ResultFormat.BOOLEAN_ONLY:
            return {"success": success}
        else:
            return {
                "success": success,
                "result": {
                    "unexpected_count": unexpected_count,
                    "unexpected_percent": unexpected_percent,
                },
            }
