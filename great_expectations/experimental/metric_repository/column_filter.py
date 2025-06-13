from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from great_expectations.core.domain import SemanticDomainTypes
from great_expectations.core.profiler_types_mapping import ProfilerTypeMapping
from great_expectations.validator.metric_configuration import MetricConfiguration

if TYPE_CHECKING:
    from great_expectations.validator.validator import Validator


class ColumnFilter:
    """
    A utility class for filtering table columns based on semantic types and other criteria.

    This class provides functionality to filter columns by:
    - Semantic types (numeric, datetime, text, etc.)
    - Column name inclusion/exclusion lists
    - Column name suffixes
    """

    def __init__(  # noqa: PLR0913
        self,
        include_column_names: Optional[List[str]] = None,
        exclude_column_names: Optional[List[str]] = None,
        include_column_name_suffixes: Optional[List[str]] = None,
        exclude_column_name_suffixes: Optional[List[str]] = None,
        include_semantic_types: Optional[
            Union[SemanticDomainTypes, List[SemanticDomainTypes]]
        ] = None,
        exclude_semantic_types: Optional[
            Union[SemanticDomainTypes, List[SemanticDomainTypes]]
        ] = None,
    ) -> None:
        """
        Initialize the ColumnFilter.

        Args:
            include_column_names: Specify columns to include in filter.
            exclude_column_names: Specify columns to exclude from filter.
            include_column_name_suffixes: Specify columns to include by matching suffix.
            exclude_column_name_suffixes: Specify columns to exclude by matching suffix.
            include_semantic_types: Semantic types to include.
            exclude_semantic_types: Semantic types to exclude.
        """
        self._include_column_names = include_column_names or []
        self._exclude_column_names = exclude_column_names or []
        self._include_column_name_suffixes = include_column_name_suffixes or []
        self._exclude_column_name_suffixes = exclude_column_name_suffixes or []

        # Normalize semantic types to lists
        self._include_semantic_types = self._normalize_semantic_types(include_semantic_types)
        self._exclude_semantic_types = self._normalize_semantic_types(exclude_semantic_types)

    def _normalize_semantic_types(
        self, semantic_types: Optional[Union[SemanticDomainTypes, List[SemanticDomainTypes]]]
    ) -> List[SemanticDomainTypes]:
        """Convert semantic types to a normalized list format."""
        if semantic_types is None:
            return []
        if isinstance(semantic_types, SemanticDomainTypes):
            return [semantic_types]
        return semantic_types

    def get_filtered_column_names(
        self,
        validator: Validator,
    ) -> List[str]:
        """
        Get column names filtered by the specified criteria.

        Args:
            validator: The validator containing the batch data.

        Returns:
            List of filtered column names.
        """
        # Get all column names from the table
        all_column_names = self._get_table_column_names(validator)

        # Apply column name filtering
        filtered_columns = self._apply_column_name_filters(all_column_names)

        # Apply semantic type filtering if specified
        if self._include_semantic_types or self._exclude_semantic_types:
            semantic_type_map = self._build_semantic_type_map(validator, filtered_columns)
            filtered_columns = self._apply_semantic_type_filters(
                filtered_columns, semantic_type_map
            )

        return filtered_columns

    def _get_table_column_names(self, validator: Validator) -> List[str]:
        """Get all column names from the table."""
        return validator.get_metric(
            metric=MetricConfiguration(
                metric_name="table.columns",
                metric_domain_kwargs={
                    "batch_id": validator.active_batch_id,
                },
                metric_value_kwargs={
                    "include_nested": True,
                },
            )
        )

    def _apply_column_name_filters(self, column_names: List[str]) -> List[str]:
        """Apply include/exclude column name and suffix filters."""
        filtered_columns = column_names[:]

        # Apply include column names filter
        if self._include_column_names:
            filtered_columns = [
                col for col in filtered_columns if col in self._include_column_names
            ]

        # Apply exclude column names filter
        if self._exclude_column_names:
            filtered_columns = [
                col for col in filtered_columns if col not in self._exclude_column_names
            ]

        # Apply include column name suffixes filter
        if self._include_column_name_suffixes:
            filtered_columns = [
                col
                for col in filtered_columns
                if any(col.endswith(suffix) for suffix in self._include_column_name_suffixes)
            ]

        # Apply exclude column name suffixes filter
        if self._exclude_column_name_suffixes:
            filtered_columns = [
                col
                for col in filtered_columns
                if not any(col.endswith(suffix) for suffix in self._exclude_column_name_suffixes)
            ]

        return filtered_columns

    def _build_semantic_type_map(
        self, validator: Validator, column_names: List[str]
    ) -> Dict[str, SemanticDomainTypes]:
        """Build a mapping from column names to their inferred semantic types."""
        column_types_dict_list: List[Dict[str, Any]] = validator.get_metric(
            metric=MetricConfiguration(
                metric_name="table.column_types",
                metric_domain_kwargs={
                    "batch_id": validator.active_batch_id,
                },
                metric_value_kwargs={
                    "include_nested": True,
                },
            )
        )

        semantic_type_map = {}
        for column_name in column_names:
            semantic_type = self._infer_semantic_type_from_column_type(
                column_types_dict_list, column_name
            )
            semantic_type_map[column_name] = semantic_type

        return semantic_type_map

    def _infer_semantic_type_from_column_type(
        self, column_types_dict_list: List[Dict[str, Any]], column_name: str
    ) -> SemanticDomainTypes:
        """Infer semantic type from column type information."""
        column_type_info = self._find_column_type_info(column_types_dict_list, column_name)
        if not column_type_info:
            return SemanticDomainTypes.UNKNOWN

        column_type = str(column_type_info["type"]).upper()
        return self._map_column_type_to_semantic_type(column_type)

    def _find_column_type_info(
        self, column_types_dict_list: List[Dict[str, Any]], column_name: str
    ) -> Optional[Dict[str, Any]]:
        """Find column type information for the given column name."""
        for col_info in column_types_dict_list:
            if (
                col_info["name"] == column_name or col_info["name"].strip("`") == column_name
            ):  # Spark specific fix
                return col_info if "type" in col_info else None
        return None

    def _map_column_type_to_semantic_type(self, column_type: str) -> SemanticDomainTypes:
        """Map column type to semantic type."""
        # Check numeric types
        if self._is_numeric_type(column_type):
            return SemanticDomainTypes.NUMERIC

        # Check other types
        type_mappings = [
            (ProfilerTypeMapping.STRING_TYPE_NAMES, SemanticDomainTypes.TEXT),
            (ProfilerTypeMapping.BOOLEAN_TYPE_NAMES, SemanticDomainTypes.LOGIC),
            (ProfilerTypeMapping.BINARY_TYPE_NAMES, SemanticDomainTypes.BINARY),
            (ProfilerTypeMapping.CURRENCY_TYPE_NAMES, SemanticDomainTypes.CURRENCY),
            (ProfilerTypeMapping.IDENTIFIER_TYPE_NAMES, SemanticDomainTypes.IDENTIFIER),
        ]

        for type_names, semantic_type in type_mappings:
            if column_type in {type_name.upper() for type_name in type_names}:
                return semantic_type

        # Check datetime types (with prefix matching)
        if any(
            column_type.startswith(type_name.upper())
            for type_name in ProfilerTypeMapping.DATETIME_TYPE_NAMES
        ):
            return SemanticDomainTypes.DATETIME

        # Check miscellaneous types
        if self._is_miscellaneous_type(column_type):
            return SemanticDomainTypes.MISCELLANEOUS

        return SemanticDomainTypes.UNKNOWN

    def _is_numeric_type(self, column_type: str) -> bool:
        """Check if column type is numeric."""
        numeric_types = ProfilerTypeMapping.INT_TYPE_NAMES + ProfilerTypeMapping.FLOAT_TYPE_NAMES
        return any(column_type.startswith(type_name.upper()) for type_name in numeric_types)

    def _is_miscellaneous_type(self, column_type: str) -> bool:
        """Check if column type is miscellaneous."""
        misc_types = {
            type_name.upper() for type_name in ProfilerTypeMapping.MISCELLANEOUS_TYPE_NAMES
        } | {type_name.upper() for type_name in ProfilerTypeMapping.RECORD_TYPE_NAMES}
        return column_type in misc_types

    def _apply_semantic_type_filters(
        self, column_names: List[str], semantic_type_map: Dict[str, SemanticDomainTypes]
    ) -> List[str]:
        """Apply semantic type include/exclude filters."""
        filtered_columns = column_names[:]

        # Apply include semantic types filter
        if self._include_semantic_types:
            filtered_columns = [
                col
                for col in filtered_columns
                if semantic_type_map.get(col) in self._include_semantic_types
            ]

        # Apply exclude semantic types filter
        if self._exclude_semantic_types:
            filtered_columns = [
                col
                for col in filtered_columns
                if semantic_type_map.get(col) not in self._exclude_semantic_types
            ]

        return filtered_columns
