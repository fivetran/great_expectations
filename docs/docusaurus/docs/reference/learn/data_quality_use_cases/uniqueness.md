---
sidebar_label: 'Uniqueness'
title: 'Validate data uniqueness with GX'
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

Data uniqueness is a fundamental aspect of data quality that ensures distinct values are present only once where expected in a dataset. Uniqueness constraints are often applied to columns that serve as primary keys, unique identifiers, or timestamps. Validating uniqueness is critical for maintaining data integrity, preventing duplication, and enabling accurate analysis.

Failing to validate uniqueness can lead to various data quality issues:

1. Duplicates can skew analytics, leading to incorrect conclusions and flawed decision-making. For example, duplicate transactions could overstate revenue.
2. Non-unique identifiers, like customer IDs, can cause data corruption when merging or joining datasets. This could result in lost data or mismatched records.
3. Redundant data wastes storage space and complicates data management. It also slows query performance by unnecessarily increasing table size.
4. Inconsistencies from uniqueness violations erode trust in the data. Analysts and executives may doubt reports and hesitate to act on the insights.

Great Expectations (GX) provides a suite of Expectations for validating data uniqueness. By codifying uniqueness rules and continuously validating data against them, data engineers can catch issues early and ensure a reliable, trustworthy dataset for downstream consumption. The rest of this guide will show you how to leverage GX to implement robust uniqueness checks in your data pipelines.

## Prerequisite knowledge

This article assumes basic familiarity with GX components and workflows. If you're new to GX, start with the [GX Overview](https://docs.greatexpectations.io/docs/cloud/overview/gx_cloud_overview/) to familiarize yourself with key concepts and setup procedures.

## Data preview

The examples in this guide use a sample customer dataset, available as a [CSV file on GitHub](https://raw.githubusercontent.com/great-expectations/great_expectations/develop/tests/test_sets/learn_data_quality_use_cases/customer_uniqueness.csv).

| customer_id | first_name | last_name | email_address         | phone_number | country | government_id |
|-------------|------------|-----------|------------------------|--------------|---------|---------------|
| 1           | John       | Doe       | johndoe@email.com      | 1234567890   | USA     | 123-45-6789   |
| 2           | Jane       | Smith     | jsmith@email.com       | 9876543210   | Canada  | 987-65-4321   |
| 3           | Jon        | Doe       | jon.doe@email.com      | 1234567890   | USA     | 123-45-6789   |
| 4           | J.         | Doe       | johndoe@email.com      | 1234567891   | USA     | 123-45-6789   |

In this dataset, rows 1, 3, and 4 likely represent the same person with slight variations in their registered information. This scenario is common in real-world customer databases and presents a challenge for maintaining data uniqueness and integrity.

Uniqueness is particularly crucial for fields like `customer_id`, `email_address`, and `government_id`. However, due to data entry errors, multiple registrations, or system migrations, duplicates can still occur. When combined, fields such as `first_name`, `last_name`, `phone_number`, and `government_id` should ideally form a unique identifier for each customer. This ensures that each customer is distinctly recorded and prevents issues like fragmented customer profiles or incorrect communications.

## Key uniqueness Expectations

### Column-level Expectations

#### Expect Column Proportion Of Unique Values To Be Between

This Expectation validates that the proportion of unique values in a column is between a specified minimum and maximum value. It's useful for ensuring a certain level of uniqueness in a column without requiring full uniqueness.

For example, you might expect at least 90% of the `email_address` values to be unique:

```python
gxe.ExpectColumnProportionOfUniqueValuesToBeBetween(
    column="email_address",
    min_value=0.9,
    max_value=1.0
)
```

<small>View `ExpectColumnProportionOfUniqueValuesToBeBetween` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_column_proportion_of_unique_values_to_be_between).</small>

#### ExpectColumnUniqueValueCountToBeBetween

This Expectation validates that the number of unique values in a column is between a specified minimum and maximum value. It's useful when you have a specific range in mind for the number of unique values that should be present.

For example, you might expect the `country` column to contain between 1 and 5 unique values:

```python
gxe.ExpectColumnUniqueValueCountToBeBetween(
    column="country",
    min_value=1,
    max_value=5
)
```

<small>View `ExpectColumnUniqueValueCountToBeBetween` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_column_unique_value_count_to_be_between).</small>


#### ExpectColumnValuesToBeUnique

