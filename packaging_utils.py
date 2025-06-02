"""Packaging utilities for parsing requirements files.

This module provides shared functionality for parsing requirements files
across the Great Expectations codebase, eliminating code duplication.
"""

from typing import IO, Iterable

from packaging.requirements import Requirement


def _parse_requirements_lines(lines: Iterable[str]) -> list[Requirement]:
    """Parse requirements from an iterable of lines.

    Args:
        lines: An iterable of requirement lines.

    Returns:
        A list of Requirement objects.
    """
    requirements = []
    for line in lines:
        cleaned_line = line.strip()
        if cleaned_line and not cleaned_line.startswith("#"):
            # Remove inline comments if present
            if "#" in cleaned_line:
                cleaned_line = cleaned_line.split("#")[0].strip()
            if cleaned_line:  # Check if there's still content after removing comments
                requirements.append(Requirement(cleaned_line))
    return requirements


def parse_requirements_content(content: str) -> list[str]:
    """Parse requirements from a string containing requirements.

    Args:
        content: A string containing requirements, one per line.

    Returns:
        A list of requirement strings.
    """
    requirements = _parse_requirements_lines(content.splitlines())
    return [str(req) for req in requirements]


def parse_requirements_file(file_path: str) -> list[str]:
    """Parse requirements from a file path.

    Args:
        file_path: Path to the requirements file.

    Returns:
        A list of requirement strings.
    """
    with open(file_path) as f:
        return parse_requirements_file_obj(f)


def parse_requirements_file_obj(file_obj: IO[str]) -> list[str]:
    """Parse requirements from a file object.

    Args:
        file_obj: A file object containing requirements.

    Returns:
        A list of requirement strings.
    """
    requirements = _parse_requirements_lines(file_obj)
    return [str(req) for req in requirements]


def parse_requirements_content_to_objects(content: str) -> list[Requirement]:
    """Parse requirements from a string containing requirements.

    Args:
        content: A string containing requirements, one per line.

    Returns:
        A list of Requirement objects.
    """
    return _parse_requirements_lines(content.splitlines())
