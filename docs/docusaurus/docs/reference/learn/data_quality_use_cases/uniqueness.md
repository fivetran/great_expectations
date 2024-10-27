---
sidebar_label: 'Uniqueness'
title: 'Validate data uniqueness with GX'
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

Data uniqueness is a fundamental aspect of data quality that ensures distinct values are present where expected in a dataset. Uniqueness constraints are often applied to columns that serve as primary keys, unique identifiers, or timestamps. Validating uniqueness is critical for maintaining data integrity, preventing duplication, and enabling accurate analysis.

Failing to validate uniqueness can lead to various data quality issues:

1. Duplicates can skew analytics, leading to incorrect conclusions and flawed decision-making. For example, duplicate transactions could overstate revenue.
2. Non-unique identifiers, like customer IDs, can cause data corruption when merging or joining datasets. This could result in lost data or mismatched records.
3. Redundant data wastes storage space and complicates data management. It also slows query performance by unnecessarily increasing table size.
4. Inconsistencies from uniqueness violations erode trust in the data. Analysts and executives may doubt reports and hesitate to act on the insights.

Great Expectations (GX) provides a suite of Expectations for validating data uniqueness. By codifying uniqueness rules and continuously validating data against them, data engineers can catch issues early and ensure a reliable, trustworthy dataset for downstream consumption. The rest of this guide will show you how to leverage GX to implement robust uniqueness checks in your data pipelines.

## Prerequisite knowledge

This article assumes basic familiarity with GX components and workflows. If you're new to GX, start with the [GX Overview](https://docs.greatexpectations.io/docs/cloud/overview/gx_cloud_overview/) to familiarize yourself with key concepts and setup procedures.

## Data preview

The examples in this guide use a sample transaction dataset, available as a [CSV file on GitHub](https://raw.githubusercontent.com/great-expectations/great_expectations/develop/tests/test_sets/learn_data_quality_use_cases/uniqueness.csv).

| transfer_type     | sender_account_number  | recipient_fullname | transfer_amount | transfer_ts       |
|----------|------------------------|--------------------|-----------------|---------------------|
| domestic | 244084670977           | Jaxson Duke        | 9143.40         | 2024-05-01 01:12    |
| domestic | 954005011218           | Nelson O’Connell   | 3285.21         | 2024-05-01 05:08    |

Uniqueness is particularly crucial for columns like `sender_account_number` and `transfer_ts`. When combined, fields such as `sender_account_number`, `recipient_fullname`, `transfer_amount`, and `transfer_ts` should form a unique identifier for each transaction. This ensures that each transfer is distinctly recorded and prevents issues like double-counting or missing transactions.

## Key uniqueness Expectations

### Column-level Expectations

#### Expect Column Proportion Of Unique Values To Be Between

This Expectation validates that the proportion of unique values in a column is between a specified minimum and maximum value. It's useful for ensuring a certain level of uniqueness in a column without requiring full uniqueness.

For example, you might expect at least 80% of the `sender_account_number` values to be unique:

```python
gxe.ExpectColumnProportionOfUniqueValuesToBeBetween(
    column="sender_account_number",
    min_value=0.8,
    max_value=1.0
)
```

<small>View `ExpectColumnProportionOfUniqueValuesToBeBetween` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_column_proportion_of_unique_values_to_be_between).</small>

#### ExpectColumnUniqueValueCountToBeBetween

This Expectation validates that the number of unique values in a column is between a specified minimum and maximum value. It's useful when you have a specific range in mind for the number of unique values that should be present.

For example, you might expect the `recipient_fullname` column to contain between 1 and 2 unique values:

```python
gxe.ExpectColumnUniqueValueCountToBeBetween(
    column="recipient_fullname",
    min_value=1,
    max_value=2
)
```

<small>View `ExpectColumnUniqueValueCountToBeBetween` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_column_unique_value_count_to_be_between).</small>


#### ExpectColumnValuesToBeUnique

