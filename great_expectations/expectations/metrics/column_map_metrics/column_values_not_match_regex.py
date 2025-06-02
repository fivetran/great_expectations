from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Optional

from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.metric_function_types import (
    SummarizationMetricNameSuffixes,
)
from great_expectations.execution_engine import (
    PandasExecutionEngine,
    SparkDFExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.map_metric_provider import (
    ColumnMapMetricProvider,
    column_condition_partial,
)
from great_expectations.expectations.metrics.metric_provider import (
    MetricProvider,
    metric_value,
)
from great_expectations.expectations.metrics.util import get_dialect_regex_expression
from great_expectations.validator.metric_configuration import MetricConfiguration

if TYPE_CHECKING:
    from great_expectations.execution_engine import ExecutionEngine
    from great_expectations.expectations.expectation_configuration import (
        ExpectationConfiguration,
    )

logger = logging.getLogger(__name__)


def regex_to_like(regex):
    """
    Convert regex patterns to SQL LIKE patterns for MSSQL compatibility.
    Returns None if the pattern is too complex for LIKE conversion.
    """
    # Handle exact pattern mappings first (most common cases)
    pattern_mappings = {
        # Character class patterns
        '^[a-zA-Z].*': '[a-zA-Z]%',           # Starts with letter
        '^[A-Z].*': '[A-Z]%',                 # Starts with uppercase
        '^[a-z].*': '[a-z]%',                 # Starts with lowercase
        '^[0-9].*': '[0-9]%',                 # Starts with digit
        '.*[a-zA-Z]$': '%[a-zA-Z]',           # Ends with letter
        '.*[0-9]$': '%[0-9]',                 # Ends with digit
        
        # Email patterns
        '.*@.*': '%@%',                       # Contains @
        '.*@.*\\..*': '%@%.%',                # Basic email pattern
        
        # Common word patterns
        '^[A-Z][a-z]*': '[A-Z][a-z]%',       # Capitalized word
        
        # Whitespace patterns
        '.*\\s.*': '% %',                     # Contains whitespace
        '^\\s.*': ' %',                       # Starts with whitespace
        '.*\\s$': '% ',                       # Ends with whitespace
    }
    
    if regex in pattern_mappings:
        return pattern_mappings[regex]
    
    # Store original for error messages
    original_regex = regex
    
    # Check for unsupported complex patterns first
    unsupported_patterns = [
        r'\\d\{(\d+),(\d+)\}',               # Range quantifiers {2,4}
        r'[\+\*\?]\{',                       # Complex quantifiers
        r'\(\?\:',                           # Non-capturing groups
        r'\(\?\=',                           # Positive lookahead
        r'\(\?\!',                           # Negative lookahead
        r'\(\?\<\=',                         # Positive lookbehind
        r'\(\?\<\!',                         # Negative lookbehind
        r'\|',                               # Alternation
        r'\\[bBAZ]',                         # Word boundaries
    ]
    
    for pattern in unsupported_patterns:
        if re.search(pattern, regex):
            return None
    
    # Start conversion process
    like = regex
    
    # Handle anchors - remove them as LIKE is implicit anchoring
    if like.startswith('^'):
        like = like[1:]
    if like.endswith('$'):
        like = like[:-1]
    
    # Handle escaped characters (preserve literal meaning)
    like = like.replace(r'\.', '<!LITERAL_DOT!>')
    like = like.replace(r'\-', '<!LITERAL_DASH!>')
    like = like.replace(r'\_', '<!LITERAL_UNDERSCORE!>')
    like = like.replace(r'\%', '<!LITERAL_PERCENT!>')
    like = like.replace(r'\\', '<!LITERAL_BACKSLASH!>')
    
    # Convert quantified digit patterns
    like = re.sub(r'\\d\{(\d+)\}', lambda m: '_' * int(m.group(1)), like)
    
    # Convert character classes to LIKE equivalents
    like = like.replace(r'\d', '_')           # Any digit
    like = like.replace(r'\w', '_')           # Any word character (approx)
    like = like.replace(r'\s', ' ')           # Whitespace (space)
    
    # Convert wildcard patterns
    like = like.replace('.*', '%')            # Zero or more of any char
    like = like.replace('.+', '_%')           # One or more of any char
    like = like.replace('.', '_')             # Any single character
    
    # Handle simple character sets [abc] -> _ (approximation)
    like = re.sub(r'\[([^\]]+)\]', r'[\1]', like)
    
    # Handle negated character sets [^abc] -> _ (approximation)
    like = re.sub(r'\[\^([^\]]+)\]', '_', like)
    
    # Convert common quantifiers (simple cases only)
    like = re.sub(r'(.)\+', r'\1%', like)     # One or more -> char%
    like = re.sub(r'(.)\*', r'%', like)       # Zero or more -> %
    like = re.sub(r'(.)\?', r'\1', like)      # Optional -> just the char
    
    # Restore escaped characters
    like = like.replace('<!LITERAL_DOT!>', '.')
    like = like.replace('<!LITERAL_DASH!>', '-')
    like = like.replace('<!LITERAL_UNDERSCORE!>', '[_]')  # Escape underscore in LIKE
    like = like.replace('<!LITERAL_PERCENT!>', '[%]')     # Escape percent in LIKE
    like = like.replace('<!LITERAL_BACKSLASH!>', '\\')
    
    # Final validation - check for remaining regex syntax that can't be converted
    remaining_regex_chars = [
        r'\(',                               # Grouping
        r'\)',
        r'\{[^}]*\}',                       # Remaining quantifiers
        r'\\[^dws]',                        # Other escape sequences
    ]
    
    for pattern in remaining_regex_chars:
        if re.search(pattern, like):
            return None
    
    # Additional validation - ensure result makes sense
    if len(like) == 0:
        return None
    
    # Clean up any double wildcards
    like = re.sub(r'%+', '%', like)          # Multiple % -> single %
    
    return like


class ColumnValuesNotMatchRegex(ColumnMapMetricProvider):
    condition_metric_name = "column_values.not_match_regex"
    condition_value_keys = ("regex",)

    @column_condition_partial(engine=PandasExecutionEngine)
    def _pandas(cls, column, regex, **kwargs):
        return ~column.astype(str).str.contains(regex)

    @column_condition_partial(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(cls, column, regex, _dialect, **kwargs):
        # Handle MSSQL specially
        # if _dialect.dialect.name.lower() == "mssql":
        #     like_pattern = regex_to_like(regex)
        #     if like_pattern is not None:
        #         return ~column.like(like_pattern)  # NOT LIKE
        #     else:
        #         raise NotImplementedError(f"Regex pattern '{regex}' too complex for MSSQL")
        
        # Original logic for other dialects
        regex_expression = get_dialect_regex_expression(column, regex, _dialect, positive=False)
        if regex_expression is None:
            logger.warning(f"Regex is not supported for dialect {_dialect!s}")
            raise NotImplementedError

        return regex_expression


    @column_condition_partial(engine=SparkDFExecutionEngine)
    def _spark(cls, column, regex, **kwargs):
        return ~column.rlike(regex)


class ColumnValuesNotMatchRegexCount(MetricProvider):
    metric_name = "column_values.not_match_regex.count"

    metric_value_kwargs = ("regex",)

    @metric_value(engine=PandasExecutionEngine)
    def _pandas(*, metrics, **kwargs):
        return metrics[
            f"column_values.match_regex.{SummarizationMetricNameSuffixes.UNEXPECTED_COUNT.value}"
        ]

    @metric_value(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(*, metrics, **kwargs):
        return metrics[
            f"column_values.match_regex.{SummarizationMetricNameSuffixes.UNEXPECTED_COUNT.value}"
        ]

    @metric_value(engine=SparkDFExecutionEngine)
    def _spark(*, metrics, **kwargs):
        return metrics[
            f"column_values.match_regex.{SummarizationMetricNameSuffixes.UNEXPECTED_COUNT.value}"
        ]

    @classmethod
    @override
    def _get_evaluation_dependencies(
        cls,
        metric: MetricConfiguration,
        configuration: Optional[ExpectationConfiguration] = None,
        execution_engine: Optional[ExecutionEngine] = None,
        runtime_configuration: Optional[dict] = None,
    ):
        dependencies: dict = super()._get_evaluation_dependencies(
            metric=metric,
            configuration=configuration,
            execution_engine=execution_engine,
            runtime_configuration=runtime_configuration,
        )
        dependencies[
            f"column_values.match_regex.{SummarizationMetricNameSuffixes.UNEXPECTED_COUNT.value}"
        ] = MetricConfiguration(
            metric_name=f"column_values.match_regex.{SummarizationMetricNameSuffixes.UNEXPECTED_COUNT.value}",
            metric_domain_kwargs=metric.metric_domain_kwargs,
            metric_value_kwargs=metric.metric_value_kwargs,
        )
        return dependencies
