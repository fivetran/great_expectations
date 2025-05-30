"""Utilities for parsing and handling package requirements."""

from __future__ import annotations

from pathlib import Path
from typing import Union

from packaging.requirements import Requirement


def parse_requirements_file(file_path: Union[str, Path]) -> list[str]:
    """
    Parse a requirements file and return a list of requirement strings.

    Handles comments (both full-line and inline) and empty lines.

    Args:
        file_path: Path to the requirements file

    Returns:
        List of requirement strings (e.g., ["pandas>=1.0.0", "numpy>=1.20.0"])

    Raises:
        FileNotFoundError: If the file doesn't exist
        InvalidRequirement: If a requirement line is malformed
    """
    with open(file_path) as f:
        content = f.read()

    return parse_requirements_content(content)


def parse_requirements_content(content: str) -> list[str]:
    """
    Parse requirements content and return a list of requirement strings.

    Handles comments (both full-line and inline) and empty lines.

    Args:
        content: String content of a requirements file

    Returns:
        List of requirement strings (e.g., ["pandas>=1.0.0", "numpy>=1.20.0"])

    Raises:
        InvalidRequirement: If a requirement line is malformed
    """
    requirements = []

    for line in content.splitlines():
        if line and not line.startswith("#"):
            # Remove inline comments
            requirement_string = line.split("#")[0].strip()
            if requirement_string:
                # Validate the requirement by parsing it
                req = Requirement(requirement_string)
                requirements.append(str(req))

    return requirements


def parse_requirements_file_to_objects(file_path: Union[str, Path]) -> list[Requirement]:
    """
    Parse a requirements file and return a list of Requirement objects.

    Args:
        file_path: Path to the requirements file

    Returns:
        List of Requirement objects

    Raises:
        FileNotFoundError: If the file doesn't exist
        InvalidRequirement: If a requirement line is malformed
    """
    with open(file_path) as f:
        content = f.read()

    return parse_requirements_content_to_objects(content)


def parse_requirements_content_to_objects(content: str) -> list[Requirement]:
    """
    Parse requirements content and return a list of Requirement objects.

    Args:
        content: String content of a requirements file

    Returns:
        List of Requirement objects

    Raises:
        InvalidRequirement: If a requirement line is malformed
    """
    requirements = []

    for line in content.splitlines():
        if line and not line.startswith("#"):
            # Remove inline comments
            requirement_string = line.split("#")[0].strip()
            if requirement_string:
                requirements.append(Requirement(requirement_string))

    return requirements
