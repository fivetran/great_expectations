import pytest

from great_expectations.expectations.expectation import (
    _add_unexpected_index_query_to_result,
    _format_map_output,
)

# module level markers
pytestmark = pytest.mark.unit


def test_format_map_output_with_numbers():
    success = False
    element_count = 5
    nonnull_count = 5
    unexpected_list = [
        {"foreign_key_1": 1, "foreign_key_2": 2},
        {"foreign_key_1": 1, "foreign_key_2": 2},
        {"foreign_key_1": 1, "foreign_key_2": 2},
    ]
    unexpected_index_list = [1, 2, 3]
    assert _format_map_output(
        result_format={
            "result_format": "COMPLETE",
            "partial_unexpected_count": 20,
            "include_unexpected_rows": False,
        },
        success=success,
        element_count=element_count,
        nonnull_count=nonnull_count,
        unexpected_count=len(unexpected_list),
        unexpected_list=unexpected_list,
        unexpected_index_list=unexpected_index_list,
    ) == {
        "success": False,
        "result": {
            "element_count": 5,
            "missing_count": 0,
            "missing_percent": 0.0,
            "partial_unexpected_list": [
                {"foreign_key_1": 1, "foreign_key_2": 2},
                {"foreign_key_1": 1, "foreign_key_2": 2},
                {"foreign_key_1": 1, "foreign_key_2": 2},
            ],
            "unexpected_count": 3,
            "unexpected_percent": 60.0,
            "unexpected_percent_total": 60.0,
            "unexpected_percent_nonmissing": 60.0,
            "partial_unexpected_counts": [{"value": (1, 2), "count": 3}],
            "partial_unexpected_index_list": [1, 2, 3],
            "unexpected_list": [
                {"foreign_key_1": 1, "foreign_key_2": 2},
                {"foreign_key_1": 1, "foreign_key_2": 2},
                {"foreign_key_1": 1, "foreign_key_2": 2},
            ],
            "unexpected_index_list": [1, 2, 3],
        },
    }


def test_format_map_output_with_numbers_without_values():
    success = False
    element_count = 5
    nonnull_count = 5
    unexpected_list = [
        {"foreign_key_1": 1, "foreign_key_2": 2},
        {"foreign_key_1": 1, "foreign_key_2": 2},
        {"foreign_key_1": 1, "foreign_key_2": 2},
    ]
    unexpected_index_list = [1, 2, 3]
    assert _format_map_output(
        result_format={
            "result_format": "COMPLETE",
            "partial_unexpected_count": 20,
            "include_unexpected_rows": False,
            "exclude_unexpected_values": True,
        },
        success=success,
        element_count=element_count,
        nonnull_count=nonnull_count,
        unexpected_count=len(unexpected_list),
        unexpected_list=unexpected_list,
        unexpected_index_list=unexpected_index_list,
    ) == {
        "success": False,
        "result": {
            "element_count": 5,
            "missing_count": 0,
            "missing_percent": 0.0,
            "unexpected_count": 3,
            "unexpected_percent": 60.0,
            "unexpected_percent_total": 60.0,
            "unexpected_percent_nonmissing": 60.0,
            "partial_unexpected_index_list": [1, 2, 3],
            "unexpected_index_list": [1, 2, 3],
        },
    }


def test_format_map_output_with_strings():
    success = False
    element_count = 5
    nonnull_count = 5
    unexpected_list = [
        {"foreign_key_1": "a", "foreign_key_2": 2},
        {"foreign_key_1": "a", "foreign_key_2": 2},
        {"foreign_key_1": "a", "foreign_key_2": 2},
    ]
    unexpected_index_list = [1, 2, 3]
    assert _format_map_output(
        result_format={
            "result_format": "COMPLETE",
            "partial_unexpected_count": 20,
            "include_unexpected_rows": False,
        },
        success=success,
        element_count=element_count,
        nonnull_count=nonnull_count,
        unexpected_count=len(unexpected_list),
        unexpected_list=unexpected_list,
        unexpected_index_list=unexpected_index_list,
    ) == {
        "success": False,
        "result": {
            "element_count": 5,
            "missing_count": 0,
            "missing_percent": 0.0,
            "partial_unexpected_list": [
                {"foreign_key_1": "a", "foreign_key_2": 2},
                {"foreign_key_1": "a", "foreign_key_2": 2},
                {"foreign_key_1": "a", "foreign_key_2": 2},
            ],
            "unexpected_count": 3,
            "unexpected_percent": 60.0,
            "unexpected_percent_total": 60.0,
            "unexpected_percent_nonmissing": 60.0,
            "partial_unexpected_counts": [{"value": ("a", 2), "count": 3}],
            "partial_unexpected_index_list": [1, 2, 3],
            "unexpected_list": [
                {"foreign_key_1": "a", "foreign_key_2": 2},
                {"foreign_key_1": "a", "foreign_key_2": 2},
                {"foreign_key_1": "a", "foreign_key_2": 2},
            ],
            "unexpected_index_list": [1, 2, 3],
        },
    }


