"""Tests for packaging_utils module."""

import tempfile
from pathlib import Path

import pytest
from packaging.requirements import InvalidRequirement, Requirement

from great_expectations.packaging_utils import (
    parse_requirements_content,
    parse_requirements_content_to_objects,
    parse_requirements_file,
    parse_requirements_file_to_objects,
)


class TestParseRequirementsContent:
    """Tests for parse_requirements_content function."""

    def test_empty_content(self):
        """Test parsing empty content."""
        result = parse_requirements_content("")
        assert result == []

    def test_whitespace_only(self):
        """Test parsing content with only whitespace."""
        result = parse_requirements_content("   \n\t\n   ")
        assert result == []

    def test_comments_only(self):
        """Test parsing content with only comments."""
        content = """
        # This is a comment
        # Another comment
        """
        result = parse_requirements_content(content)
        assert result == []

    def test_single_requirement(self):
        """Test parsing a single requirement."""
        result = parse_requirements_content("pandas>=1.0.0")
        assert result == ["pandas>=1.0.0"]

    def test_multiple_requirements(self):
        """Test parsing multiple requirements."""
        content = """
        pandas>=1.0.0
        numpy>=1.20.0
        sqlalchemy>=1.4.0,<2.0.0
        """
        result = parse_requirements_content(content)
        expected = ["pandas>=1.0.0", "numpy>=1.20.0", "sqlalchemy<2.0.0,>=1.4.0"]
        assert result == expected

    def test_inline_comments(self):
        """Test parsing requirements with inline comments."""
        content = """
        pandas>=1.0.0  # Data manipulation library
        numpy>=1.20.0  # Numerical computing
        """
        result = parse_requirements_content(content)
        assert result == ["pandas>=1.0.0", "numpy>=1.20.0"]

    def test_mixed_content(self):
        """Test parsing content with mixed requirements and comments."""
        content = """
        # This is a header comment
        pandas>=1.0.0  # Data manipulation

        # Section for numerical libraries
        numpy>=1.20.0

        # Empty lines and more comments

        sqlalchemy>=1.4.0,<2.0.0  # Database toolkit
        # Final comment
        """
        result = parse_requirements_content(content)
        expected = ["pandas>=1.0.0", "numpy>=1.20.0", "sqlalchemy<2.0.0,>=1.4.0"]
        assert result == expected

    def test_complex_requirements(self):
        """Test parsing complex requirements with extras and markers."""
        content = """
        requests[security]>=2.25.0
        pandas>=1.0.0; python_version>="3.8"
        numpy>=1.20.0,<2.0.0
        """
        result = parse_requirements_content(content)
        assert len(result) == 3
        assert "requests[security]>=2.25.0" in result
        assert 'pandas>=1.0.0; python_version >= "3.8"' in result
        assert "numpy<2.0.0,>=1.20.0" in result

    def test_invalid_requirement(self):
        """Test that invalid requirements raise an error."""
        with pytest.raises(InvalidRequirement):
            parse_requirements_content("invalid requirement string >>>")

    def test_requirement_normalization(self):
        """Test that requirements are normalized."""
        content = "Pandas >= 1.0.0 , < 2.0.0"
        result = parse_requirements_content(content)
        # The exact normalization format may vary, but it should be parseable
        assert len(result) == 1
        req = Requirement(result[0])
        # Package names preserve case, but should be normalized for comparison
        assert req.name.lower() == "pandas"


class TestParseRequirementsContentToObjects:
    """Tests for parse_requirements_content_to_objects function."""

    def test_returns_requirement_objects(self):
        """Test that the function returns Requirement objects."""
        content = """
        pandas>=1.0.0
        numpy>=1.20.0
        """
        result = parse_requirements_content_to_objects(content)
        assert len(result) == 2
        assert all(isinstance(req, Requirement) for req in result)
        assert result[0].name == "pandas"
        assert result[1].name == "numpy"

    def test_requirement_attributes(self):
        """Test that Requirement object attributes are accessible."""
        content = "pandas>=1.0.0,<2.0.0"
        result = parse_requirements_content_to_objects(content)
        req = result[0]
        assert req.name == "pandas"
        assert str(req.specifier) == "<2.0.0,>=1.0.0"


class TestParseRequirementsFile:
    """Tests for parse_requirements_file function."""

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        with pytest.raises(FileNotFoundError):
            parse_requirements_file("non_existent_file.txt")

    def test_parse_real_file(self):
        """Test parsing a real requirements file."""
        content = """
        # Development requirements
        pandas>=1.0.0  # Data manipulation
        numpy>=1.20.0

        # Database requirements
        sqlalchemy>=1.4.0,<2.0.0
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = parse_requirements_file(temp_path)
            expected = ["pandas>=1.0.0", "numpy>=1.20.0", "sqlalchemy<2.0.0,>=1.4.0"]
            assert result == expected
        finally:
            Path(temp_path).unlink()

    def test_parse_with_pathlib_path(self):
        """Test parsing using a pathlib.Path object."""
        content = "pandas>=1.0.0\nnumpy>=1.20.0"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            result = parse_requirements_file(temp_path)
            assert result == ["pandas>=1.0.0", "numpy>=1.20.0"]
        finally:
            temp_path.unlink()


class TestParseRequirementsFileToObjects:
    """Tests for parse_requirements_file_to_objects function."""

    def test_parse_file_to_objects(self):
        """Test parsing a file to Requirement objects."""
        content = """
        pandas>=1.0.0
        numpy>=1.20.0
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = parse_requirements_file_to_objects(temp_path)
            assert len(result) == 2
            assert all(isinstance(req, Requirement) for req in result)
            assert result[0].name == "pandas"
            assert result[1].name == "numpy"
        finally:
            Path(temp_path).unlink()


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_windows_line_endings(self):
        """Test parsing content with Windows line endings."""
        content = "pandas>=1.0.0\r\nnumpy>=1.20.0\r\n"
        result = parse_requirements_content(content)
        assert result == ["pandas>=1.0.0", "numpy>=1.20.0"]

    def test_mixed_line_endings(self):
        """Test parsing content with mixed line endings."""
        content = "pandas>=1.0.0\r\nnumpy>=1.20.0\nsqlalchemy>=1.4.0\r"
        result = parse_requirements_content(content)
        assert len(result) == 3

    def test_trailing_whitespace(self):
        """Test parsing requirements with trailing whitespace."""
        content = "pandas>=1.0.0   \nnumpy>=1.20.0\t\n"
        result = parse_requirements_content(content)
        assert result == ["pandas>=1.0.0", "numpy>=1.20.0"]

    def test_unicode_characters(self):
        """Test that unicode characters in comments don't break parsing."""
        content = """
        # Requirements with unicode: ñáéíóú
        pandas>=1.0.0  # Data library 📊
        numpy>=1.20.0  # Math library ∑
        """
        result = parse_requirements_content(content)
        assert result == ["pandas>=1.0.0", "numpy>=1.20.0"]

    def test_very_long_requirement(self):
        """Test parsing a very long requirement string."""
        long_req = "some-very-long-package-name-that-exceeds-normal-length" + ">=1.0.0"
        result = parse_requirements_content(long_req)
        assert len(result) == 1
        assert "some-very-long-package-name-that-exceeds-normal-length" in result[0]
