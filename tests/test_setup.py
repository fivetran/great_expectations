"""Unit tests for setup.py functions."""

import sys
import tempfile
from pathlib import Path

import pytest

# Add the project root to the Python path so we can import from setup.py
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from setup import parse_requirements


class TestParseRequirements:
    @pytest.mark.unit
    def test_parse_simple_requirements(self):
        content = """numpy>=1.20.0
pandas>=1.3.0
requests>=2.25.0"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            f.flush()

            result = parse_requirements(Path(f.name))

        expected = ["numpy>=1.20.0", "pandas>=1.3.0", "requests>=2.25.0"]
        assert result == expected

    @pytest.mark.unit
    def test_parse_requirements_with_comments(self):
        """Test parsing requirements file with full-line comments."""
        content = """# This is a comment
numpy>=1.20.0
# Another comment
pandas>=1.3.0
requests>=2.25.0"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            f.flush()

            result = parse_requirements(Path(f.name))

        expected = ["numpy>=1.20.0", "pandas>=1.3.0", "requests>=2.25.0"]
        assert result == expected

    @pytest.mark.unit
    def test_parse_requirements_with_inline_comments(self):
        """Test parsing requirements file with inline comments."""
        content = """numpy>=1.20.0  # Scientific computing
pandas>=1.3.0  # Data manipulation
requests>=2.25.0  # HTTP library"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            f.flush()

            result = parse_requirements(Path(f.name))

        expected = ["numpy>=1.20.0", "pandas>=1.3.0", "requests>=2.25.0"]
        assert result == expected

    def test_parse_requirements_with_empty_lines(self):
        """Test parsing requirements file with empty lines."""
        content = """numpy>=1.20.0

pandas>=1.3.0


requests>=2.25.0"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            f.flush()

            result = parse_requirements(Path(f.name))

        expected = ["numpy>=1.20.0", "pandas>=1.3.0", "requests>=2.25.0"]
        assert result == expected

    @pytest.mark.unit
    def test_parse_requirements_mixed_content(self):
        """Test parsing requirements file with mixed content
        (comments, empty lines, inline comments)."""
        content = """# Main dependencies
numpy>=1.20.0  # Scientific computing

# Data processing
pandas>=1.3.0

# HTTP requests
requests>=2.25.0  # For API calls

# Optional dependencies
# scipy>=1.7.0"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            f.flush()

            result = parse_requirements(Path(f.name))

        expected = ["numpy>=1.20.0", "pandas>=1.3.0", "requests>=2.25.0"]
        assert result == expected

    @pytest.mark.unit
    def test_parse_requirements_complex_versions(self):
        """Test parsing requirements with complex version specifications."""
        content = """numpy>=1.20.0,<2.0
pandas>=1.3.0,!=1.4.0
requests~=2.25.0
scipy==1.7.3
matplotlib>3.0,<=3.5.2"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            f.flush()

            result = parse_requirements(Path(f.name))

        expected = [
            "numpy>=1.20.0,<2.0",
            "pandas>=1.3.0,!=1.4.0",
            "requests~=2.25.0",
            "scipy==1.7.3",
            "matplotlib>3.0,<=3.5.2",
        ]
        assert result == expected

    @pytest.mark.unit
    def test_parse_requirements_with_extras(self):
        """Test parsing requirements with extras."""
        content = """requests[security]>=2.25.0
sqlalchemy[postgresql,mysql]>=1.4.0
pytest[testing]>=6.0.0  # Testing framework"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            f.flush()

            result = parse_requirements(Path(f.name))

        expected = [
            "requests[security]>=2.25.0",
            "sqlalchemy[postgresql,mysql]>=1.4.0",
            "pytest[testing]>=6.0.0",
        ]
        assert result == expected

    @pytest.mark.unit
    def test_parse_empty_requirements_file(self):
        """Test parsing an empty requirements file."""
        content = ""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            f.flush()

            result = parse_requirements(Path(f.name))

        assert result == []

    @pytest.mark.unit
    def test_parse_requirements_only_comments(self):
        """Test parsing a requirements file with only comments."""
        content = """# This file contains only comments
# No actual requirements
# Another comment line"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            f.flush()

            result = parse_requirements(Path(f.name))

        assert result == []

    @pytest.mark.unit
    def test_parse_requirements_whitespace_handling(self):
        """Test that whitespace is properly handled."""
        content = """  numpy>=1.20.0
    pandas>=1.3.0
requests>=2.25.0  # comment with spaces  """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            f.flush()

            result = parse_requirements(Path(f.name))

        expected = ["numpy>=1.20.0", "pandas>=1.3.0", "requests>=2.25.0"]
        assert result == expected

    @pytest.mark.unit
    def test_parse_requirements_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        with pytest.raises(FileNotFoundError):
            parse_requirements(Path("/nonexistent/path/requirements.txt"))
