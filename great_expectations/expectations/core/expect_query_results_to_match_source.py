from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Dict, Tuple, Type, Union

from great_expectations.compatibility import pydantic
from great_expectations.compatibility.typing_extensions import override
from great_expectations.expectations.expectation import BatchExpectation
from great_expectations.expectations.metadata_types import DataQualityIssues, SupportedDataSources
from great_expectations.expectations.model_field_descriptions import MOSTLY_DESCRIPTION
from great_expectations.expectations.model_field_types import (
    MostlyField,  # noqa: TC001  # pydantic needs the actual type
)

if TYPE_CHECKING:
    from great_expectations.core import ExpectationValidationResult
    from great_expectations.execution_engine import ExecutionEngine


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
    SupportedDataSources.BIGQUERY.value,
    SupportedDataSources.SNOWFLAKE.value,
    SupportedDataSources.DATABRICKS.value,
    SupportedDataSources.REDSHIFT.value,
]
DATA_QUALITY_ISSUES = [DataQualityIssues.MULTI_ASSET.value]


class ExpectQueryResultsToMatchSource(BatchExpectation):
    __doc__ = f"""{EXPECTATION_SHORT_DESCRIPTION}

    ExpectQueryResultsToMatchSource executes one SQL query for each of \
    two Data Sources and compares their results. It validates that the results from \
    the current Data Asset's query matches those from the source Data Source's query \
    above a specified threshold.

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
    domain_keys: ClassVar[Tuple[str, ...]] = (
        "batch_id",
        "row_condition",
        "condition_parser",
    )

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

    @override
    def _validate(
        self,
        metrics: dict,
        runtime_configuration: dict | None = None,
        execution_engine: ExecutionEngine | None = None,
    ) -> Union[ExpectationValidationResult, dict]:
        target_results = metrics["target_query.table"]
        source_results = metrics["source_query.data_source_table"]

        target_set = {tuple(row) for row in target_results}
        source_set = {tuple(row) for row in source_results}

        common_rows = target_set.intersection(source_set)

        total_rows = len(target_set)
        if total_rows == 0:
            match_percentage = 100.0  # If there are no rows, consider it a perfect match
        else:
            match_percentage = (len(common_rows) / total_rows) * 100.0

        success_kwargs = self._get_success_kwargs()
        mostly = success_kwargs.get("mostly", 1)

        return {
            "success": match_percentage >= (mostly * 100),
            "result": {
                "observed_value": match_percentage,
                "details": {
                    "target_row_count": len(target_set),
                    "source_row_count": len(source_set),
                    "matching_row_count": len(common_rows),
                },
            },
        }