This Expectation validates that each value in a column is unique. It's useful for ensuring there are no duplicates in a column that should contain only unique values, such as a primary key or a timestamp.

For example, you might expect the `customer_id` column to contain only unique values:

```python
gxe.ExpectColumnValuesToBeUnique(
    column="customer_id"
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

For example, you might expect the combination of `first_name`, `last_name`, and `government_id` to uniquely identify each customer:

```python
gxe.ExpectCompoundColumnsToBeUnique(
    column_list=["first_name", "last_name", "government_id"],
)
```

<small>View `ExpectCompoundColumnsToBeUnique` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_compound_columns_to_be_unique).</small>


#### ExpectSelectColumnValuesToBeUniqueWithinRecord

This Expectation validates that, for each row, the values across a specified set of columns are unique. It's useful for ensuring there are no duplicate values within a single row across multiple fields.

For example, you might expect each customer record to have a unique `email_address` and `phone_number` combination:

```python
gxe.ExpectSelectColumnValuesToBeUniqueWithinRecord(
  column_list=["email_address", "phone_number"],
)
```

Note that this Expectation allows for duplicate rows as long as the specified columns have unique values within each row.

<small>View `ExpectSelectColumnValuesToBeUniqueWithinRecord` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_select_column_values_to_be_unique_within_record).</small>

:::tip[GX tip for uniqueness Expectations]
When validating uniqueness, consider the level of granularity required for your use case. Column-level Expectations like `ExpectColumnValuesToBeUnique` ensure uniqueness within a single column, while row-level Expectations like `ExpectCompoundColumnsToBeUnique` validate uniqueness across multiple columns. Choose the appropriate Expectation based on whether you need to validate a unique identifier, a composite key, or a combination of fields that should be unique within each row.
:::

## Example: Validate uniqueness of a column

**Context**: In customer databases, certain columns are expected to contain unique values to ensure data integrity and prevent duplicate records. For example, the `government_id` column should contain unique values as it represents a unique identifier for each customer. Monitoring the uniqueness of such columns can help detect data quality issues, such as duplicate customer entries or data input errors.

**Goal**: Using the `ExpectColumnValuesToBeUnique` Expectation and either GX Core or GX Cloud, validate that the `government_id` column contains only unique values.

<Tabs
   defaultValue="gx_cloud"
   values={[
      {value: 'gx_core', label: 'GX Core'},
      {value: 'gx_cloud', label: 'GX Cloud'}
   ]}
>

<TabItem value="gx_cloud" label="GX Cloud">
Use the GX Cloud UI to walk through the following steps.

1. Create a Postgres Data Asset for the `uniqueness_customers` table, using the connection string:

  ```
   postgresql+psycopg2://try_gx:try_gx@postgres.workshops.greatexpectations.io/gx_learn_data_quality
  ```

3. Add an **Expect column values to be unique** Expectation to the freshly created Data Asset.
4. Populate the Expectation:
   * Select `government_id` as the **Column**.
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

**GX solution**: GX enables validating the uniqueness of values in a column. By using the `ExpectColumnValuesToBeUnique` Expectation, you can ensure that each value in the specified column appears only once. This can be done using either GX Core or GX Cloud.

In this example, we expect the `government_id` column to contain only unique values. The `ExpectColumnValuesToBeUnique` Expectation allows us to codify this requirement and validate it against our data. If duplicate government IDs are found, the validation will fail, alerting us to potential data quality issues such as duplicate customer records or data entry errors.

## Scenarios

### Detecting duplicate transactions

**Context**: In financial systems, duplicate transactions can lead to incorrect account balances, unhappy customers, and accounting discrepancies. Monitoring key fields for uniqueness helps detect and prevent such issues.

**GX solution**: Use `ExpectCompoundColumnsToBeUnique` to validate that the combination of fields that uniquely identify a transaction (e.g., timestamp, sender account, recipient account, amount) is unique across all rows.

### Ensuring integrity of customer records

**Context**: In a customer database, each customer should have a unique identifier. Duplicate customer IDs can lead to severe data integrity issues, such as incorrectly merged customer profiles, misdirected communications, or inaccurate analytics. If not caught early, resolving duplicate records can become a complex, error-prone, and resource-intensive process.

**GX solution**: Use `ExpectColumnValuesToBeUnique` to ensure that the customer ID column contains only unique values. If duplicates are found, investigate and resolve them to maintain data integrity.

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
