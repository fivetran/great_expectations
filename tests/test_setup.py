import sys
from pathlib import Path

import pytest

# Add the project root to the Python path so we can import from setup.py
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from setup import parse_requirements


class TestParseRequirements:
    @pytest.mark.parametrize(
        "content,expected",
        [
            pytest.param(
                """numpy>=1.20.0
pandas>=1.3.0
requests>=2.25.0""",
                ["numpy>=1.20.0", "pandas>=1.3.0", "requests>=2.25.0"],
                id="simple_requirements",
            ),
            pytest.param(
                """# This is a comment
numpy>=1.20.0
# Another comment
pandas>=1.3.0
requests>=2.25.0""",
                ["numpy>=1.20.0", "pandas>=1.3.0", "requests>=2.25.0"],
                id="full_line_comments",
            ),
            pytest.param(
                """numpy>=1.20.0  # Scientific computing
pandas>=1.3.0  # Data manipulation
requests>=2.25.0  # HTTP library""",
                ["numpy>=1.20.0", "pandas>=1.3.0", "requests>=2.25.0"],
                id="inline_comments",
            ),
            pytest.param(
                """numpy>=1.20.0

pandas>=1.3.0


requests>=2.25.0""",
                ["numpy>=1.20.0", "pandas>=1.3.0", "requests>=2.25.0"],
                id="empty_lines",
            ),
            pytest.param(
                """# Main dependencies
numpy>=1.20.0  # Scientific computing

# Data processing
pandas>=1.3.0

# HTTP requests
requests>=2.25.0  # For API calls

# Optional dependencies
# scipy>=1.7.0""",
                ["numpy>=1.20.0", "pandas>=1.3.0", "requests>=2.25.0"],
                id="mixed_content",
            ),
            pytest.param(
                """numpy>=1.20.0,<2.0
pandas>=1.3.0,!=1.4.0
requests~=2.25.0
scipy==1.7.3
matplotlib>3.0,<=3.5.2""",
                [
                    "numpy>=1.20.0,<2.0",
                    "pandas>=1.3.0,!=1.4.0",
                    "requests~=2.25.0",
                    "scipy==1.7.3",
                    "matplotlib>3.0,<=3.5.2",
                ],
                id="complex_versions",
            ),
            pytest.param(
                """requests[security]>=2.25.0
sqlalchemy[postgresql,mysql]>=1.4.0
pytest[testing]>=6.0.0  # Testing framework""",
                [
                    "requests[security]>=2.25.0",
                    "sqlalchemy[postgresql,mysql]>=1.4.0",
                    "pytest[testing]>=6.0.0",
                ],
                id="requirements_with_extras",
            ),
            pytest.param("", [], id="empty_file"),
            pytest.param(
                """# This file contains only comments
# No actual requirements
# Another comment line""",
                [],
                id="only_comments",
            ),
            pytest.param(
                """  numpy>=1.20.0
    pandas>=1.3.0
requests>=2.25.0  # comment with spaces  """,
                ["numpy>=1.20.0", "pandas>=1.3.0", "requests>=2.25.0"],
                id="whitespace_handling",
            ),
        ],
    )
    @pytest.mark.unit
    def test_parse_requirements(self, content, expected, tmp_path):
        """Test parsing requirements files with various content formats."""
        # Create temporary requirements file
        requirements_file = tmp_path / "requirements.txt"
        requirements_file.write_text(content)

        result = parse_requirements(requirements_file)
        assert result == expected

    @pytest.mark.unit
    def test_parse_requirements_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        with pytest.raises(FileNotFoundError):
            parse_requirements(Path("/nonexistent/path/requirements.txt"))
