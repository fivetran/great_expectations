from __future__ import annotations

from typing import Any, Callable

import pyparsing

# Import classes and functions that may have different names in different versions
try:
    from pyparsing import DelimitedList
except ImportError:
    # Backward compatibility for older pyparsing versions (e.g., 3.0.9 used by Airflow 2.5.0)
    from pyparsing import (
        delimitedList as DelimitedList,
    )

try:
    from pyparsing import dict_of
except ImportError:
    # Backward compatibility for older pyparsing versions (e.g., 3.0.9 used by Airflow 2.5.0)
    from pyparsing import (
        dictOf as dict_of,
    )

# Re-export commonly used pyparsing classes and functions
from pyparsing import (
    CaselessKeyword,
    CaselessLiteral,
    Combine,
    Forward,
    Group,
    Literal,
    ParseException,
    ParseResults,
    QuotedString,
    Regex,
    Suppress,
    Word,
    alphanums,
    alphas,
    alphas8bit,
    hexnums,
)

# Re-export pyparsing module itself for cases where the full module is needed
__all__ = [
    "CaselessKeyword",
    "CaselessLiteral",
    "Combine",
    "DelimitedList",
    "Forward",
    "Group",
    "Literal",
    "ParseException",
    "ParseResults",
    "QuotedString",
    "Regex",
    "Suppress",
    "Word",
    "alphanums",
    "alphas",
    "alphas8bit",
    "dict_of",
    "hexnums",
    "parse_string",
    "pyparsing",
    "set_parse_action",
    "set_results_name",
]


def set_parse_action(parser: Any, action: Callable) -> Any:
    """Compatibility wrapper for set_parse_action/setParseAction.

    Args:
        parser: The pyparsing parser object
        action: The parse action function to apply

    Returns:
        The parser object with the parse action set (for chaining)
    """
    try:
        return parser.set_parse_action(action)
    except AttributeError:
        return parser.setParseAction(action)


def set_results_name(parser: Any, name: str) -> Any:
    """Compatibility wrapper for set_results_name/setResultsName.

    Args:
        parser: The pyparsing parser object
        name: The name to assign to the parsed results

    Returns:
        The parser object with the results name set (for chaining)
    """
    try:
        return parser.set_results_name(name)
    except AttributeError:
        return parser.setResultsName(name)


def parse_string(parser: Any, string: str, parse_all: bool = False) -> Any:
    """Compatibility wrapper for parse_string/parseString.

    Args:
        parser: The pyparsing parser object
        string: The string to parse
        parse_all: Whether to require parsing the entire string

    Returns:
        The parse results
    """
    try:
        return parser.parse_string(string, parse_all=parse_all)
    except AttributeError:
        return parser.parseString(string, parseAll=parse_all)
