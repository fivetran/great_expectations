---
sidebar_label: "Expectations overview"
title: "Expectations overview"
description: Learn about Expectations - declarative, verifiable assumptions about your data.
---

An Expectation is a verifiable assertion about your data. They make implicit assumptions about your data explicit, and they provide a flexible, declarative language for describing expected behavior. They can help you better understand your data and help you improve data quality.

This page provides an overview of Expectation types and options. For instructions on working with Expectations, see [Manage Expectations](/cloud/expectations/manage_expectations.md).

## Available Expectations

The following table lists the available GX Cloud Expectations. Note that some Data Sources do not support certain Expectations. Visit the [Expectations gallery](https://greatexpectations.io/expectations/) for details.

| Data quality issue | Expectation                                            | Description                                                                                                                            | Dynamic Parameters? | Forecasted range? |
|--------------------|--------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|---------------------|-------------------|
| Completeness       | **column proportion of non-null values to be between** | Expect the proportion of non-null values to be between a minimum value and a maximum value.                                            | Yes                 | Yes               |
| Completeness       | **column values to be null**                           | Expect the column values to be null.                                                                                                   | Yes                 | No                |
| Completeness       | **column values to not be null**                       | Expect the column values to not be null.                                                                                               | Yes                 | No                |
| Multi-source       | **query results to match comparison**                  | Query multiple Data Sources and compare the results for equality.                                                                      | No                  | No                |
| Numeric            | **column KL divergence to be less than***               | Expect the Kulback-Leibler (KL) divergence (relative entropy) of the specified column with respect to the partition object to be lower than the provided threshold.         | No              | No              |
| Numeric            | **column max to be between**                           | Expect the column maximum to be between a minimum and a maximum value.                                                                 | Yes                 | No                |
| Numeric            | **column mean to be between**                          | Expect the column mean to be between a minimum and a maximum value.                                                                    | Yes                 | No                |
| Numeric            | **column median to be between**                        | Expect the column median to be between a minimum and a maximum value.                                                                  | Yes                 | No                |
| Numeric            | **column min to be between**                           | Expect the column minimum to be between a minimum value and a maximum value.                                                           | Yes                 | No                |
| Numeric            | **column pair values A to be greater than B**          | Expect the values in column A to be greater than column B.                                                                             | No                  | No                |
| Numeric            | **column quantile values to be between***               | Expect the specific provided column quantiles to be between a minimum value and a maximum value. | No | No |
| Numeric            | **column stdev to be between**                         | Expect the column standard deviation to be between a minimum value and a maximum value.                                                | Yes                 | No                |
| Numeric            | **column sum to be between**                           | Expect the column sum to be between a minimum value and a maximum value.                                                               | Yes                 | No                |
| Numeric            | **column values to be between**                        | Expect the column entries to be between a minimum value and a maximum value.                                                           | No                  | No                |
| Numeric            | **column z scores to be less than**                    | Expect the Z-scores of a column's values to be less than a given threshold.                                                            | No                  | No                |
| Numeric            | **multicolumn sum to equal**                           | Expect that the sum of row values in a specified column list is the same for each row, and equal to a specified sum total.             | No                  | No                |
| Schema             | **column to exist**                                    | Checks for the existence of a specified column within a table or view.                                                                 | No                  | No                |
| Schema             | **column values to be in type list**                   | Expect a column to contain values from a specified type list.                                                                          | No                  | No                |
| Schema             | **column values to be of type**                        | Expect a column to contain values of a specified data type.                                                                            | No                  | No                |
| Schema             | **table column count to be between**                   | Expect the number of columns in a table or view to be between two values.                                                              | Yes                 | No                |
| Schema             | **table column count to equal**                        | Expect the number of columns in a table or view to equal a value.                                                                      | No                  | No                |
| Schema             | **table columns to match ordered list**                | Expect the columns in a table or view to exactly match a specified list.                                                               | No                  | No                |
| Schema             | **table columns to match set**                         | Expect the columns in a table or view to match an unordered set.                                                                       | No                  | No                |
| SQL                | **custom Expectation with SQL**                        | Expect a SQL query to return no rows.                                                                                                  | No                  | No                |
| Uniqueness         | **column distinct values to be in set**                | Expect the set of distinct column values to be contained by a given set.                                                               | No                  | No                |
| Uniqueness         | **column distinct values to contain set**              | Expect the set of distinct column values to contain a given set.                                                                       | No                  | No                |
| Uniqueness         | **column distinct values to equal set**                | Expect the set of distinct column values to equal a given set.                                                                         | No                  | No                |
| Uniqueness         | **column proportion of unique values to be between**   | Expect the proportion of unique values to be between a minimum value and a maximum value.                                              | Yes                 | No                |
| Uniqueness         | **column unique value count to be between**            | Expect the number of unique values to be between a minimum value and a maximum value.                                                  | Yes                 | No                |
| Uniqueness         | **column values to be unique**                         | Expect each column value to be unique.                                                                                                 | No                  | No                |
| Uniqueness         | **compound columns to be unique**                      | Expect the compound columns to be unique.                                                                                              | No                  | No                |
| Uniqueness         | **select column values to be unique within record**    | Expect the values for each record to be unique across the columns listed. Note that records can be duplicated.                         | No                  | No                |
| Validity           | **column most common value to be in set**              | Expect the most common value to be within the designated value set.                                                                    | No                  | No                |
| Validity           | **column pair values to be equal**                     | Expect the values in column A to be the same as column B.                                                                              | No                  | No                |
| Validity           | **column pair values to be in set***                    | Expect the paired values from columns A and B to belong to a set of valid pairs.                                                     | No                   | No               |
| Validity           | **column value lengths to be between**                 | Expect the column entries to be strings with length between a minimum value and a maximum value.                                       | No                  | No                |
| Validity           | **column value lengths to equal**                      | Expect the column entries to be strings with length equal to the provided value.                                                       | No                  | No                |
| Validity           | **column values to be in set**                         | Expect each column value to be in a given set.                                                                                         | No                  | No                |
| Validity           | **column values to not be in set**                     | Expect column entries to not be in the set.                                                                                            | No                  | No                |
| Validity           | **column values to match like pattern**                | Expect the column entries to be strings that match a given like pattern expression.                                                    | No                  | No                |
| Validity           | **column values to match like pattern list**           | Expect the column entries to be strings that match any of a provided list of like pattern expressions.                                 | No                  | No                |
| Validity           | **column values to match regex**                       | Expect the column entries to be strings that match a given regular expression.                                                         | No                  | No                |
| Validity           | **column values to match regex list**                  | Expect the column entries to be strings that can be matched to either any of or all of a list of regular expressions.                  | No                  | No                |
| Validity           | **column values to not match like pattern**            | Expect the column entries to be strings that do NOT match a given like pattern expression.                                             | No                  | No                |
| Validity           | **column values to not match like pattern list**       | Expect the column entries to be strings that do NOT match any of a provided list of like pattern expressions.                          | No                  | No                |
| Validity           | **column values to not match regex**                   | Expect the column entries to be strings that do NOT match a given regular expression.                                                  | No                  | No                |
| Validity           | **column values to not match regex list**              | Expect the column entries to be strings that do not match any of a list of regular expressions. Matches can be anywhere in the string. | No                  | No                |
| Volume             | **table row count to be between**                      | Expect the number of rows to be between two values.                                                                                    | Yes                 | Yes               |
| Volume             | **table row count to equal**                           | Expect the number of rows to equal a value.                                                                                            | No                  | No                |
| Volume             | **table row count to equal other table**               | Expect the number of rows to equal the number in another table or view within the same database.                                       | No                  | No                |

*Configurable through only the GX Cloud API. 

## Custom SQL Expectations

GX Cloud offers the ability to write a custom Expectation using SQL. It is designed to fail validation if the provided SQL query returns one or more rows.

The provided query should be written in the dialect of the Data Source in which a given Data Asset lives. If you are working with a Query Data Asset, note that there are some [limitations on allowed datatypes](/cloud/data_assets/manage_data_assets.md#data-asset-options-for-sql-data-sources) in the provided query. To simplify working with custom SQL Expectations, you can use ExpectAI to [generate a SQL query](/docs/cloud/expectations/manage_expectations.md#generate-sql) based on a natural language prompt you provide and a data profile GX Cloud automatically provides.

:::info Optional `{batch}` named query

The optional `{batch}` named query references the Batch of data under test. When the Expectation is evaluated, the `{batch}` named query will be replaced with the Batch of data that is validated.

:::

## Multi-source Expectations

A Multi-source Expectation executes one SQL query for each of two Data Sources and compares their results for equality. This can be helpful for validating consistency between systems during data migration or regular data loading processes. Multi-source Expectations can detect data drift introduced during the ETL process through discrepancies in schemas, counts, time windows, data types, and precision levels between Data Sources. Here are some examples of comparisons you can test:
- Every row in table A matches every row in table B.
- An aggregate metric of table A matches the same aggregate metric of table B.
- An aggregate metric of table A matches a different aggregate metric of table B. (For example, the count of rows where X is true in table A matches the count of rows where Y and Z are true in table B.)

To compare results for equality, each row returned by the query for the base Data Source will be compared to each row returned by the query for the comparison Data Source. When you configure a Multi-source Expectation, you set an **Expected percentage of identical rows**. The Expectation will fail if the percentage of identical rows between your two queries falls below this threshold.

The percentage of identical rows is computed by dividing the number of matching rows by the maximum number of rows in either result. Here are some example scenarios:

| Base result row count | Comparison result row count | Matched rows | Percentage of identical rows |
| --------------------- | --------------------------- | ------------ | ---------------------------- |
| 200                   | 200                         | 200          | 100%                         |
| 25                    | 100                         | 25           | 25%                          |
| 100                   | 25                          | 1            | 1%                           |
| 0                     | 0                           | 0            | 100%                         |

To create a Multi-source Expectation, [add the **expect query results to match comparison** Expectation](/cloud/expectations/manage_expectations.md#create-an-expectation) on the base Data Source. Each provided query should be written in the dialect of the associated Data Source.

Keep the following limitations in mind when working with Multi-source Expectations:
- The comparison is limited to the first 200 rows of each query result. If you anticipate that a query will return more than 200 rows, use an `ORDER BY` clause to control what is surfaced first for comparison.
- Batches are not supported. To test a time-based interval of data, use timestamp windows in your base and comparison SQL queries.
- The Expectation configuration and validation results are not reflected on the comparison Data Source. The Expectation is always managed on the Data Asset where you initially configure it.

## Anomaly Detection

Anomaly Detection Expectations evolve with your data to detect deviations from historical patterns. To speed up their creation, you can generate Anomaly Detection Expectations when you use the GX Cloud UI to [create new Data Assets](/cloud/data_assets/manage_data_assets.md#add-a-data-asset-from-an-existing-data-source) or [add Expectations](/cloud/expectations/manage_expectations.md#create-an-expectation). Note that [some Data Sources](/docs/cloud/data_sources/manage_data_sources.md#workflow-and-feature-support) don't support these options. All Data Sources support manual configuration of Anomaly Detection by adding Expectations with Dynamic Parameters or forecasted ranges.

### Dynamic Parameters

Dynamic Parameters allow you to create Expectations whose parameters update based on new data. GX Cloud can populate new Expectation parameters at runtime using the last `n` validation results. For example, you can define an Expectation to validate that the maximum value within a column does not exceed 20% above a previously recorded value.

You will be able to input:

- Sensitivity: `X%` of the average of previous values

- Constraint: `Above`, `below`, or `above and below` for the sensitivity threshold

- Run count: `n` previous validation results

When you select your `n` run count, and: 

- There are `0` previous runs, the Expectation will always succeed.

- There are `<n` runs, the Expectation will take all previous runs into account.

- There are `n` runs, the Expectation will take the last `n` runs into account.

- There are `>n` runs, the Expectation will take the last `n` runs into account.

### Forecasted ranges

Forecasted ranges are determined by GX Cloud through a continuous learning algorithm that analyzes historical patterns in your data. For example, a forecasted range for volume Anomaly Detection could detect a sudden increase when volume has been stable or stagnation in a season when volume typically grows. GX Cloud sets and updates forecasted range parameters on your behalf. 

Keep the following in mind when working with forecasted ranges:
- Expectations with forecasted ranges will always succeed for the first 2 validation runs. This is because GX Cloud needs at least 2 data points to produce a forecast.
- Forecasted ranges are not supported for incrementally validated Batches of data.

## Row conditions

By default, Expectations apply to every row retrieved in a [Batch](/docs/cloud/validations/run_validations.md). However, there are instances when an Expectation may not be relevant for every row. For example, you might expect that a column indicating the country of origin for a product should not be null when the product is an import. If it’s ok for the country of origin column to be null for products produced locally, then applying a nullness check for country of origin on every row in the Batch could result in many false negatives. To address this scenario, GX Cloud allows you to restrict Expectations to apply to only a subset of the data retrieved in a Batch.

Row conditions support complex business logic through the following elements:

- Condition statements that check a single column against a value or set of values. 
- Condition blocks that combine multiple condition statements with an AND relationship between them. When multiple condition blocks exist, the blocks themselves have an OR relationship between them.


Here are some examples of how to express complex row conditions:

- **A and B**: Two condition statements within a single condition block.

   ![product_category is in books, magazines, cards and purchase_amount is greater than 100](/img/a_and_b.png)

- **A or B**: Two condition statements, each in its own condition block.

   ![purchase_date is after 2025-10-31 or return_date is after 2025-10-31](/img/a_or_b.png)

- **(A and B) or (C and D)**: Two condition statements in one condition block and two statements in another block.

   ![return_date is not null and product_category is clothing or product_rating is less than or equal to 2 and purchase_amount is greater than or equal to 100](/img/a_and_b_or_c_and_d.png)

- **A and (B or C)**: This pattern is not supported verbatim, but you can achieve the same result with **(A and B) or (A and C)** as two condition statements in one condition block and two statements in another block.

   ![product_category is games and purchase_amount is greater than or equal to 250 or product_category is games and product rating is 5](/img/a_and_b_or_c.png)

An Expectation can have up to 100 condition statements grouped in any number of condition blocks.


## Failure severity

Every Expectation is assigned a severity level of critical, warning, or info that indicates the impact of the Expectation failing. Failure severity indicators are surfaced throughout GX Cloud to help your team understand the quality of your data. This includes high-level information like the overall status of a Data Asset as well as granular details like individual results in Validation run history.  

You can use the following to create severity-based responses to results:
- [Alerts](/cloud/alerts/alert_about_failures.md).
- Built-in [Actions](/cloud/alerts/trigger_actions.md).
- Pipeline conditioning with the `get_maximum_severity_failure` helper method in the [`ExpectationSuiteValidationResult` class](/reference/api/core//ExpectationSuiteValidationResult_class.mdx).

You decide the severity when you manually create an Expectation. When you have GX Cloud generate Expectations, they default to warning severity, which you can edit later. If an Expectation fails to execute, the failure will be recorded as critical, regardless of the Expectation configuration, to bring your attention to the fact that your data is not being tested as intended.

## GX-managed vs. API-managed Expectations

In GX Cloud, Expectations can be GX-managed or API-managed.
- GX-managed Expectations are created using the GX Cloud UI.
- API-managed Expectations are created using the GX Cloud API.

If you have both kinds of Expectations, they will be organized in separate tables on the **Expectations** tab as they have different capabilities in the GX Cloud UI. 

Here is a comparison of key characteristics of GX-managed and API-managed Expectations. 

| Characteristic        | GX-managed Expectation                                                                                                                                                                                                          | API-managed Expectation                                                                                                                                                                                     |
|-----------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Edit                  | [Edit parameters](/cloud/expectations/manage_expectations.md#edit-an-expectation) with the GX Cloud UI.                                                                                                                         | [Edit parameters with the GX Cloud API](/reference/api/expectations/Expectation_class.mdx) or the GX Cloud UI.                                                                                              |
| Batch                 | Options depend on your Data Source. See [Run Validations](/cloud/validations/run_validations.md) for more information.                                                                                                          | Options depend on your Data Source. See [Run Validations](/cloud/validations/run_validations.md) for more information.                                                                                      |
| Ad hoc Validation     | Options depend on your Data Source and whether you want to validate your entire Data Asset or a time-based subset. See [Run Validations](/cloud/validations/run_validations.md) for more information.                           | Options depend on your Data Source and whether you want to validate your entire Data Asset or a time-based subset. See [Run Validations](/cloud/validations/run_validations.md) for more information.       |
| Recurring Validations | [Schedule Validations](/cloud/schedules/manage_schedules.md) in the GX Cloud UI.                                                                                                                                                | Not supported, use an [orchestrator](/cloud/integrations/integrate_airflow.md) to control recurring validations.                                                                                                   |
| Validation Results    | [Access results in the Validations tab](/cloud/validations/run_validations.md#view-validation-run-history) of the GX Cloud UI.<br /><br />[Format results](/cloud/validations/format_results.md?interface=ui) with the GX Cloud UI or the GX Cloud API. | [Access results with the GX Cloud API](/cloud/validations/run_validations.md) or in the Validations tab of the GX Cloud UI.<br /><br />[Format results](/cloud/validations/format_results.md?interface=api) with the GX Cloud API.   |
| Expectation Suite     | Automatically organized in a hidden default Expectation Suite.                                                                                                                                                                  | Manually grouped into [custom Expectation Suites](/core/define_expectations/organize_expectation_suites.md) via the GX Cloud API.                                                                           |
| Delete                | [Delete Expectation](/docs/cloud/expectations/manage_expectations/#delete-an-expectation) with the GX Cloud UI.                                                                                                                 | [Delete Expectation with the GX Cloud API](/reference/api/ExpectationSuite_class.mdx#great_expectations.ExpectationSuite.delete_expectation) or the GX Cloud UI.                                            |


:::note Hidden resources for GX-managed Expectations
To support GX-managed Expectations, we create resources that you typically won't directly interact with. For example, we create a GX-managed Expectation Suite that we use to organize your Expectations. For some workflows you may need to work with these hidden resources, for example, you may need to [find the name of an automatically created Checkpoint](/cloud/integrations/integrate_airflow.md#create-a-dag-file-for-your-gx-cloud-checkpoint). But, typically you can ignore the existence of these hidden resources. 
:::
