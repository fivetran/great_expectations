from __future__ import annotations

from collections import Counter
from functools import cmp_to_key
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Literal, Optional, Tuple, Type, Union

from great_expectations import exceptions
from great_expectations.compatibility import pydantic
from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.result_format import ResultFormat
from great_expectations.core.suite_parameters import (
    SuiteParameterDict,  # noqa: TC001 # FIXME CoP
)
from great_expectations.expectations.expectation import (
    BatchExpectation,
    parse_value_to_observed_type,
    render_suite_parameter_string,
)
from great_expectations.expectations.metadata_types import DataQualityIssues, SupportedDataSources
from great_expectations.expectations.model_field_descriptions import (
    FAILURE_SEVERITY_DESCRIPTION,
    MOSTLY_DESCRIPTION,
)
from great_expectations.expectations.model_field_types import (
    MostlyField,  # noqa: TC001  # pydantic needs the actual type
)
from great_expectations.render.components import (
    AtomicDiagnosticRendererType,
    AtomicPrescriptiveRendererType,
    RenderedAtomicContent,
    RenderedAtomicValue,
)
from great_expectations.render.renderer.observed_value_renderer import ObservedValueRenderState
from great_expectations.render.renderer.renderer import renderer
from great_expectations.render.renderer_configuration import (
    AddParamArgs,
    CodeBlock,
    CodeBlockLanguage,
    RendererConfiguration,
    RendererSchema,
    RendererTableValue,
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
BASE_QUERY_DESCRIPTION = "A SQL query to be executed for this Data Asset."
COMPARISON_DATA_SOURCE_NAME_DESCRIPTION = (
    "The name of the comparison Data Source to compare this Asset against."
)
COMPARISON_QUERY_DESCRIPTION = "A SQL query to be executed for the comparison Data Source."
SUPPORTED_DATA_SOURCES = [
    SupportedDataSources.POSTGRESQL.value,
    SupportedDataSources.AURORA.value,
    SupportedDataSources.CITUS.value,
    SupportedDataSources.ALLOY.value,
    SupportedDataSources.NEON.value,
    SupportedDataSources.SNOWFLAKE.value,
    SupportedDataSources.DATABRICKS.value,
    SupportedDataSources.REDSHIFT.value,
    SupportedDataSources.SQLITE.value,
]
DATA_QUALITY_ISSUES = [DataQualityIssues.MULTI_SOURCE.value]


class ExpectQueryResultsToMatchComparison(BatchExpectation):
    __doc__ = f"""{EXPECTATION_SHORT_DESCRIPTION}

    ExpectQueryResultsToMatchComparison executes one SQL query for each of \
    two Data Sources and compares their results. It validates that the results from \
    the current Data Source's query matches those from the comparison Data Source's query, \
    above a specified threshold.

    Each record returned by the 'base_query' will be compared to each record \
    returned by the 'comparison_query'.

    The maximum number of records that will be returned for comparison from \
    each query is 200.

    The order of records returned does not matter unless \
    the number of records returned would be greater than 200.

    Column names do not matter, but the order of the columns does.

    Match percentage (100% - unexpected percent) is compared to the mostly threshold \
    to determine pass/fail.
        e.g.
    unexpected percent = 10%, mostly = 80%, (100% - 10%) > 80% - pass
    unexpected percent = 10%, mostly = 91%, (100% - 10%) < 91% - fail


    The match percentage is computed by dividing the number of matching records \
    by the maximum number of records in either the comparison result or the base result.
       e.g.
    Comparison Row Count: 100  Base Row Count: 100  Matches: 100  Match Percentage: 100%
    Comparison Row Count: 25   Base Row Count: 100  Matches: 25   Match Percentage: 25%
    Comparison Row Count: 100  Base Row Count: 25   Matches: 1    Match Percentage: 1%

    If both the base and comparison queries return 0 records, \
    it is considered a successful result.


    Args:
        base_query (str): {BASE_QUERY_DESCRIPTION}
        comparison_data_source_name (str): {COMPARISON_DATA_SOURCE_NAME_DESCRIPTION}
        comparison_query (str): {COMPARISON_QUERY_DESCRIPTION}
        mostly (float): {MOSTLY_DESCRIPTION}

    Other Parameters:
        severity (str or None): \
            {FAILURE_SEVERITY_DESCRIPTION} \
            For more detail, see [failure severity](https://docs.greatexpectations.io/docs/cloud/expectations/expectations_overview/#failure-severity).

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
    Data Quality Issues:
        {DATA_QUALITY_ISSUES[0]}
    """

    base_query: Union[str, SuiteParameterDict] = pydantic.Field(description=BASE_QUERY_DESCRIPTION)
    comparison_data_source_name: Union[str, SuiteParameterDict] = pydantic.Field(
        description=COMPARISON_DATA_SOURCE_NAME_DESCRIPTION
    )
    comparison_query: Union[str, SuiteParameterDict] = pydantic.Field(
        description=COMPARISON_QUERY_DESCRIPTION
    )
    mostly: MostlyField = 1

    metric_dependencies: ClassVar[Tuple[str, ...]] = (
        "base_query.table",
        "comparison_query.data_source_table",
    )
    success_keys: ClassVar[Tuple[str, ...]] = (
        "base_query",
        "comparison_data_source_name",
        "comparison_query",
        "mostly",
    )
    domain_keys: ClassVar[Tuple[str, ...]] = ("batch_id",)

    class Config:
        title = "Expect query results to match comparison"

        @staticmethod
        def schema_extra(
            schema: Dict[str, Any], model: Type[ExpectQueryResultsToMatchComparison]
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
        query_type: Literal["base", "comparison"],
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
        base_query_block = cls._get_query_rendered_content(
            query_type="base",
            add_param_args=(("base_query", RendererValueType.STRING),),
            template_str=None,  # `description` should override this
            renderer_configuration=RendererConfiguration(
                configuration=configuration,
                result=result,
                runtime_configuration=runtime_configuration,
            ),
        )
        comparison_query_block = cls._get_query_rendered_content(
            query_type="comparison",
            add_param_args=(
                ("comparison_data_source_name", RendererValueType.STRING),
                ("comparison_query", RendererValueType.STRING),
            ),
            template_str="Compare with Data Source $comparison_data_source_name",
            renderer_configuration=RendererConfiguration(
                configuration=configuration,
                result=result,
                runtime_configuration=runtime_configuration,
            ),
        )
        return [base_query_block, comparison_query_block]

    @override
    def _validate(
        self,
        metrics: dict,
        runtime_configuration: dict | None = None,
        execution_engine: ExecutionEngine | None = None,
    ) -> Union[ExpectationValidationResult, dict]:
        result_format_config: str | dict[str, Any] = self._get_result_format(
            runtime_configuration=runtime_configuration
        )
        # result_format can be a string or a dict with a "result_format" key
        if isinstance(result_format_config, dict):
            result_format = result_format_config.get("result_format", ResultFormat.SUMMARY)
        else:
            result_format = result_format_config

        missing_rows: list[dict[str, Any]]
        unexpected_rows: list[dict[str, Any]]

        base_results: list[dict[str, Any]] = metrics["base_query.table"]
        comparison_results: list[dict[str, Any]] = metrics["comparison_query.data_source_table"]
        base_result_count = len(base_results)
        comparison_result_count = len(comparison_results)

        if base_result_count + comparison_result_count == 0:
            unexpected_count = 0
            unexpected_percent = 0.0
            missing_rows = []
            unexpected_rows = []
        else:
            # creates a hashmap with row values as key and count of duplicate rows as value
            base_results_frequency_map = self._rows_to_frequency_map(base_results)
            comparison_results_frequency_map = self._rows_to_frequency_map(comparison_results)

            # Get the matches: if we see a value X times in comparison,
            # and Y times in base, min(X, Y)
            # is the number of matches.
            matching_counts = {
                k: min(
                    base_results_frequency_map.get(k, 0),
                    comparison_results_frequency_map.get(k, 0),
                )
                for k in comparison_results_frequency_map
            }
            match_count = sum(matching_counts.values())

            # see docstring for explanation of why we use max of comparison or base here
            unexpected_count = max(comparison_result_count, base_result_count) - match_count
            unexpected_percent = (
                1 - (match_count / max(comparison_result_count, base_result_count))
            ) * 100

            # NOTE: counter_a - counter_b reduces the numbers in counter_a to as low as 0,
            # but will not go negative
            missing_rows = self._compute_row_data(
                col_names=self._get_column_names_from_result(comparison_results),
                frequency_map=comparison_results_frequency_map - base_results_frequency_map,
            )
            unexpected_rows = self._compute_row_data(
                col_names=self._get_column_names_from_result(base_results),
                frequency_map=base_results_frequency_map - comparison_results_frequency_map,
            )

        success_kwargs = self._get_success_kwargs()
        mostly = success_kwargs.get("mostly", 1)
        success = (100 - unexpected_percent) >= (mostly * 100)

        if result_format == ResultFormat.BOOLEAN_ONLY:
            return {"success": success}
        elif result_format == ResultFormat.COMPLETE:
            return {
                "success": success,
                "result": {
                    "unexpected_count": unexpected_count,
                    "unexpected_percent": unexpected_percent,
                    "details": {
                        "missing_rows": missing_rows,
                        "unexpected_rows": unexpected_rows,
                    },
                },
            }
        else:
            # BASIC or SUMMARY - don't include details with row data
            return {
                "success": success,
                "result": {
                    "unexpected_count": unexpected_count,
                    "unexpected_percent": unexpected_percent,
                },
            }

    def _rows_to_frequency_map(self, rows: list[dict[str, Any]]) -> Counter[tuple]:
        try:
            return Counter(tuple(row.values()) for row in rows)
        except TypeError as e:
            if "unhashable type" in str(e):
                col_name = self._get_first_unhashable_column(rows)
                raise exceptions.UnhashableColumnError(col_name) from e
            else:
                raise e from e

    def _get_first_unhashable_column(self, rows: list[dict[str, Any]]) -> str:
        for row in rows:
            for col, value in row.items():
                try:
                    hash(value)
                except TypeError:
                    return col
        raise ValueError

    @override
    @classmethod
    @renderer(renderer_type=AtomicDiagnosticRendererType.OBSERVED_VALUE)
    def _atomic_diagnostic_observed_value(
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> list[RenderedAtomicContent] | RenderedAtomicContent:
        details = cls._get_details_from_results(result)
        if details is None:
            # Details are only available with COMPLETE result_format
            # For BASIC/SUMMARY, use unexpected_percent; for BOOLEAN_ONLY, use a fallback
            return cls._create_fallback_observed_value(
                configuration=configuration,
                result=result,
                runtime_configuration=runtime_configuration,
            )

        missing_rows: list[dict[str, Any]] = details["missing_rows"]
        unexpected_rows: list[dict[str, Any]] = details["unexpected_rows"]
        missing_rows_cols = cls._get_column_names_from_result(missing_rows)
        unexpected_rows_cols = cls._get_column_names_from_result(unexpected_rows)
        missing_rows_table = cls._create_observed_values_table(missing_rows)
        unexpected_rows_table = cls._create_observed_values_table(unexpected_rows)

        if len(missing_rows) == 0 and len(unexpected_rows) == 0:
            # For COMPLETE format with no differences, return empty list
            # (detailed observed value is not needed when everything matches)
            return []
        elif (
            len(missing_rows) == 1
            and len(unexpected_rows) == 1
            and len(missing_rows_cols) == 1
            and len(unexpected_rows_cols) == 1
        ):
            return cls._create_single_value(
                comparison_col_name=missing_rows_cols[0],
                base_col_name=unexpected_rows_cols[0],
                configuration=configuration,
                result=result,
                runtime_configuration=runtime_configuration,
            )
        elif len(missing_rows_cols) <= 1 and len(unexpected_rows_cols) <= 1:
            return cls._create_observed_values_set(
                comparison_col_name=missing_rows_cols[0] if missing_rows_cols else None,
                base_col_name=unexpected_rows_cols[0] if unexpected_rows_cols else None,
                configuration=configuration,
                result=result,
                runtime_configuration=runtime_configuration,
            )
        else:
            return [
                cls._create_table_rendered_atomic_content(
                    unexpected_rows_table,
                    label="Unexpected rows found in current table",
                ),
                cls._create_table_rendered_atomic_content(
                    missing_rows_table,
                    label="Expected rows not found in current table",
                ),
            ]

    @classmethod
    def _create_single_value(
        cls,
        comparison_col_name: str,
        base_col_name: str,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> list[RenderedAtomicContent]:
        result_details = cls._get_details_from_results(result)
        assert result_details is not None  # Caller guarantees details exist

        renderer_configuration_base: RendererConfiguration = RendererConfiguration(
            configuration=configuration,
            result=result,
            runtime_configuration=runtime_configuration,
        )
        base_value = result_details["unexpected_rows"][0][base_col_name]
        renderer_configuration_base.add_param(
            name="base_value",
            value=base_value,
        )
        renderer_configuration_base.template_str = "Observed value: $base_value"

        renderer_configuration_comparison: RendererConfiguration = RendererConfiguration(
            configuration=configuration,
            result=result,
            runtime_configuration=runtime_configuration,
        )
        comparison_value = result_details["missing_rows"][0][comparison_col_name]
        renderer_configuration_comparison.add_param(
            name="comparison_value",
            value=comparison_value,
        )
        renderer_configuration_comparison.template_str = "Expected value: $comparison_value"

        return [
            RenderedAtomicContent(
                name=AtomicDiagnosticRendererType.OBSERVED_VALUE,
                value=RenderedAtomicValue(
                    template=renderer_configuration_base.template_str,
                    params=renderer_configuration_base.params.dict(),
                    schema={"type": "com.superconductive.rendered.string"},
                ),
                value_type="StringValueType",
            ),
            RenderedAtomicContent(
                name=AtomicDiagnosticRendererType.OBSERVED_VALUE,
                value=RenderedAtomicValue(
                    template=renderer_configuration_comparison.template_str,
                    params=renderer_configuration_comparison.params.dict(),
                    schema={"type": "com.superconductive.rendered.string"},
                ),
                value_type="StringValueType",
            ),
        ]

    @classmethod
    def _create_observed_values_set(
        cls,
        comparison_col_name: Optional[str] = None,
        base_col_name: Optional[str] = None,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> RenderedAtomicContent:
        result_details = cls._get_details_from_results(result)
        assert result_details is not None  # Caller guarantees details exist
        comparison_values = (
            [
                row[comparison_col_name]
                for row in result_details["missing_rows"]
                if row[comparison_col_name] is not None
            ]
            if comparison_col_name
            else []
        )
        base_values = (
            [
                row[base_col_name]
                for row in result_details["unexpected_rows"]
                if row[base_col_name] is not None
            ]
            if base_col_name
            else []
        )
        renderer_configuration: RendererConfiguration = RendererConfiguration(
            configuration=configuration,
            result=result,
            runtime_configuration=runtime_configuration,
        )
        comparison_param_name = "expected_value"
        base_param_name = "observed_value"
        expected_param_prefix = "exp__"
        ov_param_prefix = "ov__"

        renderer_configuration.add_param(
            name=comparison_param_name,
            param_type=RendererValueType.ARRAY,
            value=comparison_values,
        )
        renderer_configuration = cls._add_array_params(
            array_param_name=comparison_param_name,
            param_prefix=expected_param_prefix,
            renderer_configuration=renderer_configuration,
        )

        renderer_configuration.add_param(
            name=base_param_name,
            param_type=RendererValueType.ARRAY,
            value=base_values,
        )
        renderer_configuration = cls._add_array_params(
            array_param_name=base_param_name,
            param_prefix=ov_param_prefix,
            renderer_configuration=renderer_configuration,
        )
        observed_value_set = set(base_values)
        sample_observed_value = next(iter(observed_value_set)) if observed_value_set else None
        expected_value_set = {
            parse_value_to_observed_type(observed_value=sample_observed_value, value=value)
            for value in comparison_values
        }

        observed_values = (
            (name, schema)
            for name, schema in renderer_configuration.params
            if name.startswith(ov_param_prefix)
        )

        expected_values = (
            (name, schema)
            for name, schema in renderer_configuration.params
            if name.startswith(expected_param_prefix)
        )

        template_str_list = []
        for name, schema in observed_values:
            render_state = (
                ObservedValueRenderState.EXPECTED.value
                if schema.value in expected_value_set
                else ObservedValueRenderState.UNEXPECTED.value
            )
            renderer_configuration.params.__dict__[name].render_state = render_state
            template_str_list.append(f"${name}")

        for name, schema in expected_values:
            coerced_value = parse_value_to_observed_type(
                observed_value=sample_observed_value,
                value=schema.value,
            )
            if coerced_value not in observed_value_set:
                renderer_configuration.params.__dict__[
                    name
                ].render_state = ObservedValueRenderState.MISSING.value
                template_str_list.append(f"${name}")

        renderer_configuration.template_str = " ".join(template_str_list)

        value_obj = RenderedAtomicValue(
            template=renderer_configuration.template_str,
            params=renderer_configuration.params.dict(),
            meta_notes=renderer_configuration.meta_notes,
            schema={"type": "com.superconductive.rendered.string"},
        )
        return RenderedAtomicContent(
            name=AtomicDiagnosticRendererType.OBSERVED_VALUE,
            value=value_obj,
            value_type="StringValueType",
        )

    @classmethod
    def _get_details_from_results(
        cls, result: Optional[ExpectationValidationResult]
    ) -> Optional[dict[str, Any]]:
        if not result or not result.result:
            return None
        details = result.result.get("details")
        if not isinstance(details, dict):
            # Details are only available with COMPLETE result_format
            return None
        return details

    @classmethod
    def _create_fallback_observed_value(
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> RenderedAtomicContent:
        """Create a fallback observed value for non-COMPLETE result formats.

        For BASIC/SUMMARY formats, displays the unexpected_percent.
        For BOOLEAN_ONLY or when no data is available, displays '--'.
        """
        renderer_configuration: RendererConfiguration = RendererConfiguration(
            configuration=configuration,
            result=result,
            runtime_configuration=runtime_configuration,
        )

        # Try to get unexpected_percent from result (available in BASIC/SUMMARY formats)
        unexpected_percent: Optional[float] = None
        if result and result.result:
            unexpected_percent = result.result.get("unexpected_percent")

        if unexpected_percent is not None:
            renderer_configuration.add_param(
                name="unexpected_percent",
                param_type=RendererValueType.NUMBER,
                value=unexpected_percent,
            )
            template_str = "$unexpected_percent% unexpected"
        else:
            # BOOLEAN_ONLY format or no data available
            renderer_configuration.add_param(
                name="observed_value",
                param_type=RendererValueType.STRING,
                value="--",
            )
            template_str = "$observed_value"

        return RenderedAtomicContent(
            name=AtomicDiagnosticRendererType.OBSERVED_VALUE,
            value=RenderedAtomicValue(
                template=template_str,
                params=renderer_configuration.params.dict(),
                meta_notes=renderer_configuration.meta_notes,
                schema={"type": "com.superconductive.rendered.string"},
            ),
            value_type="StringValueType",
        )

    @classmethod
    def _create_table_rendered_atomic_content(
        cls,
        table: list[list[RendererTableValue]],
        label: str,
    ) -> RenderedAtomicContent:
        rows = table[1:]
        template = f"{label}: $row_count"
        params = {
            "row_count": {
                "schema": RendererSchema(type=RendererValueType.NUMBER),
                "value": len(rows),
            }
        }

        if not table:
            return RenderedAtomicContent(
                name=AtomicDiagnosticRendererType.OBSERVED_VALUE,
                value=RenderedAtomicValue(
                    template=template,
                    params=params,
                ),
                value_type="TableType",
            )

        return RenderedAtomicContent(
            name=AtomicDiagnosticRendererType.OBSERVED_VALUE,
            value=RenderedAtomicValue(
                template=template,
                params=params,
                header_row=table[0],
                table=rows,
            ),
            value_type="TableType",
        )

    @classmethod
    def _create_observed_values_table(
        cls,
        rows: list[dict[str, Any]],
    ) -> list[list[RendererTableValue]]:
        if not rows:
            return []

        col_names = cls._get_column_names_from_result(rows)
        header_row = [
            RendererTableValue(
                schema=RendererSchema(type=RendererValueType.STRING),
                value=col_name,
            )
            for col_name in col_names
        ]
        output_rows: list[list[RendererTableValue]] = []
        for row in rows:
            output_row_values = []
            for col_name in col_names:
                col_value = row[col_name]
                output_row_values.append(
                    RendererTableValue(
                        schema=RendererSchema(
                            type=RendererValueType.from_value(col_value)
                            if col_value is not None
                            else RendererValueType.STRING
                        ),
                        value=col_value,
                    )
                )
            output_rows.append(output_row_values)

        return [header_row, *output_rows]

    @classmethod
    def _compute_row_data(
        cls,
        col_names: list[str],
        frequency_map: Counter[tuple],
    ) -> list[dict[str, Any]]:
        """Given a frequency map of values and a list of their keys, compute a list of
        column-name -> column value dictionaries.

        Example:
          - col_names: ["a", "b"]
          - frequency_map: Counter({
                (1, 2): 2,
                (3, 4): 1,
            })

          -> [
                {"a": 1, "b": 2},
                {"a": 1, "b": 2},
                {"a": 3, "b": 4},
             ]
        """
        # Convert the frequency map to an iterator of row values,
        # so we'll have multiple of anything that has a count > 1.
        # Then ensure we're sorted (deterministic output).
        # We define our own comparator for the sorting so that we can handle tuples
        # with None values, since e.g. `(1, None) < (1, 2)` fails with a TypeError.
        all_elements = frequency_map.elements()
        row_values = sorted(all_elements, key=cmp_to_key(cls._null_safe_tuple_compare))

        return [
            {col_names[i]: row_values[i] for i in range(len(col_names))}
            for row_values in row_values
        ]

    @classmethod
    def _get_column_names_from_result(
        cls,
        results_list: list[dict[str, Any]],
    ) -> list[str]:
        """Get the list of columns from a result list.

        NOTE: Order matters here, and we rely on python 3.7's deterministic ordering of results.
        """
        if results_list:
            return list(results_list[0].keys())
        else:
            return []

    @classmethod
    def _null_safe_tuple_compare(
        cls,
        a: tuple[Any, ...],
        b: tuple[Any, ...],
    ) -> int:
        """
        Compare two tuples, treating None as less than anything else.

        This satisfies the requirements of
        `sorted(<TUPLES>, key=cmp_to_key(cls._null_safe_tuple_compare))`.
        None is treated as less than anything else.
        """
        for x, y in zip(a, b, strict=False):
            if x == y:
                # elements match; go on to next element
                continue
            if x is None:
                return -1
            if y is None:
                return 1
            if x > y:
                return 1
            if x < y:
                return -1
        # If all items equal so far, compare by length
        return len(a) > len(b)