def test_format_map_output_with_strings_without_values():
    success = False
    element_count = 5
    nonnull_count = 5
    unexpected_list = [
        {"foreign_key_1": "a", "foreign_key_2": 2},
        {"foreign_key_1": "a", "foreign_key_2": 2},
        {"foreign_key_1": "a", "foreign_key_2": 2},
    ]
    unexpected_index_list = [1, 2, 3]
    assert _format_map_output(
        result_format={
            "result_format": "COMPLETE",
            "partial_unexpected_count": 20,
            "include_unexpected_rows": False,
            "exclude_unexpected_values": True,
        },
        success=success,
        element_count=element_count,
        nonnull_count=nonnull_count,
        unexpected_count=len(unexpected_list),
        unexpected_list=unexpected_list,
        unexpected_index_list=unexpected_index_list,
    ) == {
        "success": False,
        "result": {
            "element_count": 5,
            "missing_count": 0,
            "missing_percent": 0.0,
            "unexpected_count": 3,
            "unexpected_percent": 60.0,
            "unexpected_percent_total": 60.0,
            "unexpected_percent_nonmissing": 60.0,
            "partial_unexpected_index_list": [1, 2, 3],
            "unexpected_index_list": [1, 2, 3],
        },
    }


def test_format_map_output_with_strings_two_matches():
    success = False
    element_count = 5
    nonnull_count = 5
    unexpected_list = [
        {"foreign_key_1": "a", "foreign_key_2": 2},
        {"foreign_key_1": "a", "foreign_key_2": 2},
        {"foreign_key_1": "b", "foreign_key_2": 3},
    ]
    unexpected_index_list = [1, 3]
    assert _format_map_output(
        result_format={
            "result_format": "COMPLETE",
            "partial_unexpected_count": 20,
            "include_unexpected_rows": False,
        },
        success=success,
        element_count=element_count,
        nonnull_count=nonnull_count,
        unexpected_count=len(unexpected_list),
        unexpected_list=unexpected_list,
        unexpected_index_list=unexpected_index_list,
    ) == {
        "success": False,
        "result": {
            "element_count": 5,
            "missing_count": 0,
            "missing_percent": 0.0,
            "partial_unexpected_list": [
                {"foreign_key_1": "a", "foreign_key_2": 2},
                {"foreign_key_1": "a", "foreign_key_2": 2},
                {"foreign_key_1": "b", "foreign_key_2": 3},
            ],
            "unexpected_count": 3,
            "unexpected_percent": 60.0,
            "unexpected_percent_total": 60.0,
            "unexpected_percent_nonmissing": 60.0,
            "partial_unexpected_counts": [
                {"value": ("a", 2), "count": 2},
                {"value": ("b", 3), "count": 1},
            ],
            "partial_unexpected_index_list": [1, 3],
            "unexpected_list": [
                {"foreign_key_1": "a", "foreign_key_2": 2},
                {"foreign_key_1": "a", "foreign_key_2": 2},
                {"foreign_key_1": "b", "foreign_key_2": 3},
            ],
            "unexpected_index_list": [1, 3],
        },
    }


def test_format_map_output_with_strings_two_matches_without_values():
    success = False
    element_count = 5
    nonnull_count = 5
    unexpected_list = [
        {"foreign_key_1": "a", "foreign_key_2": 2},
        {"foreign_key_1": "a", "foreign_key_2": 2},
        {"foreign_key_1": "b", "foreign_key_2": 3},
    ]
    unexpected_index_list = [1, 3]
    assert _format_map_output(
        result_format={
            "result_format": "COMPLETE",
            "partial_unexpected_count": 20,
            "include_unexpected_rows": False,
            "exclude_unexpected_values": True,
        },
        success=success,
        element_count=element_count,
        nonnull_count=nonnull_count,
        unexpected_count=len(unexpected_list),
        unexpected_list=unexpected_list,
        unexpected_index_list=unexpected_index_list,
    ) == {
        "success": False,
        "result": {
            "element_count": 5,
            "missing_count": 0,
            "missing_percent": 0.0,
            "unexpected_count": 3,
            "unexpected_percent": 60.0,
            "unexpected_percent_total": 60.0,
            "unexpected_percent_nonmissing": 60.0,
            "partial_unexpected_index_list": [1, 3],
            "unexpected_index_list": [1, 3],
        },
    }


