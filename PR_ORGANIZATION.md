# PR Organization Guide

This document outlines the three separate PRs for optimizing the distinct values expectations.

## PR 1: `m/gx-2374/distinct-values-be-in-set`

### Files to Modify:
1. **`great_expectations/expectations/metrics/column_aggregate_metrics/column_distinct_values.py`**
   - Add `ColumnDistinctValuesNotInSetCount` class (lines 191-237)
   - Add `ColumnDistinctValuesNotInSet` class (lines 240-330)

2. **`great_expectations/expectations/metrics/column_aggregate_metrics/__init__.py`**
   - Add imports:
     ```python
     ColumnDistinctValuesNotInSet,
     ColumnDistinctValuesNotInSetCount,
     ```

3. **`great_expectations/expectations/core/expect_column_distinct_values_to_be_in_set.py`**
   - Update imports (add ValidationDependencies, MetricConfiguration, get_metric_kwargs, parse_result_format)
   - Change `metric_dependencies` to use new metrics
   - Add `get_validation_dependencies` override method
   - Update `_validate` method

4. **`great_expectations/metrics/column/distinct_values_not_in_set_count.py`**
   - Create new file with Metrics API wrapper

5. **`great_expectations/metrics/column/distinct_values_not_in_set.py`**
   - Create new file with Metrics API wrapper

6. **`great_expectations/metrics/__init__.py`**
   - Add imports:
     ```python
     from .column.distinct_values_not_in_set import ColumnDistinctValuesNotInSet
     from .column.distinct_values_not_in_set_count import ColumnDistinctValuesNotInSetCount
     ```

---

## PR 2: `m/gx-2374/distinct-values-contain-set`

### Files to Modify:
1. **`great_expectations/expectations/metrics/column_aggregate_metrics/column_distinct_values.py`**
   - Add `ColumnDistinctValuesMissingFromSet` class (lines 333-426)

2. **`great_expectations/expectations/metrics/column_aggregate_metrics/__init__.py`**
   - Add import:
     ```python
     ColumnDistinctValuesMissingFromSet,
     ```

3. **`great_expectations/expectations/core/expect_column_distinct_values_to_contain_set.py`**
   - Update imports (add ValidationDependencies, MetricConfiguration, get_metric_kwargs, parse_result_format)
   - Change `metric_dependencies` to use new metric
   - Add `get_validation_dependencies` override method
   - Update `_validate` method

4. **`great_expectations/metrics/column/distinct_values_missing_from_set.py`**
   - Create new file with Metrics API wrapper

5. **`great_expectations/metrics/__init__.py`**
   - Add import:
     ```python
     from .column.distinct_values_missing_from_set import ColumnDistinctValuesMissingFromSet
     ```

---

## PR 3: `m/gx-2374/distinct-values-equal-set`

### Files to Modify:
1. **`great_expectations/expectations/metrics/column_aggregate_metrics/column_distinct_values.py`**
   - Add `ColumnDistinctValuesNotEqualSet` class (lines 429-541)

2. **`great_expectations/expectations/metrics/column_aggregate_metrics/__init__.py`**
   - Add import:
     ```python
     ColumnDistinctValuesNotEqualSet,
     ```

3. **`great_expectations/expectations/core/expect_column_distinct_values_to_equal_set.py`**
   - Update imports (add ValidationDependencies, MetricConfiguration, get_metric_kwargs, parse_result_format)
   - Change `metric_dependencies` to use new metric
   - Add `get_validation_dependencies` override method
   - Update `_validate` method

4. **`great_expectations/metrics/column/distinct_values_not_equal_set.py`**
   - Create new file with Metrics API wrapper

5. **`great_expectations/metrics/__init__.py`**
   - Add import:
     ```python
     from .column.distinct_values_not_equal_set import ColumnDistinctValuesNotEqualSet
     ```

---

## Notes:
- Each PR is independent and can be reviewed/merged separately
- Tests will be added in follow-up PRs after all three are merged
- The Metrics API wrapper classes follow the same pattern as existing metrics
- All changes maintain backwards compatibility (column.value_counts remains unchanged)