This Expectation validates that each value in a column is unique. It's useful for ensuring there are no duplicates in a column that should contain only unique values, such as a primary key or a timestamp.

For example, you might expect the `transfer_ts` column to contain only unique timestamps:

```python
gxe.ExpectColumnValuesToBeUnique(
    column="transfer_ts"
)
```

If there are any duplicate values, they will be listed in `result.exceptions_list`, and the `unexpected_percent` will show the percentage of rows with duplicates.

<small>View `ExpectColumnValuesToBeUnique` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_column_values_to_be_unique).</small>

:::tip[GX tip for uniqueness Expectations]
If your data allows for a small number of duplicates, consider using `ExpectColumnProportionOfUniqueValuesToBeBetween` or `ExpectColumnUniqueValueCountToBeBetween` instead of strict uniqueness Expectations. These Expectations allow you to set a threshold for the proportion or count of unique values, providing more flexibility in cases where perfect uniqueness is not required or where a small number of duplicates are acceptable.
:::

### Row-level Expectations

#### ExpectCompoundColumnsToBeUnique

This Expectation validates that the combination of values across multiple columns is unique for each row. It's useful for ensuring uniqueness across a set of columns that together form a unique identifier, such as a composite key.

For example, you might expect the combination of `sender_account_number`, `recipient_fullname`, and `transfer_amount` to uniquely identify each transaction:

```python
gxe.ExpectCompoundColumnsToBeUnique(
    column_list=["sender_account_number", "recipient_fullname", "transfer_amount"],
)
```

<small>View `ExpectCompoundColumnsToBeUnique` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_compound_columns_to_be_unique).</small>


#### ExpectSelectColumnValuesToBeUniqueWithinRecord

This Expectation validates that, for each row, the values across a specified set of columns are unique. It's useful for ensuring there are no duplicate values within a single row across multiple fields.

For example, you might expect each transaction to have a unique `transfer_type` and `transfer_amount` combination:

```python
gxe.ExpectSelectColumnValuesToBeUniqueWithinRecord(
    column_list=["transfer_type", "transfer_amount"],
)
```

Note that this Expectation allows for duplicate rows as long as the specified columns have unique values within each row.

<small>View `ExpectSelectColumnValuesToBeUniqueWithinRecord` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_select_column_values_to_be_unique_within_record).</small>

:::tip[GX tip for uniqueness Expectations]
When validating uniqueness, consider the level of granularity required for your use case. Column-level Expectations like `ExpectColumnValuesToBeUnique` ensure uniqueness within a single column, while row-level Expectations like `ExpectCompoundColumnsToBeUnique` validate uniqueness across multiple columns. Choose the appropriate Expectation based on whether you need to validate a unique identifier, a composite key, or a combination of fields that should be unique within each row.
:::


### Sets-based Expectations

Great Expectations provides a group of Expectations to validate that column values belong to, contain, or equal specific sets. The table below lists the available Expectations in this category.