class TestBooleanOnlyWithReturnUnexpectedIndexQuery:
    """Tests for BOOLEAN_ONLY format with return_unexpected_index_query."""

    def test_boolean_only_with_return_unexpected_index_query_includes_query(self):
        """BOOLEAN_ONLY with return_unexpected_index_query=True should include the query."""
        result = _format_map_output(
            result_format={
                "result_format": "BOOLEAN_ONLY",
                "return_unexpected_index_query": True,
                "partial_unexpected_count": 0,
            },
            success=False,
            element_count=5,
            nonnull_count=5,
            unexpected_count=2,
            unexpected_index_query="SELECT * FROM table WHERE condition",
        )

        assert result["success"] is False
        assert "result" in result
        assert result["result"]["unexpected_index_query"] == "SELECT * FROM table WHERE condition"

    def test_boolean_only_with_return_unexpected_index_query_includes_column_names(self):
        """BOOLEAN_ONLY with return_unexpected_index_query=True should include column names."""
        result = _format_map_output(
            result_format={
                "result_format": "BOOLEAN_ONLY",
                "return_unexpected_index_query": True,
                "unexpected_index_column_names": ["pk_1", "pk_2"],
                "partial_unexpected_count": 0,
            },
            success=False,
            element_count=5,
            nonnull_count=5,
            unexpected_count=2,
            unexpected_index_query="SELECT pk_1, pk_2 FROM table WHERE condition",
            unexpected_index_column_names=["pk_1", "pk_2"],
        )

        assert result["success"] is False
        assert "result" in result
        assert (
            result["result"]["unexpected_index_query"]
            == "SELECT pk_1, pk_2 FROM table WHERE condition"
        )
        assert result["result"]["unexpected_index_column_names"] == ["pk_1", "pk_2"]

    def test_boolean_only_without_return_unexpected_index_query_is_empty(self):
        """BOOLEAN_ONLY without return_unexpected_index_query should return empty result.

        This test verifies backwards compatibility.
        """
        result = _format_map_output(
            result_format={
                "result_format": "BOOLEAN_ONLY",
                "partial_unexpected_count": 20,
            },
            success=False,
            element_count=5,
            nonnull_count=5,
            unexpected_count=2,
            unexpected_index_query="SELECT * FROM table WHERE condition",
        )

        assert result == {"success": False}

    def test_boolean_only_with_return_unexpected_index_query_false_is_empty(self):
        """BOOLEAN_ONLY with return_unexpected_index_query=False should return empty result."""
        result = _format_map_output(
            result_format={
                "result_format": "BOOLEAN_ONLY",
                "return_unexpected_index_query": False,
                "partial_unexpected_count": 0,
            },
            success=False,
            element_count=5,
            nonnull_count=5,
            unexpected_count=2,
            unexpected_index_query="SELECT * FROM table WHERE condition",
        )

        assert result == {"success": False}

    def test_boolean_only_with_return_unexpected_index_query_but_no_query(self):
        """BOOLEAN_ONLY with return_unexpected_index_query=True but no query.

        Should return empty result.
        """
        result = _format_map_output(
            result_format={
                "result_format": "BOOLEAN_ONLY",
                "return_unexpected_index_query": True,
                "partial_unexpected_count": 0,
            },
            success=True,
            element_count=5,
            nonnull_count=5,
            unexpected_count=0,
            unexpected_index_query=None,
        )

        assert result == {"success": True}


