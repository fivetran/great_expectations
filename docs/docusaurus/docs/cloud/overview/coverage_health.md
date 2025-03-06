---
title: 'Coverage health'
description: Understand what you're testing and how often for a more holistic perspective on data health. 
---

To understand data health, you need to know more than just whether tests are passing or failing - you also need to understand what you're testing and how often. 

## Coverage health metrics
To help you have a better understanding of data health, GX provides the following coverage health metrics on the **Data Assets** page:

- **Active Coverage:** The percentage of Data Assets that have been validated in the last 30 days with an Expectation for volume, schema, or completeness. This is calculated as ((% of Assets validated for volume) + (% of Assets validated for schema) + (% of Assets validated for completeness)) / 3. 
- **Active Assets:** The percentage of Data Assets that have had any Validations in the last 30 days. All kinds of Validations count including scheduled validations, manual validations, and API-orchestrated validiations. This metric does not consider what kinds of Expectations have been validated. 
- Coverage for the following data quality issues: 
   - **Volume:** The percentage of Data Assets that have at least one volume-focused Expectation. This includes the following Expectations:
      - [ExpectTableRowCountToBeBetween](https://greatexpectations.io/expectations/expect_table_row_count_to_be_between/)
      - [ExpectTableRowCountToEqual](https://greatexpectations.io/expectations/expect_table_row_count_to_equal/)
      - [ExpectTableRowCountToEqualOtherTable](https://greatexpectations.io/expectations/expect_table_row_count_to_equal_other_table/)
   - **Schema:** The percentage of Data Assets that have at least one schema-focused Expectation. This includes the following Expectations:
      - [ExpectColumnToExist](https://greatexpectations.io/expectations/expect_column_to_exist/)
      - [ExpectColumnValuesToBeInTypeList](https://greatexpectations.io/expectations/expect_column_values_to_be_in_type_list/)
      - [ExpectColumnValuesToBeOfType](https://greatexpectations.io/expectations/expect_column_values_to_be_of_type/)
      - [ExpectTableColumnCountToBeBetween](https://greatexpectations.io/expectations/expect_table_column_count_to_be_between/)
      - [ExpectTableColumnCountToEqual](https://greatexpectations.io/expectations/expect_table_column_count_to_equal/)
      - [ExpectTableColumnsToMatchOrderedList](https://greatexpectations.io/expectations/expect_table_columns_to_match_ordered_list/)
      - [ExpectTableColumnsToMatchSet](https://greatexpectations.io/expectations/expect_table_columns_to_match_set/)
   - **Completeness:** The percentage of Data Assets that have at least one completeness-focused Expectation. This includes the following Expectations:  
      - [ExpectColumnValuesToBeNull](https://greatexpectations.io/expectations/expect_column_values_to_be_null/)
      - [ExpectColumnValuesToNotBeNull](https://greatexpectations.io/expectations/expect_column_values_to_not_be_null/)
   Note that the **Volume**, **Schema**, and **Completeness** metrics consider only whether or not Expectations exist. These particular metrics do not consider whether the Expectations have been validated. 

Only current Data Assets are considered in these metrics. Any Assets that have been deleted are excluded in the calculations even if they've had Validations within the last 30 days. 

![Example metrics: Active Assets 100%, Active Coverage 58% warning run validations, volume 100%, schema 75% warning add Expectations, completeness 50% warning add Expectations.](/img/coverage_health.png)

## Next steps
- If **Active Assets** are low, [schedule recurring Validations](/cloud/schedules/manage_schedules.md).
- If **Volume**, **Schema**, or **Completeness** coverage is low, [add Expectations](/cloud/expectations/manage_expectations.md#add-an-expectation).
- When adding new Data Assets, automate [standard data quality rules](/cloud/overview/automating_rules.md).

