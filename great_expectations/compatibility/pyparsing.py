from __future__ import annotations

from typing import Any, Callable

try:
    from pyparsing import DelimitedList, dict_of

    _USE_NEW_PYPARSING_API = True
except ImportError:
    # Backward compatibility for older pyparsing versions (e.g., 3.0.9 used by Airflow 2.5.0)
    from pyparsing import delimitedList as DelimitedList
    from pyparsing import dictOf as dict_of

    _USE_NEW_PYPARSING_API = False

# Re-export for convenience
__all__ = ["DelimitedList", "dict_of", "parse_string", "set_parse_action", "set_results_name"]


def set_parse_action(parser: Any, action: Callable) -> Any:
    """Compatibility wrapper for set_parse_action/setParseAction.

    Args:
        parser: The pyparsing parser object
        action: The parse action function to apply

    Returns:
        The parser object with the parse action set (for chaining)
    """
    if _USE_NEW_PYPARSING_API:
        return parser.set_parse_action(action)
    return parser.setParseAction(action)


def set_results_name(parser: Any, name: str) -> Any:
    """Compatibility wrapper for set_results_name/setResultsName.

    Args:
        parser: The pyparsing parser object
        name: The name to assign to the parsed results

    Returns:
        The parser object with the results name set (for chaining)
    """
    if _USE_NEW_PYPARSING_API:
        return parser.set_results_name(name)
    return parser.setResultsName(name)


def parse_string(parser: Any, string: str, parse_all: bool = True) -> Any:
    """Compatibility wrapper for parse_string/parseString.

    Args:
        parser: The pyparsing parser object
        string: The string to parse
        parse_all: Whether to require parsing the entire string

    Returns:
        The parse results
    """
    if _USE_NEW_PYPARSING_API:
        return parser.parse_string(string, parse_all=parse_all)
    return parser.parseString(string, parseAll=parse_all)