class TestBasicWithReturnUnexpectedIndexQuery:
    """Tests for BASIC format with return_unexpected_index_query."""

    def test_basic_with_return_unexpected_index_query_includes_query(self):
        """BASIC with return_unexpected_index_query=True should include the query."""
        result = _format_map_output(
            result_format={
                "result_format": "BASIC",
                "return_unexpected_index_query": True,
                "partial_unexpected_count": 25,
                "include_unexpected_rows": False,
            },
            success=False,
            element_count=5,
            nonnull_count=5,
            unexpected_count=2,
            unexpected_list=["d", "e"],
            unexpected_index_query="SELECT * FROM table WHERE condition",
        )

        assert result["success"] is False
        assert "result" in result
        assert result["result"]["unexpected_index_query"] == "SELECT * FROM table WHERE condition"
        # BASIC should also have standard fields
        assert result["result"]["element_count"] == 5
        assert result["result"]["unexpected_count"] == 2

    def test_basic_without_return_unexpected_index_query_excludes_query(self):
        """BASIC without return_unexpected_index_query should NOT include the query.

        This test verifies backwards compatibility.
        """
        result = _format_map_output(
            result_format={
                "result_format": "BASIC",
                "partial_unexpected_count": 25,
                "include_unexpected_rows": False,
            },
            success=False,
            element_count=5,
            nonnull_count=5,
            unexpected_count=2,
            unexpected_list=["d", "e"],
            unexpected_index_query="SELECT * FROM table WHERE condition",
        )

        assert result["success"] is False
        assert "result" in result
        assert "unexpected_index_query" not in result["result"]
        # But should still have standard BASIC fields
        assert result["result"]["element_count"] == 5
        assert result["result"]["unexpected_count"] == 2

    def test_basic_with_return_unexpected_index_query_false_excludes_query(self):
        """BASIC with return_unexpected_index_query=False should NOT include the query."""
        result = _format_map_output(
            result_format={
                "result_format": "BASIC",
                "return_unexpected_index_query": False,
                "partial_unexpected_count": 25,
                "include_unexpected_rows": False,
            },
            success=False,
            element_count=5,
            nonnull_count=5,
            unexpected_count=2,
            unexpected_list=["d", "e"],
            unexpected_index_query="SELECT * FROM table WHERE condition",
        )

        assert "unexpected_index_query" not in result["result"]


# Tests for the helper function _add_unexpected_index_query_to_result
class TestAddUnexpectedIndexQueryToResult:
    """Tests for the _add_unexpected_index_query_to_result helper function."""

    def test_adds_query_when_requested(self):
        """Should add query when return_unexpected_index_query is True."""
        return_obj = {"success": False}
        _add_unexpected_index_query_to_result(
            return_obj=return_obj,
            result_format={"return_unexpected_index_query": True},
            unexpected_index_query="SELECT * FROM table",
            unexpected_index_column_names=None,
        )

        assert "result" in return_obj
        assert return_obj["result"]["unexpected_index_query"] == "SELECT * FROM table"

    def test_adds_column_names_when_not_present(self):
        """Should add unexpected_index_column_names when not already in result."""
        return_obj = {"success": False}
        _add_unexpected_index_query_to_result(
            return_obj=return_obj,
            result_format={"return_unexpected_index_query": True},
            unexpected_index_query="SELECT * FROM table",
            unexpected_index_column_names=["pk_1"],
        )

        assert return_obj["result"]["unexpected_index_column_names"] == ["pk_1"]

    def test_does_not_overwrite_existing_column_names(self):
        """Should not overwrite unexpected_index_column_names if already present."""
        return_obj = {
            "success": False,
            "result": {"unexpected_index_column_names": ["existing_col"]},
        }
        _add_unexpected_index_query_to_result(
            return_obj=return_obj,
            result_format={"return_unexpected_index_query": True},
            unexpected_index_query="SELECT * FROM table",
            unexpected_index_column_names=["new_col"],
        )

        # Should keep the existing column names
        assert return_obj["result"]["unexpected_index_column_names"] == ["existing_col"]
        # But should still add the query
        assert return_obj["result"]["unexpected_index_query"] == "SELECT * FROM table"

    def test_does_nothing_when_query_is_none(self):
        """Should do nothing when unexpected_index_query is None."""
        return_obj = {"success": True}
        _add_unexpected_index_query_to_result(
            return_obj=return_obj,
            result_format={"return_unexpected_index_query": True},
            unexpected_index_query=None,
            unexpected_index_column_names=["pk_1"],
        )

        assert "result" not in return_obj

    def test_does_nothing_when_return_flag_is_false(self):
        """Should do nothing when return_unexpected_index_query is False."""
        return_obj = {"success": False}
        _add_unexpected_index_query_to_result(
            return_obj=return_obj,
            result_format={"return_unexpected_index_query": False},
            unexpected_index_query="SELECT * FROM table",
            unexpected_index_column_names=["pk_1"],
        )

        assert "result" not in return_obj

    def test_does_nothing_when_return_flag_is_missing(self):
        """Should do nothing when return_unexpected_index_query is not in result_format."""
        return_obj = {"success": False}
        _add_unexpected_index_query_to_result(
            return_obj=return_obj,
            result_format={},
            unexpected_index_query="SELECT * FROM table",
            unexpected_index_column_names=["pk_1"],
        )

        assert "result" not in return_obj
