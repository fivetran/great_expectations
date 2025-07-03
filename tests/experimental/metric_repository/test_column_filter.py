from __future__ import annotations

import pytest

from great_expectations.core.domain import SemanticDomainTypes
from great_expectations.experimental.metric_repository.column_filter import ColumnFilter
from great_expectations.validator.validator import Validator


@pytest.fixture
def mock_validator(mocker):
    """Create a mock validator for testing."""
    validator = mocker.Mock(spec=Validator)
    validator.active_batch_id = "test_batch_id"
    return validator


@pytest.fixture
def sample_column_names():
    """Sample column names for testing."""
    return ["id", "name", "age", "salary", "created_at", "is_active", "description"]


@pytest.fixture
def sample_column_types():
    """Sample column type information for testing."""
    return [
        {"name": "id", "type": "INTEGER"},
        {"name": "name", "type": "VARCHAR"},
        {"name": "age", "type": "INTEGER"},
        {"name": "salary", "type": "DECIMAL"},
        {"name": "created_at", "type": "TIMESTAMP"},
        {"name": "is_active", "type": "BOOLEAN"},
        {"name": "description", "type": "TEXT"},
    ]


class TestColumnFilter:
    """Test cases for ColumnFilter class."""

    @pytest.mark.unit
    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        column_filter = ColumnFilter()
        assert column_filter._include_column_names == []
        assert column_filter._exclude_column_names == []
        assert column_filter._include_column_name_suffixes == []
        assert column_filter._exclude_column_name_suffixes == []
        assert column_filter._include_semantic_types == []
        assert column_filter._exclude_semantic_types == []

    @pytest.mark.unit
    def test_init_with_parameters(self):
        """Test initialization with specific parameters."""
        column_filter = ColumnFilter(
            include_column_names=["col1", "col2"],
            exclude_column_names=["col3"],
            include_semantic_types=[SemanticDomainTypes.NUMERIC],
            exclude_semantic_types=[SemanticDomainTypes.TEXT],
        )
        assert column_filter._include_column_names == ["col1", "col2"]
        assert column_filter._exclude_column_names == ["col3"]
        assert column_filter._include_semantic_types == [SemanticDomainTypes.NUMERIC]
        assert column_filter._exclude_semantic_types == [SemanticDomainTypes.TEXT]

    @pytest.mark.unit
    def test_normalize_semantic_types_none(self):
        """Test semantic type normalization with None."""
        column_filter = ColumnFilter()
        result = column_filter._normalize_semantic_types(None)
        assert result == []

    @pytest.mark.unit
    def test_normalize_semantic_types_single(self):
        """Test semantic type normalization with single type."""
        column_filter = ColumnFilter()
        result = column_filter._normalize_semantic_types(SemanticDomainTypes.NUMERIC)
        assert result == [SemanticDomainTypes.NUMERIC]

    @pytest.mark.unit
    def test_normalize_semantic_types_list(self):
        """Test semantic type normalization with list."""
        column_filter = ColumnFilter()
        types = [SemanticDomainTypes.NUMERIC, SemanticDomainTypes.TEXT]
        result = column_filter._normalize_semantic_types(types)
        assert result == types

    @pytest.mark.unit
    def test_get_table_column_names(self, mock_validator, sample_column_names):
        """Test getting table column names."""
        mock_validator.get_metric.return_value = sample_column_names

        column_filter = ColumnFilter()
        result = column_filter._get_table_column_names(mock_validator)

        assert result == sample_column_names
        mock_validator.get_metric.assert_called_once()

    @pytest.mark.unit
    def test_apply_column_name_filters_no_filters(self, sample_column_names):
        """Test column name filtering with no filters applied."""
        column_filter = ColumnFilter()
        result = column_filter._apply_column_name_filters(sample_column_names)
        assert result == sample_column_names

    @pytest.mark.unit
    def test_apply_column_name_filters_include_names(self, sample_column_names):
        """Test column name filtering with include names."""
        column_filter = ColumnFilter(include_column_names=["id", "name"])
        result = column_filter._apply_column_name_filters(sample_column_names)
        assert result == ["id", "name"]

    @pytest.mark.unit
    def test_apply_column_name_filters_exclude_names(self, sample_column_names):
        """Test column name filtering with exclude names."""
        column_filter = ColumnFilter(exclude_column_names=["id", "description"])
        result = column_filter._apply_column_name_filters(sample_column_names)
        expected = ["name", "age", "salary", "created_at", "is_active"]
        assert result == expected

    @pytest.mark.unit
    def test_apply_column_name_filters_include_suffixes(self, sample_column_names):
        """Test column name filtering with include suffixes."""
        column_filter = ColumnFilter(include_column_name_suffixes=["_at", "age"])
        result = column_filter._apply_column_name_filters(sample_column_names)
        assert result == ["age", "created_at"]

    @pytest.mark.unit
    def test_apply_column_name_filters_exclude_suffixes(self, sample_column_names):
        """Test column name filtering with exclude suffixes."""
        column_filter = ColumnFilter(exclude_column_name_suffixes=["_at", "ion"])
        result = column_filter._apply_column_name_filters(sample_column_names)
        expected = ["id", "name", "age", "salary", "is_active"]
        assert result == expected

    @pytest.mark.unit
    def test_infer_semantic_type_numeric_integer(self, sample_column_types):
        """Test semantic type inference for integer columns."""
        column_filter = ColumnFilter()
        result = column_filter._infer_semantic_type_from_column_type(sample_column_types, "id")
        assert result == SemanticDomainTypes.NUMERIC

    @pytest.mark.unit
    def test_infer_semantic_type_numeric_decimal(self, sample_column_types):
        """Test semantic type inference for decimal columns."""
        column_filter = ColumnFilter()
        result = column_filter._infer_semantic_type_from_column_type(sample_column_types, "salary")
        assert result == SemanticDomainTypes.NUMERIC

    @pytest.mark.unit
    def test_infer_semantic_type_text(self, sample_column_types):
        """Test semantic type inference for text columns."""
        column_filter = ColumnFilter()
        result = column_filter._infer_semantic_type_from_column_type(sample_column_types, "name")
        assert result == SemanticDomainTypes.TEXT

    @pytest.mark.unit
    def test_infer_semantic_type_datetime(self, sample_column_types):
        """Test semantic type inference for datetime columns."""
        column_filter = ColumnFilter()
        result = column_filter._infer_semantic_type_from_column_type(
            sample_column_types, "created_at"
        )
        assert result == SemanticDomainTypes.DATETIME

    @pytest.mark.unit
    def test_infer_semantic_type_boolean(self, sample_column_types):
        """Test semantic type inference for boolean columns."""
        column_filter = ColumnFilter()
        result = column_filter._infer_semantic_type_from_column_type(
            sample_column_types, "is_active"
        )
        assert result == SemanticDomainTypes.LOGIC

    @pytest.mark.unit
    def test_infer_semantic_type_unknown(self, sample_column_types):
        """Test semantic type inference for unknown columns."""
        column_filter = ColumnFilter()
        result = column_filter._infer_semantic_type_from_column_type(
            sample_column_types, "nonexistent"
        )
        assert result == SemanticDomainTypes.UNKNOWN

    @pytest.mark.unit
    def test_infer_semantic_type_spark_backticks(self):
        """Test semantic type inference with Spark backtick column names."""
        column_types = [{"name": "`column_name`", "type": "INTEGER"}]
        column_filter = ColumnFilter()
        result = column_filter._infer_semantic_type_from_column_type(column_types, "column_name")
        assert result == SemanticDomainTypes.NUMERIC

    @pytest.mark.unit
    def test_build_semantic_type_map(self, mock_validator, sample_column_types):
        """Test building semantic type map."""
        mock_validator.get_metric.return_value = sample_column_types

        column_filter = ColumnFilter()
        column_names = ["id", "name", "created_at"]
        result = column_filter._build_semantic_type_map(mock_validator, column_names)

        expected = {
            "id": SemanticDomainTypes.NUMERIC,
            "name": SemanticDomainTypes.TEXT,
            "created_at": SemanticDomainTypes.DATETIME,
        }
        assert result == expected

    @pytest.mark.unit
    def test_apply_semantic_type_filters_include(self):
        """Test semantic type filtering with include types."""
        column_filter = ColumnFilter(include_semantic_types=[SemanticDomainTypes.NUMERIC])
        column_names = ["id", "name", "age"]
        semantic_type_map = {
            "id": SemanticDomainTypes.NUMERIC,
            "name": SemanticDomainTypes.TEXT,
            "age": SemanticDomainTypes.NUMERIC,
        }

        result = column_filter._apply_semantic_type_filters(column_names, semantic_type_map)
        assert result == ["id", "age"]

    @pytest.mark.unit
    def test_apply_semantic_type_filters_exclude(self):
        """Test semantic type filtering with exclude types."""
        column_filter = ColumnFilter(exclude_semantic_types=[SemanticDomainTypes.TEXT])
        column_names = ["id", "name", "age"]
        semantic_type_map = {
            "id": SemanticDomainTypes.NUMERIC,
            "name": SemanticDomainTypes.TEXT,
            "age": SemanticDomainTypes.NUMERIC,
        }

        result = column_filter._apply_semantic_type_filters(column_names, semantic_type_map)
        assert result == ["id", "age"]

    @pytest.mark.unit
    def test_get_filtered_column_names_no_semantic_filtering(
        self, mock_validator, sample_column_names
    ):
        """Test getting filtered column names without semantic filtering."""
        mock_validator.get_metric.return_value = sample_column_names

        column_filter = ColumnFilter(exclude_column_names=["description"])
        result = column_filter.get_filtered_column_names(mock_validator)

        expected = ["id", "name", "age", "salary", "created_at", "is_active"]
        assert result == expected

    @pytest.mark.unit
    def test_get_filtered_column_names_with_semantic_filtering(
        self, mock_validator, sample_column_names, sample_column_types
    ):
        """Test getting filtered column names with semantic filtering."""

        # Mock the validator to return column names and types
        def mock_get_metric(metric):
            if metric.metric_name == "table.columns":
                return sample_column_names
            elif metric.metric_name == "table.column_types":
                return sample_column_types
            return None

        mock_validator.get_metric.side_effect = mock_get_metric

        column_filter = ColumnFilter(
            include_semantic_types=[SemanticDomainTypes.NUMERIC], exclude_column_names=["id"]
        )
        result = column_filter.get_filtered_column_names(mock_validator)

        # Should include numeric columns (age, salary) but exclude 'id'
        expected = ["age", "salary"]
        assert result == expected

    @pytest.mark.unit
    def test_get_filtered_column_names_complex_filtering(
        self, mock_validator, sample_column_names, sample_column_types
    ):
        """Test getting filtered column names with complex filtering."""

        # Mock the validator to return column names and types
        def mock_get_metric(metric):
            if metric.metric_name == "table.columns":
                return sample_column_names
            elif metric.metric_name == "table.column_types":
                return sample_column_types
            return None

        mock_validator.get_metric.side_effect = mock_get_metric

        column_filter = ColumnFilter(
            include_semantic_types=[SemanticDomainTypes.NUMERIC, SemanticDomainTypes.TEXT],
            exclude_column_names=["description"],
            include_column_name_suffixes=["e", "y"],
        )
        result = column_filter.get_filtered_column_names(mock_validator)

        # Should include columns ending with 'e' or 'y' that are numeric or text,
        # but exclude 'description'
        # name (ends with 'e', TEXT), age (ends with 'e', NUMERIC), salary (ends with 'y', NUMERIC)
        expected = ["name", "age", "salary"]
        assert result == expected
