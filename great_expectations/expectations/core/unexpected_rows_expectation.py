from __future__ import annotations

import logging
from string import Formatter
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Final, Iterable, Optional, Tuple, Type, Union

from great_expectations.compatibility import pydantic
from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.suite_parameters import (
    SuiteParameterDict,  # FIXME CoP
)
from great_expectations.exceptions.exceptions import (
    InvalidQueryError,
    MissingKeysError,
    ValidationError,
)
from great_expectations.expectations.expectation import (
    BatchExpectation,
    render_suite_parameter_string,
)
from great_expectations.expectations.metadata_types import DataQualityIssues, SupportedDataSources
from great_expectations.render import (
    AtomicDiagnosticRendererType,
    RenderedAtomicContent,
    renderedAtomicValueSchema,
)
from great_expectations.render.components import LegacyRendererType, RenderedStringTemplateContent
from great_expectations.render.renderer.renderer import renderer
from great_expectations.render.renderer_configuration import (
    CodeBlock,
    CodeBlockLanguage,
    RendererConfiguration,
    RendererValueType,
)
from great_expectations.render.util import substitute_none_for_missing

if TYPE_CHECKING:
    from great_expectations.core import ExpectationValidationResult
    from great_expectations.execution_engine import ExecutionEngine
    from great_expectations.expectations.expectation_configuration import ExpectationConfiguration


logger = logging.getLogger(__name__)


EXPECTATION_SHORT_DESCRIPTION: Final = (
    "This Expectation will fail validation if the query returns one or more rows. "
    "The WHERE clause defines the fail criteria. Supports template variables for column names."
)
UNEXPECTED_ROWS_QUERY_DESCRIPTION: Final = (
    "A SQL or Spark-SQL query to be executed for validation. Can use template variables like "
    "{column_name}."
)
TEMPLATE_DICT_DESCRIPTION: Final = (
    "Optional dictionary containing column names or other values as template variables for the SQL "
    "query."
)
SUPPORTED_DATA_SOURCES: Final = [
    SupportedDataSources.SPARK.value,
    SupportedDataSources.POSTGRESQL.value,
    SupportedDataSources.AURORA.value,
    SupportedDataSources.CITUS.value,
    SupportedDataSources.ALLOY.value,
    SupportedDataSources.NEON.value,
    SupportedDataSources.REDSHIFT.value,
    SupportedDataSources.MYSQL.value,
    SupportedDataSources.BIGQUERY.value,
    SupportedDataSources.SNOWFLAKE.value,
    SupportedDataSources.DATABRICKS.value,
]
DATA_QUALITY_ISSUES: Final = [DataQualityIssues.SQL.value]


