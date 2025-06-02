"""Tests for packaging_utils module."""

import sys
import tempfile
from pathlib import Path

from packaging.requirements import Requirement

# Add the root directory to the Python path to import packaging_utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from packaging_utils import (
    parse_requirements_content,
    parse_requirements_content_to_objects,
    parse_requirements_file,
    parse_requirements_file_obj,
)


class TestParseRequirementsContent:
    """Test parsing requirements from string content."""

    def test_empty_content(self):
        """Test parsing empty content."""
        result = parse_requirements_content("")
        assert result == []

    def test_single_requirement(self):
        """Test parsing a single requirement."""
        content = "requests>=2.25.0"
        result = parse_requirements_content(content)
        assert result == ["requests>=2.25.0"]

    def test_multiple_requirements(self):
        """Test parsing multiple requirements."""
        content = "requests>=2.25.0\npandas==1.3.0\nnumpy>=1.20"
        result = parse_requirements_content(content)
        assert result == ["requests>=2.25.0", "pandas==1.3.0", "numpy>=1.20"]

    def test_with_comments(self):
        """Test parsing requirements with comments."""
        content = """# This is a comment
requests>=2.25.0
# Another comment
pandas==1.3.0"""
        result = parse_requirements_content(content)
        assert result == ["requests>=2.25.0", "pandas==1.3.0"]

    def test_with_inline_comments(self):
        """Test parsing requirements with inline comments."""
        content = "requests>=2.25.0  # For HTTP requests\npandas==1.3.0  # Data analysis"
        result = parse_requirements_content(content)
        assert result == ["requests>=2.25.0", "pandas==1.3.0"]

    def test_with_empty_lines(self):
        """Test parsing requirements with empty lines."""
        content = """requests>=2.25.0

pandas==1.3.0


numpy>=1.20"""
        result = parse_requirements_content(content)
        assert result == ["requests>=2.25.0", "pandas==1.3.0", "numpy>=1.20"]


class TestParseRequirementsContentToObjects:
    """Test parsing requirements from string content to Requirement objects."""

    def test_single_requirement_object(self):
        """Test parsing a single requirement to object."""
        content = "requests>=2.25.0"
        result = parse_requirements_content_to_objects(content)
        assert len(result) == 1
        assert isinstance(result[0], Requirement)
        assert result[0].name == "requests"

    def test_multiple_requirements_objects(self):
        """Test parsing multiple requirements to objects."""
        content = "requests>=2.25.0\npandas==1.3.0"
        result = parse_requirements_content_to_objects(content)
        assert len(result) == 2
        assert all(isinstance(req, Requirement) for req in result)
        assert result[0].name == "requests"
        assert result[1].name == "pandas"


class TestParseRequirementsFile:
    """Test parsing requirements from files."""

    def test_parse_requirements_file(self):
        """Test parsing a requirements file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("requests>=2.25.0\npandas==1.3.0")
            temp_file = f.name

        try:
            result = parse_requirements_file(temp_file)
            assert result == ["requests>=2.25.0", "pandas==1.3.0"]
        finally:
            Path(temp_file).unlink()

    def test_parse_requirements_file_obj(self):
        """Test parsing a requirements file object."""
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt") as f:
            f.write("requests>=2.25.0\npandas==1.3.0")
            f.seek(0)
            result = parse_requirements_file_obj(f)
            assert result == ["requests>=2.25.0", "pandas==1.3.0"]
