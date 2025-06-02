"""Integration tests for packaging_utils module."""

import sys
from pathlib import Path

from packaging.requirements import Requirement

# Add the root directory to the Python path to import packaging_utils
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from packaging_utils import parse_requirements_file


def test_parse_real_requirements_file():
    """Test parsing the core requirements.txt file."""
    req_file = Path(__file__).parent.parent.parent / "requirements.txt"
    if req_file.exists():
        result = parse_requirements_file(str(req_file))
        assert len(result) > 0
        # Verify all results are valid requirement strings
        for req_str in result:
            Requirement(req_str)  # Should not raise an exception