class UnexpectedRowsExpectation(BatchExpectation):
    __doc__ = f"""{EXPECTATION_SHORT_DESCRIPTION}

    UnexpectedRowsExpectations facilitate the execution of SQL or Spark-SQL queries \
    as the core logic for an Expectation. UnexpectedRowsExpectations must implement \
    a `_validate(...)` method containing logic for determining whether data returned \
    by the executed query is successfully validated. One is written by default, but \
    can be overridden.

    A successful validation is one where the unexpected_rows_query returns no rows.

    This expectation now supports template variables in the query, allowing you to parameterize \
    column names and other values through the template_dict parameter.

    UnexpectedRowsExpectation is a \
    [Batch Expectation](https://docs.greatexpectations.io/docs/guides/expectations/creating_custom_expectations/how_to_create_custom_batch_expectations).

    BatchExpectations are one of the most common types of Expectation.
    They are evaluated for an entire Batch, and answer a semantic question about the Batch itself.

    Args:
        unexpected_rows_query (str): {UNEXPECTED_ROWS_QUERY_DESCRIPTION}
        template_dict (dict): {TEMPLATE_DICT_DESCRIPTION}

    Returns:
        An [ExpectationSuiteValidationResult](https://docs.greatexpectations.io/docs/terms/validation_result)

    Code Examples:
        Basic Usage (Column Value Check):
            ```python
            expectation = UnexpectedRowsExpectation(
                unexpected_rows_query=\"\"\"
                    SELECT *
                    FROM {{batch}}
                    WHERE {{column}} IS NULL
                \"\"\",
                template_dict={{"column": "user_id"}}
            )
            ```

        Multiple Column Check:
            ```python
            expectation = UnexpectedRowsExpectation(
                unexpected_rows_query=\"\"\"
                    SELECT *
                    FROM {{batch}}
                    WHERE {{column_a}} IS NOT NULL AND {{column_b}} IS NULL
                \"\"\",
                template_dict={{"column_a": "start_date", "column_b": "end_date"}}
            )
            ```

        Legacy Usage (Without Templates):
            ```python
            expectation = UnexpectedRowsExpectation(
                unexpected_rows_query=\"\"\"
                    SELECT *
                    FROM {{batch}}
                    WHERE status NOT IN ('active', 'inactive', 'pending')
                \"\"\"
            )
            ```

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
    Data Quality Issues:
        {DATA_QUALITY_ISSUES[0]}
    """

    unexpected_rows_query: Union[str, SuiteParameterDict] = pydantic.Field(
        description=UNEXPECTED_ROWS_QUERY_DESCRIPTION
    )
    template_dict: Optional[Dict[str, str]] = pydantic.Field(
        default=None, description=TEMPLATE_DICT_DESCRIPTION
    )

    metric_dependencies: ClassVar[Tuple[str, ...]] = (
        "unexpected_rows_query.table",
        "unexpected_rows_query.row_count",
    )
    success_keys: ClassVar[Tuple[str, ...]] = ("unexpected_rows_query", "template_dict")
    domain_keys: ClassVar[Tuple[str, ...]] = (
        "batch_id",
        "row_condition",
        "condition_parser",
    )
    args_keys: ClassVar[Tuple[str, ...]] = ("template_dict",)

    # Optional: Define required template keys for subclasses
    required_template_keys: ClassVar[Iterable[str]] = ()

    @pydantic.validator("unexpected_rows_query")
    def _validate_query(
        cls, query: Union[str, SuiteParameterDict]
    ) -> Union[str, SuiteParameterDict]:
        if isinstance(query, SuiteParameterDict):
            return query

        parsed_fields = [f[1] for f in Formatter().parse(query) if f[1]]
        if "batch" not in parsed_fields:
            batch_warning_message = (
                "unexpected_rows_query should contain the {batch} parameter. "
                "Otherwise data outside the configured batch will be queried."
            )
            # instead of raising a disruptive warning, we print and log info
            # to make the user aware of the potential for querying data
            # outside the configured batch
            print(batch_warning_message)
            logger.info(batch_warning_message)

        return query.rstrip("; \t\r\n\v\f")

    @pydantic.root_validator
    def _validate_template_requirements(cls, values):
        """Validate if template_dict contains the pre-defined required keys and additional
        validations."""
        if not cls.required_template_keys:
            return values

        template_dict = values.get("template_dict") or {}

        if missing_keys := set(cls.required_template_keys) - set(template_dict):
            raise MissingKeysError(missing_keys)

        additional_validations = cls.get_additional_template_validations(template_dict)
        for description, validation in additional_validations.items():
            if not validation:
                raise ValidationError(description)

        return values

    @classmethod
    def get_additional_template_validations(
        cls, template_dict: Dict[str, str] | None = None
    ) -> Dict[str, bool]:
        """Override this method to add custom validations for template_dict values.

        Args:
            template_dict: The template dictionary to validate

        Returns:
            Dict where keys are validation descriptions and values are boolean expressions
            that should evaluate to True for valid configurations.
        """
        return {}

    def _get_rendered_query(self, configuration: Optional[ExpectationConfiguration] = None) -> str:
        """Get the query with template variables replaced."""
        configuration = configuration or self.configuration
        query = configuration.kwargs.get("unexpected_rows_query")
        template_dict = configuration.kwargs.get("template_dict")

        if query is not None and template_dict is not None:
            # {batch} is a special placeholder that should not be replaced by the template_dict
            if "batch" not in template_dict:
                template_dict["batch"] = "{batch}"
            try:
                return query.format(**template_dict)
            except KeyError as err:
                raise InvalidQueryError from err

        return query

    class Config:
        title = "Custom Expectation with SQL"

        @staticmethod
        def schema_extra(schema: Dict[str, Any], model: Type[UnexpectedRowsExpectation]) -> None:
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
    @override
    def _prescriptive_template(
        cls,
        renderer_configuration: RendererConfiguration,
    ) -> RendererConfiguration:
        renderer_configuration.add_param(
            name="unexpected_rows_query", param_type=RendererValueType.STRING
        )
        renderer_configuration.add_param(name="template_dict", param_type=RendererValueType.OBJECT)
        renderer_configuration.code_block = CodeBlock(
            code_template_str="$unexpected_rows_query",
            language=CodeBlockLanguage.SQL,
        )
        return renderer_configuration

    @classmethod
    @renderer(renderer_type=LegacyRendererType.PRESCRIPTIVE)
    @render_suite_parameter_string
    @override
    def _prescriptive_renderer(
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
        **kwargs,
    ) -> list[RenderedStringTemplateContent]:
        runtime_configuration = runtime_configuration or {}
        styling = runtime_configuration.get("styling")
        params_to_substitute = ["unexpected_rows_query"]
        if configuration and configuration.kwargs.get("template_dict") is not None:
            params_to_substitute.append("template_dict")
        params = substitute_none_for_missing(
            configuration.kwargs,  # type: ignore[union-attr] # FIXME CoP
            params_to_substitute,
        )

        template_str = "Unexpected rows query: $unexpected_rows_query"

        # Add template dict info if present
        if params.get("template_dict"):
            template_variables = ", ".join(f"{k}: {v}" for k, v in params["template_dict"].items())
            template_str += f"\nWith template variables: {template_variables}"

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

        unexpected_row_count = (
            result.get("result").get("observed_value") if result is not None else None
        )

        template_str = ""
        if isinstance(unexpected_row_count, (int, float)):
            renderer_configuration.add_param(
                name="observed_value",
                param_type=RendererValueType.NUMBER,
                value=unexpected_row_count,
            )

            template_str = "$observed_value unexpected row"
            if unexpected_row_count != 1:
                template_str += "s"

        renderer_configuration.template_str = template_str

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

    @override
    def _validate(
        self,
        metrics: dict,
        runtime_configuration: dict | None = None,
        execution_engine: ExecutionEngine | None = None,
    ) -> Union[ExpectationValidationResult, dict]:
        metric_value = metrics["unexpected_rows_query.table"]
        unexpected_row_count = metrics["unexpected_rows_query.row_count"]
        return {
            "success": unexpected_row_count == 0,
            "result": {
                "observed_value": unexpected_row_count,
                "details": {"unexpected_rows": metric_value},
            },
        }
