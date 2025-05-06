from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Tuple, Type, Union

from great_expectations.compatibility import pydantic
from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.result_format import ResultFormat
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
            target_results_with_dup_counts = Counter(tuple(row.values()) for row in target_results)
            source_results_with_dup_counts = Counter(tuple(row.values()) for row in source_results)
            # decrements source row count values by target row count values
            source_results_with_dup_counts.subtract(target_results_with_dup_counts)

            missing_count = 0
            unexpected_count = 0

            for subtracted_count in source_results_with_dup_counts.values():
                # if row was seen more in source than in target, it is missing
                if subtracted_count > 0:
                    missing_count += subtracted_count
                # if row was seen more in target than in source, it is unexpected
                elif subtracted_count < 0:
                    unexpected_count += -subtracted_count

            # we only consider "missing" records for failure calcs if they exist
            # this avoids double counting missing + unexpected when
            # a transformation occurred during copy from source to target use-case
            # e.g. if 1 row changes during table copy,
            #      there will be 1 missing row, and 1 unexpected row
            unexpected_count = missing_count or unexpected_count
            unexpected_percent = unexpected_count / source_result_count * 100

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
