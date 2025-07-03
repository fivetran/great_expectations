---
sidebar_label: "Manage Expectations"
title: "Manage Expectations"
description: Create and manage Expectations in GX Cloud.
---

An Expectation is a verifiable assertion about your data. They make implicit assumptions about your data explicit, and they provide a flexible, declarative language for describing expected behavior. They can help you better understand your data and help you improve data quality.

<!-- [//]: # (TODO: To learn more about Expectations, see Expectation.) -->

## Prerequisites

- You have a [Data Asset](/cloud/data_assets/manage_data_assets.md).

## Available Expectations

The following table lists the available GX Cloud Expectations.

| Data quality issue | Expectation                                            | Description                                                                                                                            | Dynamic Parameters? | Forecasted range? |
|--------------------|--------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------|---------------------|-------------------|
| Completeness       | **column proportion of non-null values to be between** | Expect the proportion of non-null values to be between a minimum value and a maximum value.                                            | Yes                 | No                |
| Completeness       | **column values to be null**                           | Expect the column values to be null.                                                                                                   | Yes                 | No                |
| Completeness       | **column values to not be null**                       | Expect the column values to not be null.                                                                                               | Yes                 | No                |
| Multi-source       | **query results to match comparison**                  | Query multiple Data Sources and compare the results for equality.                                                                      | No                  | No                |
| Numeric            | **column max to be between**                           | Expect the column maximum to be between a minimum and a maximum value.                                                                 | Yes                 | No                |
| Numeric            | **column mean to be between**                          | Expect the column mean to be between a minimum and a maximum value.                                                                    | Yes                 | No                |
| Numeric            | **column median to be between**                        | Expect the column median to be between a minimum and a maximum value.                                                                  | Yes                 | No                |
| Numeric            | **column min to be between**                           | Expect the column minimum to be between a minimum value and a maximum value.                                                           | Yes                 | No                |
| Numeric            | **column pair values A to be greater than B**          | Expect the values in column A to be greater than column B.                                                                             | No                  | No                |
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


## Custom SQL Expectations

GX Cloud also offers the ability to write a custom Expectation using SQL. It is designed to fail validation if the provided SQL query returns one or more rows.

The provided query should be written in the dialect of the Data Source in which a given Data Asset lives.

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

To create a Multi-source Expectation, [add the **expect query results to match comparison** Expectation](#add-an-expectation) on the base Data Source. Each provided query should be written in the dialect of the associated Data Source.

Keep the following limitations in mind when working with Multi-source Expectations:
- The comparison is limited to the first 200 rows of each query result. If you anticipate that a query will return more than 200 rows, use an `ORDER BY` clause to control what is surfaced first for comparison.
- Batches are not supported. To test a time-based interval of data, use timestamp windows in your base and comparison SQL queries.
- The Expectation configuration and validation results are not reflected on the comparison Data Source. The Expectation is always managed on the Data Asset where you initially configure it.

## Anomaly Detection

Anomaly Detection Expectations evolve with your data to detect deviations from historical patterns. To speed up their creation, you can automate Anomaly Detection Expectations when you [create new Data Assets](/cloud/data_assets/manage_data_assets.md#add-a-data-asset-from-an-existing-data-source) or [add Expectations](/cloud/expectations/manage_expectations.md#add-an-expectation) for an existing Data Asset. You can also manually configure Anomaly Detection by adding Expectations with Dynamic Parameters or forecasted ranges.

### Dynamic Parameters

Dynamic Parameters allow you to create Expectations whose parameters update based on new data. GX Cloud can populate new Expectation parameters at runtime using the last `n` validation results. For example, you can define an Expectation to validate that the maximum value within a column does not exceed 20% above a previously recorded value.

You will be able to input:

1. Sensitivity: `X%` of the average of previous values

2. Constraint: `Above`, `below`, or `above and below` for the sensitivity threshold

3. Run count: `n` previous validation results

When you select your `n` run count, and: 

- There are `0` previous runs, the Expectation will always succeed.

- There are `<n` runs, the Expectation will take all previous runs into account.

- There are `n` runs, the Expectation will take the last `n` runs into account.

- There are `>n` runs, the Expectation will take the last `n` runs into account.

### Forecasted ranges

Forecasted ranges are determined by GX Cloud through a continuous learning algorithm that analyzes historical patterns in your data. For example, a forecasted range for volume Anomaly Detection could detect a sudden increase when volume has been stable or stagnation in a season when volume typically grows. GX Cloud sets and updates forecasted range parameters on your behalf. 

Expectations with forecasted ranges will neither pass nor fail until there have been at least 2 validation runs. This is because GX Cloud needs at least 2 data points to produce a forecast.

## Expectation condition

The Expectation condition is an optional field that applies to any Expectation validating row-level data. This condition allows you to filter your data so that only a specific subset of your Batch is validated. Rows will be validated only when the condition is true.

You will need to select:

1. A column to check the condition against.
2. An operator that is used to compare the column against a parameter value.
3. A parameter that will be compared against each row in the selected column.

To clear the Expectation condition, click the clear button located on the right-hand side of the condition field.


![GX Cloud Expectation condition field](./expectation_images/expectation_condition_field.png)


![GX Cloud Expectation with condition](./expectation_images/expectation_with_condition.png)

## Add an Expectation

1. In GX Cloud, click **Data Assets**.

2. In the **Data Assets** list, click the Data Asset name.

3. Click **New Expectation**.

4. Select a data quality issue to test for.

5. Select an Expectation type.

   :::tip Automatic rules for Anomaly Detection
   If you selected the schema, volume, or completeness data quality issue, you will have the **Automatic** option to generate Expectations for [Anomaly Detection](/cloud/overview/automating_rules.md#anomaly-detection). If you instead want to create your own rules, click **Manual** and then select an Expectation type.
   :::

6. Complete the mandatory and optional fields for the Expectation. A recurring [validation schedule](/cloud/schedules/manage_schedules.md) will be applied automatically to your Expectation. 

7. Click **Save** or click **Save & Add More** and then repeat steps 4 through 7 to add additional Expectations.

8. Optional. Run a Validation. See [Run a Validation](/cloud/validations/manage_validations.md#run-a-validation).


## Generate Expectations with ExpectAI <span class="beta">Beta</span>

To accelerate test coverage, you can use ExpectAI to generate recommended Expectations for a Data Asset. These will be personalized based on an analysis of a sample of your data.

Keep the following requirements in mind when working with ExpectAI:
- Your organization must be using a [fully-hosted deployment](/cloud/deploy/deployment_patterns.md).
- The Data Asset's Data Source must be Databricks SQL, PostgreSQL, Redshift, or Snowflake.

To add AI-recommended Expectations:
1. In GX Cloud, click **Data Assets**.
2. In the **Data Assets** list, click the Data Asset name.
3. Click **Generate Expectations**.
   :::note This might take a few minutes
   ExpectAI may take a few minutes to analyze your data and recommend personalized Expectations. You can navigate away from the page while ExpectAI works in the background. GX will send an [email alert](/cloud/alerts/manage_alerts.md) when your recommended Expectations are ready for review.
   :::
4. Review the recommended Expectations and **Approve** (✓) or **Reject** (✗) them within 48 hours. After 48 hours, any remaining recommendations will be discarded.
5. Optional. Run a Validation. See [Run a Validation](/cloud/validations/manage_validations.md#run-a-validation).
6. Optional. [Edit](#edit-an-expectation) AI-generated Expectations based on the insights you get from running a Validation and your data quality needs.


## Optional. Define a Batch

If your Data Asset has at least one DATE or DATETIME column, you can define a Batch to validate your data incrementally.

1. In GX Cloud, click **Data Assets**.

2. In the **Data Assets** list, click the Data Asset name.

3. Next to the current batch configuration, click <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/> **Edit batch**.

4. Choose how to **Validate by**. Select the **Entire Asset** tab to provide all Data Asset records to your Expectations and validations, or select one of the **Year**/**Month**/**Day** tabs to use subsets of Data Asset records for your Expectations and validations. **Year** partitions Data Asset records by year, **Month** partitions Data Asset records by year and month, **Day** partitions Data Asset records by year, month, and day.

5. Select the **Batch column** that contains the DATE or DATETIME data to partition on.

## Edit an Expectation

1. In GX Cloud, click **Data Assets**.

2. In the **Data Assets** list, click the Data Asset name.

3. Find the Expectation that you want to edit.

4. Click <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/> **Edit Expectation** for the Expectation that you want to edit.

5. Edit the Expectation configuration.

6. Click **Save**.

## Delete an Expectation

1. In GX Cloud, click **Data Assets**.

2. In the **Data Assets** list, click the Data Asset name.

3. Find the Expectation that you want to delete.

4. Click <img src="/img/trash.png" alt="trash icon" width="20" height="20"/> **Delete Expectation** for the Expectation that you want to delete.

   :::tip You can delete Expectations in bulk
    If you want to delete all Expectations that test for a certain data quality issue, you can instead click <img src="/img/trash.png" alt="trash icon" width="20" height="20"/> **Bulk-delete Expectations** for the relevant category.
    :::

5. Click **Delete**.



## GX-managed vs. API-managed Expectations

In GX Cloud, Expectations can be GX-managed or API-managed.
- GX-managed Expectations are created using the GX Cloud UI.
- API-managed Expectations are created using the GX Cloud API.

If you have both kinds of Expectations, they will be organized in separate tables on the **Expectations** tab as they have different capabilities in the GX Cloud UI. 

Here is a comparison of key characteristics of GX-managed and API-managed Expectations. 

| Characteristic     | GX-managed Expectation                                                                                                                                                                              | API-managed Expectation                                                                                                                                                                                                                                                                                                     |
|--------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Edit               | [Edit parameters](/cloud/expectations/manage_expectations.md#edit-an-expectation) with the GX Cloud UI                                                                                              | [Edit parameters with the GX Cloud API](/reference/api/expectations/Expectation_class.mdx) or the GX Cloud UI                                                                                                                                                                                                                        |
| Batch              | [Define a Batch](/cloud/expectations/manage_expectations.md#optional-define-a-batch) in the GX Cloud UI                                                                                                | Define a Batch with the GX Cloud API when connecting to [SQL](/core/connect_to_data/sql_data/sql_data.md#create-a-batch-definition), [filesystem](/core/connect_to_data/filesystem_data/filesystem_data.md#create-a-batch-definition), or [dataframe](/core/connect_to_data/dataframes/dataframes.md#create-a-batch-definition) data |
| Validate           | [Run a Validation](/docs/cloud/validations/manage_validations.md#run-a-validation) using the GX Cloud UI or [run a Checkpoint](/core/trigger_actions_based_on_results/run_a_checkpoint.md) with the GX Cloud API | [Create a Validation Definition and run it](/core/run_validations/run_validations.md) with the GX Cloud API                                                                                                                                                                                                                          |
| Validation Results | [Access results in the Validations tab](/cloud/validations/manage_validations.md#view-validation-run-history) of the GX Cloud UI                                                                       | [Access results with the GX Cloud API](/core/trigger_actions_based_on_results/choose_a_result_format/choose_a_result_format.md) or in the Validations tab of the GX Cloud UI                                                                                                                                                            |
| Schedule           | Keep default schedule or [edit schedule](/cloud/schedules/manage_schedules.md) in the GX Cloud UI                                                                                                      | Not supported, use an [orchestrator](/cloud/connect/connect_airflow.md) to control recurring validations                                                                                                                                                                                                                    |
| Expectation Suite  | Automatically organized in a hidden default Expectation Suite                                                                                                                                       | Manually grouped into [custom Expectation Suites](/core/define_expectations/organize_expectation_suites.md) via the GX Cloud API                                                                                                                                                                                                     |
| Delete             | [Delete Expectation](/docs/cloud/expectations/manage_expectations/#delete-an-expectation) with the GX Cloud UI                                                                                         | [Delete Expectation with the GX Cloud API](/reference/api/ExpectationSuite_class.mdx#great_expectations.ExpectationSuite.delete_expectation) or the GX Cloud UI                                                                                                                                                                         |

:::note Hidden resources for GX-managed Expectations
To support GX-managed Expectations, we create resources that you typically won't directly interact with. For example, we create a GX-managed Expectation Suite that we use to organize your Expectations. For some workflows you may need to work with these hidden resources, for example, you may need to [find the name of an automatically created Checkpoint](/cloud/connect/connect_airflow.md#create-a-dag-file-for-your-gx-cloud-checkpoint). But, typically you can ignore the existence of these hidden resources. 
:::
