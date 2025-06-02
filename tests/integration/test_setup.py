"""Integration tests for setup.py functionality."""

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

        # Verify the file exists
        assert requirements_file.exists(), f"requirements.txt not found at {requirements_file}"

        # Parse the requirements
        requirements = parse_requirements(requirements_file)

        # Verify we got some requirements
        assert len(requirements) > 0, "requirements.txt should contain at least one requirement"

        # Verify all requirements are strings
        assert all(isinstance(req, str) for req in requirements), (
            "All requirements should be strings"
        )

        # Verify no empty strings
        assert all(req.strip() for req in requirements), "No requirements should be empty strings"

        # Verify no comment lines made it through
        assert not any(req.startswith("#") for req in requirements), (
            "No comment lines should be in the result"
        )

        # Print some info for debugging
        print(f"Found {len(requirements)} requirements in requirements.txt")
        print("First few requirements:", requirements[:5])

    @pytest.mark.filesystem
    def test_parse_dev_requirements_files(self):
        """Test parsing all dev requirements files in the reqs/ directory."""
        reqs_dir = project_root / "reqs"

        # Verify the reqs directory exists
        assert reqs_dir.exists(), f"reqs directory not found at {reqs_dir}"

        # Find all requirements files
        requirements_files = list(reqs_dir.glob("requirements-dev-*.txt"))

        # Verify we found some files
        assert len(requirements_files) > 0, "Should find at least one dev requirements file"

        # Test parsing each file
        for req_file in requirements_files:
            requirements = parse_requirements(req_file)

            # Each file should either be empty or contain valid requirements
            if requirements:
                # Verify all requirements are strings
                assert all(isinstance(req, str) for req in requirements), (
                    f"All requirements in {req_file.name} should be strings"
                )

                # Verify no empty strings
                assert all(req.strip() for req in requirements), (
                    f"No requirements in {req_file.name} should be empty strings"
                )

                # Verify no comment lines made it through
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

            # Get the extras requirements
            extras = get_extras_require()

            # Verify we got a dictionary
            assert isinstance(extras, dict), "get_extras_require should return a dictionary"

            # Verify we have some extras
            assert len(extras) > 0, "Should have at least one extra requirement set"

            # Verify all values are lists of strings
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
    def test_requirements_txt_contains_expected_packages(self):
        """Test that requirements.txt contains expected core packages."""
        requirements_file = project_root / "requirements.txt"
        requirements = parse_requirements(requirements_file)

        # Convert to a single string for easier searching
        requirements_text = " ".join(requirements).lower()

        # Check for some expected core packages (these may change over time)
        expected_packages = [
            "altair",
            "cryptography",
            "jinja2",
            "jsonschema",
            "marshmallow",
            "numpy",
            "pandas",
            "pydantic",
            "requests",
            "scipy",
        ]

        found_packages = []
        for package in expected_packages:
            if package in requirements_text:
                found_packages.append(package)

        # We should find at least half of the expected packages
        assert len(found_packages) >= len(expected_packages) // 2, (
            f"Should find at least {len(expected_packages) // 2} "
            f"expected packages, found {len(found_packages)}: {found_packages}"
        )

        print(f"Found expected packages: {found_packages}")

    @pytest.mark.filesystem
    def test_no_pkg_resources_in_requirements(self):
        """Test that pkg_resources is not in any requirements files."""
        # Check main requirements.txt
        requirements_file = project_root / "requirements.txt"
        if requirements_file.exists():
            requirements = parse_requirements(requirements_file)
            requirements_text = " ".join(requirements).lower()
            assert "pkg_resources" not in requirements_text, (
                "pkg_resources should not be in requirements.txt"
            )
            assert "pkg-resources" not in requirements_text, (
                "pkg-resources should not be in requirements.txt"
            )

        # Check dev requirements files
        reqs_dir = project_root / "reqs"
        if reqs_dir.exists():
            requirements_files = list(reqs_dir.glob("requirements-dev-*.txt"))
            for req_file in requirements_files:
                requirements = parse_requirements(req_file)
                requirements_text = " ".join(requirements).lower()
                assert "pkg_resources" not in requirements_text, (
                    f"pkg_resources should not be in {req_file.name}"
                )
                assert "pkg-resources" not in requirements_text, (
                    f"pkg-resources should not be in {req_file.name}"
                )

    @pytest.mark.filesystem
    def test_requirements_have_version_specifiers(self):
        """Test that most requirements have version specifiers."""
        requirements_file = project_root / "requirements.txt"
        requirements = parse_requirements(requirements_file)

        # Count requirements with version specifiers
        versioned_requirements = []
        for req in requirements:
            if any(op in req for op in [">=", "<=", "==", "!=", "~=", ">", "<"]):
                versioned_requirements.append(req)

        # Most requirements should have version specifiers for reproducible builds
        versioned_ratio = len(versioned_requirements) / len(requirements) if requirements else 0

        print(
            "Requirements with version specifiers: "
            f"{len(versioned_requirements)}/{len(requirements)} ({versioned_ratio:.1%})"
        )

        # At least 80% of requirements should have version specifiers
        assert versioned_ratio >= 0.8, (
            "At least 80% of requirements should have version specifiers, "
            f"got {versioned_ratio:.1%}"
        )