| Expectation Name | Validation Type | View in the Expectation Gallery |
| :-- | :-- | :-- |
| Expect Column Distinct Values To Be In Set | Distinct Values in Set | [ExpectColumnDistinctValuesToBeInSet](https://greatexpectations.io/expectations/expect_column_distinct_values_to_be_in_set) |
| Expect Column Distinct Values To Contain Set | Distinct Values Contain Set | [ExpectColumnDistinctValuesToContainSet](https://greatexpectations.io/expectations/expect_column_distinct_values_to_contain_set) |
| Expect Column Distinct Values To Equal Set | Distinct Values Equal Set | [ExpectColumnDistinctValuesToEqualSet](https://greatexpectations.io/expectations/expect_column_distinct_values_to_equal_set) |
| Expect Column Most Common Value To Be In Set | Most Common Value in Set | [ExpectColumnMostCommonValueToBeInSet](https://greatexpectations.io/expectations/expect_column_most_common_value_to_be_in_set) |
| Expect Column Pair Values To Be In Set | Column Pair Values in Set | [ExpectColumnPairValuesToBeInSet ](https://greatexpectations.io/expectations/expect_column_pair_values_to_be_in_set) |
| Expect Column Values To Be In Set | Column Values in Set | [ExpectColumnValuesToBeInSet ](https://greatexpectations.io/expectations/expect_column_values_to_be_in_set) |
| Expect Column Values To Not Be In Set | Column Values Not in Set | [ExpectColumnValuesToNotBeInSet](https://greatexpectations.io/expectations/expect_column_values_to_not_be_in_set) |

To use these Expectations, provide the `column` name and the `value_set` containing the expected values. For example, if using

```python
gxe.ExpectColumnValuesToBeInSet(
    column="test",
    value_set=[1, 2],
)
```

For `ExpectColumnPairValuesToBeInSet`, specify the `column_A`, `column_B`, and `value_pairs_set`.

```python
gxe.ExpectColumnPairValuesToBeInSet(
    column_A="test",
    column_B="test2",
    value_pairs_set=[(2,1), (1,1)],
)
```

:::tip[Choosing between cardinality and sets-based Expectations]
Cardinality Expectations are best suited for validating uniqueness and duplicate counts, while sets-based Expectations are ideal for validating against known sets of values.
:::

## Example: Validate uniqueness of a column

**Context**: In many datasets, certain columns are expected to have a specific number of unique values. For example, in a transaction dataset, the `transfer_type` column might be expected to have a limited number of distinct values representing the different types of transfers supported. Monitoring the count of unique values in such columns can help detect data quality issues, such as the introduction of unexpected new transfer types or data entry errors.

**Goal**: Using the `ExpectColumnUniqueValueCountToBeBetween` Expectation and either GX Core or GX Cloud, validate that the `transfer_type` column has an expected number of unique values.

<Tabs
   defaultValue="gx_cloud"
   values={[
      {value: 'gx_core', label: 'GX Core'},
      {value: 'gx_cloud', label: 'GX Cloud'}
   ]}
>

<TabItem value="gx_cloud" label="GX Cloud">
Use the GX Cloud UI to walk through the following steps.

1. Create a Postgres Data Asset for the `uniqueness_transfers` table, using the connection string:

  ```
   postgresql+psycopg2://try_gx:try_gx@postgres.workshops.greatexpectations.io/gx_learn_data_quality
  ```

3. Add an **Expect column unique value count to be between** Expectation to the freshly created Data Asset.
4. Populate the Expectation:
   * Select `transfer_type` as the **Column**.
   * Provide a **Min Value** of `2` and a **Max Value** of `4`.
5. Save the Expectation.
6. Click the **Validate** button.
7. Review Validation Results.
</TabItem>

<TabItem value="gx_core" label="GX Core">
Run the following GX Core workflow.

```python title="" name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/uniqueness_resources/uniqueness_workflow.py full example code"
```
</TabItem>

</Tabs>

**GX solution**: GX enables validating the count of unique values in a column. By setting a min and max value, you can ensure that the number of distinct values falls within an expected range. This can be done using either GX Core or GX Cloud.

In this example, we expect the `transfer_type` column to have between 2 and 4 unique values. The `ExpectColumnUniqueValueCountToBeBetween` Expectation allows us to codify this requirement and validate it against our data. If new transfer types are introduced or if data errors lead to unexpected values, the validation will fail, alerting us to potential data quality issues.

## Scenarios

### Detecting duplicate transactions

**Context**: In financial systems, duplicate transactions can lead to incorrect account balances, unhappy customers, and accounting discrepancies. Monitoring key fields for uniqueness helps detect and prevent such issues.

**GX solution**: Use `ExpectCompoundColumnsToBeUnique` to validate that the combination of fields that uniquely identify a transaction (e.g., timestamp, sender account, recipient account, amount) is unique across all rows.

### Ensuring integrity of customer records

**Context**: In a customer database, each customer should have a unique identifier. Duplicate customer IDs can lead to severe data integrity issues, such as incorrectly merged customer profiles, misdirected communications, or inaccurate analytics. If not caught early, resolving duplicate records can become a complex, error-prone, and resource-intensive process.

**GX solution**: Use `ExpectColumnValuesToBeUnique` to ensure that the customer ID column contains only unique values. If duplicates are found, investigate and resolve them to maintain data integrity.

### Validating allowed payment types

**Context**: In an e-commerce system, the payment type field should only contain valid, predefined values (e.g., "credit_card", "debit_card", "paypal"). Unexpected payment types could indicate data entry errors or system issues.

**GX solution**: Use `ExpectColumnDistinctValuesToEqualSet` to validate that the distinct values in the payment type column exactly match the set of allowed payment types. If unexpected values are found, investigate and resolve the discrepancy.

### Monitoring for missing sensor readings

**Context**: In IoT systems, sensors are expected to send readings at regular intervals. Missing readings could indicate sensor malfunctions, network issues, or data pipeline problems.

**GX solution**: Use `ExpectColumnValuesCounts` to check that the number of readings per sensor per time period (e.g., hourly) matches the expected count. If counts are lower than expected, investigate the cause of the missing readings.

### Ensuring consistency in product categories

**Context**: In an e-commerce system, product categories are used for navigation, filtering, and analysis. Inconsistent or unexpected category values can lead to a poor user experience and skewed analytics.

**GX solution**: Use `ExpectColumnDistinctValuesToBeInSet` to validate that the distinct values in the product category column are in a set of the allowed category values. If unexpected categories are found, update the allowed categories or correct the data.

### Detecting anomalies in user agent strings

**Context**: In web analytics, user agent strings provide information about visitors' browsers and devices. Anomalies in user agent strings, such as a high proportion of unexpected or unique values, could indicate bot traffic or potential security issues.

**GX solution**: Use `ExpectColumnProportionOfUniqueValuesToBeBetween` to check that the proportion of unique user agent strings falls within an expected range. If the proportion is unusually high, investigate the traffic sources and patterns.

## Avoid common uniqueness analysis pitfalls

- **Not considering business context**: Understand specific uniqueness requirements for each dataset and use case. Blindly applying generic checks can lead to false alarms or missed issues.
- **Checking at the wrong granularity**: Validate uniqueness at the appropriate level, whether it's individual columns or combinations of columns, based on business requirements.
- **Mishandling missing or null values**: Decide whether to consider null values as distinct or ignore them in uniqueness validation. Be consistent to avoid skewed results.
- **Ignoring subtle differences**: Be aware of whitespace, case sensitivity, and type mismatches that could cause false negatives. Clean and normalize data before uniqueness checks.
- **Not monitoring over time**: Continuously monitor uniqueness metrics to detect changes or anomalies. Set up alerts and track unique value counts over time.
- **Focusing solely on uniqueness**: Combine uniqueness validation with other data quality dimensions, such as completeness, consistency, and validity, for a comprehensive approach.

## The path forward

Uniqueness validation is a collaborative effort that involves multiple stakeholders, including data producers, consumers, and stewards. To ensure the success of your data quality initiatives, it's crucial to establish clear ownership and accountability. Assign roles and responsibilities for defining uniqueness requirements, implementing validation checks, and handling data quality issues. Foster a culture of open communication and shared responsibility, where everyone understands the importance of maintaining data uniqueness and feels empowered to contribute to the process.

As you continue your data quality journey, be sure to explore our [data quality series](/reference/learn/data_quality_use_cases/dq_use_cases_lp.md) for more insights and best practices. You'll find valuable information on integrating various aspects of data quality, such as schema, volume, and integrity, into your workflows. By taking a comprehensive approach to data quality, you can unlock the full potential of your data assets and drive meaningful business outcomes.
