from __future__ import annotations

from typing import Any, Callable

import pyparsing

try:
    from pyparsing import DelimitedList
except ImportError:
    # Backward compatibility for older pyparsing versions (e.g., 3.0.9 used by Airflow 2.5.0)
    from pyparsing import (
        delimitedList as DelimitedList,  # noqa: F401  # import used externally via compatibility import
    )

try:
    from pyparsing import dict_of
except ImportError:
    # Backward compatibility for older pyparsing versions (e.g., 3.0.9 used by Airflow 2.5.0)
    from pyparsing import (
        dictOf as dict_of,  # noqa: F401  # import used externally via compatibility import
    )

# Determine which API is available at import time
try:
    _test_parser = pyparsing.Literal("test")
    _test_parser.set_parse_action(lambda: None)
    _USE_NEW_PYPARSING_API = True
except AttributeError:
    _USE_NEW_PYPARSING_API = False


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
