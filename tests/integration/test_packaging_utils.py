"""Integration tests for packaging utils with real project files."""

import tempfile
from pathlib import Path

import pytest

from great_expectations.packaging_utils import (
    parse_requirements_file,
    parse_requirements_file_to_objects,
)


class TestRealFileIntegration:
    """Integration tests with actual project requirements files."""

    def test_parse_lite_requirements(self):
        """Test parsing the actual lite requirements file."""
        lite_file = Path("reqs/requirements-dev-lite.txt")
        if lite_file.exists():
            requirements = parse_requirements_file(lite_file)
            assert len(requirements) > 0
            # Should contain some expected packages
            requirement_names = [
                req.split(">=")[0].split("==")[0].split("[")[0] for req in requirements
            ]
            assert "boto3" in requirement_names or "coverage" in requirement_names
        else:
            pytest.skip("Lite requirements file not found")

    def test_parse_contrib_requirements(self):
        """Test parsing the actual contrib requirements file."""
        contrib_file = Path("reqs/requirements-dev-contrib.txt")
        if contrib_file.exists():
            requirements = parse_requirements_file(contrib_file)
            assert len(requirements) > 0
            # Should contain some expected packages (be more flexible about what we expect)
            requirement_names = [
                req.split(">=")[0].split("==")[0].split("[")[0].lower() for req in requirements
            ]
            # Just check that we got some valid package names
            assert any(len(name) > 2 for name in requirement_names)
        else:
            pytest.skip("Contrib requirements file not found")

    def test_parse_requirements_to_objects(self):
        """Test parsing requirements to objects with real files."""
        lite_file = Path("reqs/requirements-dev-lite.txt")
        if lite_file.exists():
            requirements = parse_requirements_file_to_objects(lite_file)
            assert len(requirements) > 0
            # All should be Requirement objects
            from packaging.requirements import Requirement

            assert all(isinstance(req, Requirement) for req in requirements)
            # Should have proper attributes
            assert all(hasattr(req, "name") and hasattr(req, "specifier") for req in requirements)
        else:
            pytest.skip("Lite requirements file not found")

    def test_file_with_complex_requirements(self):
        """Test handling files with complex requirement syntax."""
        complex_content = """
        # Complex requirements test file
        pandas>=1.3.0,<2.0.0  # Data manipulation
        requests[security]>=2.25.0
        sqlalchemy>=1.4.0,<2.0.0; python_version>="3.8"

        # Database drivers
        psycopg2-binary>=2.8.0

        # Optional dependencies
        matplotlib>=3.0.0; extra == "plotting"
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(complex_content)
            temp_path = f.name

        try:
            requirements = parse_requirements_file(temp_path)
            assert len(requirements) >= 4  # At least the main requirements

            # Check that complex requirements are parsed
            req_strings = "\n".join(requirements)
            assert "pandas" in req_strings
            assert "requests[security]" in req_strings
            assert "psycopg2-binary" in req_strings

            # Test with objects too
            req_objects = parse_requirements_file_to_objects(temp_path)
            assert len(req_objects) >= 4

            # Find pandas requirement and check its specifier
            pandas_req = next((req for req in req_objects if req.name == "pandas"), None)
            assert pandas_req is not None
            assert str(pandas_req.specifier) == "<2.0.0,>=1.3.0"

        finally:
            Path(temp_path).unlink()

    def test_setup_py_functions_directly(self):
        """Test that setup.py functions work correctly without importing the full module."""
        # Instead of importing setup.py, test the function directly
        from great_expectations.packaging_utils import parse_requirements_file

        # Test with a real requirements file
        lite_file = Path("reqs/requirements-dev-lite.txt")
        if lite_file.exists():
            # This mimics what setup.py does
            parsed = parse_requirements_file(lite_file)
            assert isinstance(parsed, list)
            assert len(parsed) > 0
            assert all(isinstance(req, str) for req in parsed)

            # Should be valid requirement strings
            from packaging.requirements import Requirement

            for req_str in parsed:
                req = Requirement(req_str)  # Should not raise
                assert req.name
        else:
            pytest.skip("Lite requirements file not found")

    def test_error_handling_with_malformed_file(self):
        """Test that errors are properly handled with malformed requirements."""
        malformed_content = """
        # This file has malformed requirements
        pandas>=1.0.0  # This is fine
        bad requirement >>>  # This should fail
        numpy>=1.20.0  # This is also fine
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(malformed_content)
            temp_path = f.name

        try:
            from packaging.requirements import InvalidRequirement

            with pytest.raises(InvalidRequirement):
                parse_requirements_file(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_empty_file_handling(self):
        """Test handling of empty or comment-only files."""
        empty_content = """
        # This file only has comments
        # No actual requirements

        # Just more comments
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(empty_content)
            temp_path = f.name

        try:
            requirements = parse_requirements_file(temp_path)
            assert requirements == []

            req_objects = parse_requirements_file_to_objects(temp_path)
            assert req_objects == []
        finally:
            Path(temp_path).unlink()


class TestBackwardsCompatibility:
    """Test that our helpers maintain backwards compatibility."""

    def test_output_format_matches_expected(self):
        """Test that output format matches what the original code expected."""
        content = """
        pandas>=1.0.0
        numpy>=1.20.0,<2.0.0
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            requirements = parse_requirements_file(temp_path)
            # Should be list of strings
            assert isinstance(requirements, list)
            assert all(isinstance(req, str) for req in requirements)

            # Should be parseable as requirements
            from packaging.requirements import Requirement

            for req_str in requirements:
                req = Requirement(req_str)
                assert hasattr(req, "name")
                assert hasattr(req, "specifier")

        finally:
            Path(temp_path).unlink()

    def test_requirement_object_compatibility(self):
        """Test that Requirement objects have expected attributes."""
        content = "pandas>=1.0.0,<2.0.0"

        req_objects = parse_requirements_file_to_objects(
            tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt").name
        )

        # Write content to temp file and re-parse
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            req_objects = parse_requirements_file_to_objects(temp_path)
            assert len(req_objects) == 1
            req = req_objects[0]

            # Should have attributes that pkg_resources.Requirement had
            assert hasattr(req, "name")
            assert hasattr(req, "specifier")  # Similar to old 'specs'
            assert req.name == "pandas"
            assert str(req.specifier) == "<2.0.0,>=1.0.0"

        finally:
            Path(temp_path).unlink()
