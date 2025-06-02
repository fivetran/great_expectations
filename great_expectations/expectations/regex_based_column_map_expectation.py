from __future__ import annotations

import logging
import re
from abc import ABC
from typing import TYPE_CHECKING, Optional

from great_expectations.compatibility.typing_extensions import override
from great_expectations.exceptions.exceptions import (
    InvalidExpectationConfigurationError,
)
from great_expectations.execution_engine import (
    PandasExecutionEngine,
    SparkDFExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.expectation import (
    ColumnMapExpectation,
    render_suite_parameter_string,
)
from great_expectations.expectations.metrics.map_metric_provider import (
    ColumnMapMetricProvider,
    column_condition_partial,
)
from great_expectations.expectations.metrics.util import get_dialect_regex_expression
from great_expectations.render import LegacyRendererType, RenderedStringTemplateContent
from great_expectations.render.renderer.renderer import renderer
from great_expectations.render.renderer_configuration import (
    RendererConfiguration,
    RendererValueType,
)
from great_expectations.render.util import (
    num_to_str,
    parse_row_condition_string_pandas_engine,
    substitute_none_for_missing,
)
from great_expectations.util import camel_to_snake

if TYPE_CHECKING:
    from great_expectations.core import (
        ExpectationValidationResult,
    )
    from great_expectations.expectations.expectation_configuration import (
        ExpectationConfiguration,
    )
    from great_expectations.render.renderer_configuration import AddParamArgs

logger = logging.getLogger(__name__)


def regex_to_like(regex):
    """
    Convert regex patterns to SQL LIKE patterns for MSSQL compatibility.
    Returns None if the pattern is too complex for LIKE conversion.
    """
    # Handle exact pattern mappings first (most common cases)
    pattern_mappings = {
        # Character class patterns
        "^[a-zA-Z].*": "[a-zA-Z]%",  # Starts with letter
        "^[A-Z].*": "[A-Z]%",  # Starts with uppercase
        "^[a-z].*": "[a-z]%",  # Starts with lowercase
        "^[0-9].*": "[0-9]%",  # Starts with digit
        ".*[a-zA-Z]$": "%[a-zA-Z]",  # Ends with letter
        ".*[0-9]$": "%[0-9]",  # Ends with digit
        # Email patterns
        ".*@.*": "%@%",  # Contains @
        ".*@.*\\..*": "%@%.%",  # Basic email pattern
        # Common word patterns
        "^[A-Z][a-z]*": "[A-Z][a-z]%",  # Capitalized word
        # Whitespace patterns
        ".*\\s.*": "% %",  # Contains whitespace
        "^\\s.*": " %",  # Starts with whitespace
        ".*\\s$": "% ",  # Ends with whitespace
    }

    if regex in pattern_mappings:
        return pattern_mappings[regex]

    # Store original for error messages
    original_regex = regex

    # Check for unsupported complex patterns first
    unsupported_patterns = [
        r"\\d\{(\d+),(\d+)\}",  # Range quantifiers {2,4}
        r"[\+\*\?]\{",  # Complex quantifiers
        r"\(\?\:",  # Non-capturing groups
        r"\(\?\=",  # Positive lookahead
        r"\(\?\!",  # Negative lookahead
        r"\(\?\<\=",  # Positive lookbehind
        r"\(\?\<\!",  # Negative lookbehind
        r"\|",  # Alternation
        r"\\[bBAZ]",  # Word boundaries
    ]

    for pattern in unsupported_patterns:
        if re.search(pattern, regex):
            return None

    # Start conversion process
    like = regex

    # Handle anchors - remove them as LIKE is implicit anchoring
    if like.startswith("^"):
        like = like[1:]
    if like.endswith("$"):
        like = like[:-1]

    # Handle escaped characters (preserve literal meaning)
    like = like.replace(r"\.", "<!LITERAL_DOT!>")
    like = like.replace(r"\-", "<!LITERAL_DASH!>")
    like = like.replace(r"\_", "<!LITERAL_UNDERSCORE!>")
    like = like.replace(r"\%", "<!LITERAL_PERCENT!>")
    like = like.replace(r"\\", "<!LITERAL_BACKSLASH!>")

    # Convert quantified digit patterns
    like = re.sub(r"\\d\{(\d+)\}", lambda m: "_" * int(m.group(1)), like)

    # Convert character classes to LIKE equivalents
    like = like.replace(r"\d", "_")  # Any digit
    like = like.replace(r"\w", "_")  # Any word character (approx)
    like = like.replace(r"\s", " ")  # Whitespace (space)

    # Convert wildcard patterns
    like = like.replace(".*", "%")  # Zero or more of any char
    like = like.replace(".+", "_%")  # One or more of any char
    like = like.replace(".", "_")  # Any single character

    # Handle simple character sets [abc] -> _ (approximation)
    like = re.sub(r"\[([^\]]+)\]", r"[\1]", like)

    # Handle negated character sets [^abc] -> _ (approximation)
    like = re.sub(r"\[\^([^\]]+)\]", "_", like)

    # Convert common quantifiers (simple cases only)
    like = re.sub(r"(.)\+", r"\1%", like)  # One or more -> char%
    like = re.sub(r"(.)\*", r"%", like)  # Zero or more -> %
    like = re.sub(r"(.)\?", r"\1", like)  # Optional -> just the char

    # Restore escaped characters
    like = like.replace("<!LITERAL_DOT!>", ".")
    like = like.replace("<!LITERAL_DASH!>", "-")
    like = like.replace("<!LITERAL_UNDERSCORE!>", "[_]")  # Escape underscore in LIKE
    like = like.replace("<!LITERAL_PERCENT!>", "[%]")  # Escape percent in LIKE
    like = like.replace("<!LITERAL_BACKSLASH!>", "\\")

    # Final validation - check for remaining regex syntax that can't be converted
    remaining_regex_chars = [
        r"\(",  # Grouping
        r"\)",
        r"\{[^}]*\}",  # Remaining quantifiers
        r"\\[^dws]",  # Other escape sequences
    ]

    for pattern in remaining_regex_chars:
        if re.search(pattern, like):
            return None

    # Additional validation - ensure result makes sense
    if len(like) == 0:
        return None

    # Clean up any double wildcards
    like = re.sub(r"%+", "%", like)  # Multiple % -> single %

    return like


class RegexColumnMapMetricProvider(ColumnMapMetricProvider):
    """Base class for all RegexColumnMapMetrics.

    RegexColumnMapMetric classes inheriting from RegexColumnMapMetricProvider are ephemeral,
    defined by their `regex` attribute, and registered during the execution of their associated RegexColumnMapExpectation.

    Metric Registration Example:

    ```python
    map_metric = RegexBasedColumnMapExpectation.register_metric(
        regex_camel_name='Vowel',
        regex_='^[aeiouyAEIOUY]*$',
    )
    ```

    In some cases, subclasses of MetricProvider, such as RegexColumnMapMetricProvider, will already
    have correct values that may simply be inherited by Metric classes.

    Args:
        regex (str): A valid regex pattern.
        metric_name (str): The name of the registered metric. Must be globally unique in a great_expectations installation.
            Constructed by the `register_metric(...)` function during Expectation execution.
        domain_keys (tuple): A tuple of the keys used to determine the domain of the metric.
        condition_value_keys (tuple): A tuple of the keys used to determine the value of the metric.

    ---Documentation---
        - https://docs.greatexpectations.io/docs/guides/expectations/creating_custom_expectations/how_to_create_custom_regex_based_column_map_expectations
    """  # noqa: E501 # FIXME CoP

    condition_value_keys = ()

    @column_condition_partial(engine=PandasExecutionEngine)
    def _pandas(cls, column, **kwargs):
        return column.astype(str).str.contains(cls.regex)

    @column_condition_partial(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(cls, column, _dialect, **kwargs):
        if _dialect.dialect.name.lower() == "mssql":
            like_pattern = regex_to_like(cls.regex)  # Use cls.regex, not regex parameter
            if like_pattern is not None:
                return column.like(like_pattern)
            else:
                raise NotImplementedError(f"Regex pattern '{cls.regex}' too complex for MSSQL")

        regex_expression = get_dialect_regex_expression(
            column, cls.regex, _dialect
        )  # Use cls.regex
        if regex_expression is None:
            logger.warning(f"Regex is not supported for dialect {_dialect.dialect.name!s}")
            raise NotImplementedError
        return regex_expression

    @column_condition_partial(engine=SparkDFExecutionEngine)
    def _spark(cls, column, **kwargs):
        return column.rlike(cls.regex)


class RegexBasedColumnMapExpectation(ColumnMapExpectation, ABC):
    """Base class for RegexBasedColumnMapExpectations.

    RegexBasedColumnMapExpectations facilitate regex parsing as the core logic for a Map Expectation.

    Example Definition:

    ```python
    ExpectColumnValuesToOnlyContainVowels(SetBasedColumnMapExpectation):
        regex_camel_name = 'Vowel'
        regex = '^[aeiouyAEIOUY]*$'
        semantic_type_name_plural = 'vowels'
        map_metric = RegexBasedColumnMapExpectation.register_metric(
            regex_camel_name=regex_camel_name,
            regex=regex
    )
    ```

    Args:
        regex_camel_name (str): A name describing a regex pattern, in camel case.
        regex_ (str): A valid regex pattern.
        semantic_type_name_plural (optional[str]): The plural form of a semantic type being validated by a regex pattern.
        map_metric (str): The name of an ephemeral metric, as returned by `register_metric(...)`.
    """  # noqa: E501 # FIXME CoP

    @staticmethod
    def register_metric(
        regex_camel_name: str,
        regex_: str,
    ) -> str:
        """Register an ephemeral metric using a constructed name with the logic provided by RegexColumnMapMetricProvider.

        Args:
            regex_camel_name: A name describing a regex pattern, in camel case.
            regex_: A valid regex pattern.

        Returns:
            map_metric: The constructed name of the ephemeral metric.
        """  # noqa: E501 # FIXME CoP
        regex_snake_name: str = camel_to_snake(regex_camel_name)
        map_metric: str = "column_values.match_" + regex_snake_name + "_regex"

        # Define the class using `type`. This allows us to name it dynamically.
        new_column_regex_metric_provider = type(  # noqa: F841 # never used
            f"(ColumnValuesMatch{regex_camel_name}Regex",
            (RegexColumnMapMetricProvider,),
            {
                "condition_metric_name": map_metric,
                "regex": regex_,
            },
        )

        return map_metric

    @override
    def validate_configuration(
        self, configuration: Optional[ExpectationConfiguration] = None
    ) -> None:
        """Raise an exception if the configuration is not viable for an expectation.

        Args:
            configuration: An ExpectationConfiguration

        Raises:
            InvalidExpectationConfigurationError: If no `regex` or `column` specified, or if `mostly` parameter
                incorrectly defined.
        """  # noqa: E501 # FIXME CoP
        super().validate_configuration(configuration)
        try:
            assert getattr(self, "regex", None) is not None, (
                "regex is required for RegexBasedColumnMap Expectations"
            )
            assert (
                "column" in configuration.kwargs  # type: ignore[union-attr] # This method is being removed
            ), "'column' parameter is required for column map expectations"
            if "mostly" in configuration.kwargs:  # type: ignore[union-attr] # This method is being removed
                mostly = configuration.kwargs["mostly"]  # type: ignore[union-attr] # This method is being removed
                assert isinstance(mostly, (int, float)), (
                    "'mostly' parameter must be an integer or float"
                )
                assert 0 <= mostly <= 1, "'mostly' parameter must be between 0 and 1"
        except AssertionError as e:
            raise InvalidExpectationConfigurationError(str(e))

    # question, descriptive, prescriptive, diagnostic
    @classmethod
    @renderer(renderer_type=LegacyRendererType.QUESTION)
    def _question_renderer(cls, configuration, result=None, runtime_configuration=None):
        column = configuration.kwargs.get("column")
        mostly = configuration.kwargs.get("mostly")
        regex = getattr(cls, "regex", None)
        semantic_type_name_plural = getattr(cls, "semantic_type_name_plural", None)

        if mostly == 1 or mostly is None:
            if semantic_type_name_plural is not None:
                return f'Are all values in column "{column}" valid {semantic_type_name_plural}, as judged by matching the regular expression {regex}?'  # noqa: E501 # FIXME CoP
            else:
                return f'Do all values in column "{column}" match the regular expression {regex}?'
        else:  # noqa: PLR5501 # FIXME CoP
            if semantic_type_name_plural is not None:
                return f'Are at least {mostly * 100}% of values in column "{column}" valid {semantic_type_name_plural}, as judged by matching the regular expression {regex}?'  # noqa: E501 # FIXME CoP
            else:
                return f'Do at least {mostly * 100}% of values in column "{column}" match the regular expression {regex}?'  # noqa: E501 # FIXME CoP

    @classmethod
    @renderer(renderer_type=LegacyRendererType.ANSWER)
    def _answer_renderer(cls, configuration=None, result=None, runtime_configuration=None):
        column = result.expectation_config.kwargs.get("column")
        mostly = result.expectation_config.kwargs.get("mostly")
        regex = result.expectation_config.kwargs.get("regex")
        semantic_type_name_plural = configuration.kwargs.get("semantic_type_name_plural")

        if result.success:
            if mostly == 1 or mostly is None:
                if semantic_type_name_plural is not None:
                    return f'All values in column "{column}" are valid {semantic_type_name_plural}, as judged by matching the regular expression {regex}.'  # noqa: E501 # FIXME CoP
                else:
                    return f'All values in column "{column}" match the regular expression {regex}.'
            else:  # noqa: PLR5501 # FIXME CoP
                if semantic_type_name_plural is not None:
                    return f'At least {mostly * 100}% of values in column "{column}" are valid {semantic_type_name_plural}, as judged by matching the regular expression {regex}.'  # noqa: E501 # FIXME CoP
                else:
                    return f'At least {mostly * 100}% of values in column "{column}" match the regular expression {regex}.'  # noqa: E501 # FIXME CoP
        else:  # noqa: PLR5501 # FIXME CoP
            if semantic_type_name_plural is not None:
                return f' Less than {mostly * 100}% of values in column "{column}" are valid {semantic_type_name_plural}, as judged by matching the regular expression {regex}.'  # noqa: E501 # FIXME CoP
            else:
                return f'Less than {mostly * 100}% of values in column "{column}" match the regular expression {regex}.'  # noqa: E501 # FIXME CoP

    @override
    @classmethod
    def _prescriptive_template(
        cls,
        renderer_configuration: RendererConfiguration,
    ):
        add_param_args: AddParamArgs = (
            ("column", RendererValueType.STRING),
            ("mostly", RendererValueType.NUMBER),
            ("regex", RendererValueType.STRING),
        )
        for name, param_type in add_param_args:
            renderer_configuration.add_param(name=name, param_type=param_type)

        params = renderer_configuration.params

        if not params.regex:
            template_str = "values must match a regular expression but none was specified."
        else:
            template_str = "values must match this regular expression: $regex"

            if params.mostly and params.mostly.value < 1.0:
                renderer_configuration = cls._add_mostly_pct_param(
                    renderer_configuration=renderer_configuration
                )
                template_str += ", at least $mostly_pct % of the time."
            else:
                template_str += "."

        if renderer_configuration.include_column_name:
            template_str = "$column " + template_str

        renderer_configuration.template_str = template_str

        return renderer_configuration

    @override
    @classmethod
    @renderer(renderer_type=LegacyRendererType.PRESCRIPTIVE)
    @render_suite_parameter_string
    def _prescriptive_renderer(
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
        **kwargs,
    ):
        runtime_configuration = runtime_configuration or {}
        include_column_name = runtime_configuration.get("include_column_name") is not False
        styling = runtime_configuration.get("styling")
        kwargs = configuration.kwargs if configuration else {}
        params = substitute_none_for_missing(
            kwargs,
            ["column", "regex", "mostly", "row_condition", "condition_parser"],
        )

        if not params.get("regex"):
            template_str = "values must match a regular expression but none was specified."
        else:
            template_str = "values must match this regular expression: $regex"
            if params["mostly"] is not None:
                params["mostly_pct"] = num_to_str(params["mostly"] * 100, no_scientific=True)
                # params["mostly_pct"] = "{:.14f}".format(params["mostly"]*100).rstrip("0").rstrip(".")  # noqa: E501 # FIXME CoP
                template_str += ", at least $mostly_pct % of the time."
            else:
                template_str += "."

        if include_column_name:
            template_str = "$column " + template_str

        if params["row_condition"] is not None:
            (
                conditional_template_str,
                conditional_params,
            ) = parse_row_condition_string_pandas_engine(params["row_condition"])
            template_str = conditional_template_str + ", then " + template_str
            params.update(conditional_params)

        params_with_json_schema = {  # noqa: F841 # never used
            "column": {"schema": {"type": "string"}, "value": params.get("column")},
            "mostly": {"schema": {"type": "number"}, "value": params.get("mostly")},
            "mostly_pct": {
                "schema": {"type": "number"},
                "value": params.get("mostly_pct"),
            },
            "regex": {"schema": {"type": "string"}, "value": params.get("regex")},
            "row_condition": {
                "schema": {"type": "string"},
                "value": params.get("row_condition"),
            },
            "condition_parser": {
                "schema": {"type": "string"},
                "value": params.get("condition_parser"),
            },
        }

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
