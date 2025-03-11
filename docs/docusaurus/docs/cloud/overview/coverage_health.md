---
title: 'Coverage health'
description: Understand what you're testing and how often for a more holistic perspective on data health. 
---

To understand data health, you need to know more than just whether tests are passing or failing. You also need to know what you're testing and how often. 

## Coverage health metrics
To help you have a better understanding of data health, GX Cloud provides the following coverage health metrics on the **Data Assets** page:

![Example metrics: Active Coverage 75% warning add Expectations, Active Data Assets 100%, schema 75% warning add Expectations, volume 100%, completeness 50% warning add Expectations.](/img/coverage_health.png)

- **Active Coverage:** The percentage of Data Assets that have been validated in the last 30 days with an Expectation for schema, volume, or completeness. This is calculated as:
   
   ```markup title="Formula"
   ((% of Data Assets validated for schema) +
    (% of Data Assets validated for volume) +
    (% of Data Assets validated for completeness))
   / 3
   ```

- **Active Data Assets:** The percentage of Data Assets that have had any Validations in the last 30 days. This metric does not consider what kinds of Expectations have been validated. 
- **Coverage** for the following data quality issues. Note that these metrics consider only whether or not Expectations exist. The following metrics do not consider whether the Expectations have been validated. 
   - **Schema:** The percentage of Data Assets that have at least one schema-focused Expectation. This includes the following Expectations:
      - [ExpectColumnToExist](https://greatexpectations.io/expectations/expect_column_to_exist/)
      - [ExpectColumnValuesToBeInTypeList](https://greatexpectations.io/expectations/expect_column_values_to_be_in_type_list/)
      - [ExpectColumnValuesToBeOfType](https://greatexpectations.io/expectations/expect_column_values_to_be_of_type/)
      - [ExpectTableColumnCountToBeBetween](https://greatexpectations.io/expectations/expect_table_column_count_to_be_between/)
      - [ExpectTableColumnCountToEqual](https://greatexpectations.io/expectations/expect_table_column_count_to_equal/)
      - [ExpectTableColumnsToMatchOrderedList](https://greatexpectations.io/expectations/expect_table_columns_to_match_ordered_list/)
      - [ExpectTableColumnsToMatchSet](https://greatexpectations.io/expectations/expect_table_columns_to_match_set/)
   - **Volume:** The percentage of Data Assets that have at least one volume-focused Expectation. This includes the following Expectations:
      - [ExpectTableRowCountToBeBetween](https://greatexpectations.io/expectations/expect_table_row_count_to_be_between/)
      - [ExpectTableRowCountToEqual](https://greatexpectations.io/expectations/expect_table_row_count_to_equal/)
      - [ExpectTableRowCountToEqualOtherTable](https://greatexpectations.io/expectations/expect_table_row_count_to_equal_other_table/)
   - **Completeness:** The percentage of Data Assets that have at least one completeness-focused Expectation. This includes the following Expectations:  
      - [ExpectColumnValuesToBeNull](https://greatexpectations.io/expectations/expect_column_values_to_be_null/)
      - [ExpectColumnValuesToNotBeNull](https://greatexpectations.io/expectations/expect_column_values_to_not_be_null/)

Only current Data Assets are considered in coverage health metrics. Deleted Data Assets are excluded from the calculations even if they've had Validations within the last 30 days. 


## Next steps
- If **Active Data Assets** are low, [schedule recurring Validations](/cloud/schedules/manage_schedules.md).
- If **Schema**, **Volume**, or **Completeness** coverage is low, [add Expectations](/cloud/expectations/manage_expectations.md#add-an-expectation).
- When adding new Data Assets, [automate standard data quality rules](/cloud/overview/automating_rules.md).

