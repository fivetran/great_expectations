import os
import sys
from pathlib import Path

import pytest

# Add the project root to the Python path so we can import from setup.py
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from setup import get_extras_require, parse_requirements


class TestSetupIntegration:
    @pytest.mark.filesystem
    def test_parse_main_requirements_txt(self):
        """Test parsing the main requirements.txt file."""
        requirements_file = project_root / "requirements.txt"

        assert requirements_file.exists(), f"requirements.txt not found at {requirements_file}"

        requirements = parse_requirements(requirements_file)

        assert len(requirements) > 0, "requirements.txt should contain at least one requirement"
        assert all(req.strip() for req in requirements), "No requirements should be empty strings"
        assert not any(req.startswith("#") for req in requirements), (
            "No comment lines should be in the result"
        )

        print(f"Found {len(requirements)} requirements in requirements.txt")
        print("First few requirements:", requirements[:5])

    @pytest.mark.filesystem
    def test_parse_dev_requirements_files(self):
        """Test parsing all dev requirements files in the reqs/ directory."""
        reqs_dir = project_root / "reqs"

        assert reqs_dir.exists(), f"reqs directory not found at {reqs_dir}"
        requirements_files = list(reqs_dir.glob("requirements-dev-*.txt"))
        assert len(requirements_files) > 0, "Should find at least one dev requirements file"

        for req_file in requirements_files:
            requirements = parse_requirements(req_file)

            assert all(isinstance(req, str) for req in requirements), (
                f"All requirements in {req_file.name} should be strings"
            )
            assert all(req.strip() for req in requirements), (
                f"No requirements in {req_file.name} should be empty strings"
            )
            assert not any(req.startswith("#") for req in requirements), (
                f"No comment lines should be in the result for {req_file.name}"
            )

            print(f"Parsed {req_file.name}: {len(requirements)} requirements")

    @pytest.mark.filesystem
    def test_get_extras_require_functionality(self):
        """Test that get_extras_require() works end-to-end."""
        # Change to project root for relative path resolution
        original_cwd = Path.cwd()
        try:
            os.chdir(project_root)

            extras = get_extras_require()

            assert len(extras) > 0, "Should have at least one extra requirement set"
            for key, requirements in extras.items():
                assert isinstance(requirements, list), f"Extra '{key}' should be a list"
                assert all(isinstance(req, str) for req in requirements), (
                    f"All requirements for extra '{key}' should be strings"
                )
                assert all(req.strip() for req in requirements), (
                    f"No requirements for extra '{key}' should be empty strings"
                )

            print(f"Found {len(extras)} extra requirement sets")
            print("Extra names:", list(extras.keys()))

        finally:
            os.chdir(original_cwd)

    @pytest.mark.filesystem
    def test_oracle_is_not_a_published_extra(self):
        """Oracle's driver is installed for its test lane, not offered to users.

        `get_extras_require` derives the extras map by globbing `reqs/`, so
        `requirements-dev-oracle.txt` — which exists so the Oracle test lane can
        install a driver — is on its own enough to publish
        `pip install 'great_expectations[oracle]'`. Oracle does not yet pass the
        curated suite, so that install path would promise support that isn't there.
        The key is held in `ignore_keys` until it does, and this is what keeps the
        hold from being reverted by accident.
        """
        original_cwd = Path.cwd()
        try:
            os.chdir(project_root)
            extras = get_extras_require()
        finally:
            os.chdir(original_cwd)

        assert (project_root / "reqs" / "requirements-dev-oracle.txt").exists(), (
            "The Oracle dev requirements file is what makes this hold necessary; "
            "if it is gone, remove this test with it."
        )
        assert "oracle" not in extras, (
            "`oracle` is now a published extra. If that is intended, delete this test "
            "and add the install row to the SQL dialect installation-commands table."
        )
