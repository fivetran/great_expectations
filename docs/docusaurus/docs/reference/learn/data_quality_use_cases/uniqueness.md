---
sidebar_label: 'Uniqueness'
title: 'Validate data uniqueness with GX'
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

Data uniqueness is a fundamental aspect of data quality that ensures distinct values are present only once where expected in a dataset. Uniqueness constraints are often applied to columns that serve as primary keys, composite keys, or other unique identifiers. Validating uniqueness is critical for maintaining data integrity, preventing duplication, and enabling accurate analysis.

Failing to validate uniqueness can lead to various data quality problems:

* Duplicates can skew analytics, leading to incorrect conclusions and flawed decision-making. For example, duplicate transactions could overstate revenue.
* Non-unique identifiers can cause data corruption when merging or joining datasets, resulting in lost data or mismatched records.
* Redundant data wastes storage space and complicates data management. It also slows query performance by unnecessarily increasing table size.
* Inconsistencies from uniqueness violations erode trust in the data. Analysts and executives may doubt data-derived recommendations and hesitate to act on the insights.

Great Expectations (GX) provides a collection of Expectations to validate data uniqueness. By codifying uniqueness rules and continuously validating data against them, organizations can catch issues early and ensure high quality data for downstream consumption. This article will discuss how to leverage GX to implement uniqueness checks as part of your data validation.

## Prerequisite knowledge

This article assumes basic familiarity with GX components and workflows. If you're new to GX, start with the [GX Cloud](/cloud/overview/gx_cloud_overview.md) and [GX Core](/core/introduction/introduction.mdx) overviews to familiarize yourself with key concepts and setup procedures.

## Data preview

The examples in this article use a sample customer dataset. The data is available from a public Postgres database, as shown in the examples, or can also be accessed in [CSV format](https://raw.githubusercontent.com/great-expectations/great_expectations/develop/tests/test_sets/learn_data_quality_use_cases/uniqueness_customers.csv).

| customer_id | first_name | last_name | email_address | secondary_email | phone_number | country_code | government_id |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| 1 | John | Doe | johndoe@email.com |   | +1 123 456-7890 | US | 123-45-6789 |
| 2 | Jane | Smith | jsmith@email.com | jsmith@email.com | +1 409 437-3210 | CA | 987 654 321 |
| 3 | Bob | Thatcher | bobthatcher@email.com |   |   | US | 235-98-4389 |
| 4 | Jon | Doe | jon.doe@email.com | jon.doe2@email.com | +1 888 999-9999 | US |   |
| 5 | J | Doe | jd@email.com |   |   | US | 123-45-6789 |
| 6 | Jenny | Williams |   |   |   | CA | 298 367 456 |
| 7 | Johnathan | Doe | johndoe@email.co.uk |   | +44 333 981537 | UK | RC 23 94 27 B |
| 8 | Liz | Brown | l2@email.com | lizzeb@email.com | +44 1224 587623 | UK |   |
| 9 | Jonathan | Doe |   | jdoe@email.co.uk | +44 333 991537 | UK | RC 23 94 27 C |
| 10 | Elizabeth | Brown | lizzeb@email.com | l2@email.com | +44 1224 587623 | UK |   |

Primary key fields, such as `customer_id`, can uniquely identify a row of data but cannot always uniquely identify the corresponding real-world entity, such as a person. In this dataset, some individual customers are represented by multiple rows, each with slight variations in their registered information. This scenario is common in real-world customer databases and presents a challenge for validating and maintaining data uniqueness.

Uniqueness is particularly crucial for fields like `customer_id`, `email_address`, `government_id`. However, due to data entry errors, multiple registrations, or system migrations, duplicates can still occur. When combined, fields such as `country_code` and `government_id` might ideally form a unique identifier for each customer. This ensures that each customer is distinctly recorded and prevents issues like fragmented customer profiles or incorrect communications.

## Key uniqueness Expectations

Duplicate data can manifest as duplicate rows within a dataset, or as duplicate values within a single row. GX provides Expectations, available in both GX Cloud and GX Core, that validate for uniqueness across rows and within rows.

### Expect column values to be unique

This Expectation checks that each value in a column is unique. It is useful to validate that there are no duplicates in a column that should contain only unique values, such as a primary key column.

**Example**: Expect the `customer_id` column to contain only unique values.

```python title="Python" name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/uniqueness_resources/uniqueness_expectations.py ExpectColumnValuesToBeUnique"
```

<small>View `ExpectColumnValuesToBeUnique` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_column_values_to_be_unique).</small>


### Expect compound columns to be unique

This Expectation validates that the combination of values across multiple columns is unique for each row. It can be used to check uniqueness across a set of columns that together form a unique identifier, such as a composite key.

**Example**: Expect that the combination of `country_code` and `government_id` to uniquely identify a customer record.

```python title="Python" name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/uniqueness_resources/uniqueness_expectations.py ExpectCompoundColumnsToBeUnique"
```

<small>View `ExpectCompoundColumnsToBeUnique` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_compound_columns_to_be_unique).</small>


### Expect column proportion of unique values to be between

This Expectation validates that the proportion of unique values in a column is between a specified minimum and maximum value. It is useful for ensuring a certain level of uniqueness in a column without requiring full uniqueness.

**Example**: Validate that at least 90% of all customer `email_address` values are unique.

```python title="Python" name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/uniqueness_resources/uniqueness_expectations.py ExpectColumnProportionOfUniqueValuesToBeBetween"
```

<small>View `ExpectColumnProportionOfUniqueValuesToBeBetween` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_column_proportion_of_unique_values_to_be_between).</small>


### Expect column unique value count to be between

This Expectation validates that the number of unique values in a column is between a specified minimum and maximum value. It is useful for validating that the quantity of unique values falls within an expected range, for example, checking for a known range of distinct category values in a categorical column.

**Example**: Ensure that the `country_code` column contains between 1 and 5 unique values.

```python title="Python" name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/uniqueness_resources/uniqueness_expectations.py ExpectColumnUniqueValueCountToBeBetween"
```

<small>View `ExpectColumnUniqueValueCountToBeBetween` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_column_unique_value_count_to_be_between).</small>


### Expect select column values to be unique within record

This Expectation validates that, for each row, the values across a specified set of columns are unique. It is useful to check for the presence of duplicate column values within a single row. Note that this Expectation allows for duplicate rows within the dataset, as long as the specified columns have unique values within each individual row.

**Example**: Expect each customer record to have a unique `email_address` and `secondary_email`.

```python title="Python" name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/uniqueness_resources/uniqueness_expectations.py ExpectSelectColumnValuesToBeUniqueWithinRecord"
```

<small>View `ExpectSelectColumnValuesToBeUniqueWithinRecord` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_select_column_values_to_be_unique_within_record).</small>

<br/>
<br/>

:::tip[GX tip for uniqueness Expectations]
* If your data allows for a small number of duplicates, consider using `ExpectColumnProportionOfUniqueValuesToBeBetween` or `ExpectColumnUniqueValueCountToBeBetween` instead of strict uniqueness Expectations. These Expectations allow you to set a threshold for the proportion or count of unique values, providing more flexibility in cases where perfect uniqueness is not required or where a small number of duplicates are acceptable.

* When validating uniqueness, consider the level of granularity required for your use case. Column-level Expectations like `ExpectColumnValuesToBeUnique` ensure uniqueness within a single column, while row-level Expectations like `ExpectCompoundColumnsToBeUnique` validate uniqueness across multiple columns. Choose the appropriate Expectation based on whether you need to validate a unique identifier, a composite key, or a combination of fields that should be unique within each row.
:::

## Example: Identify potential duplicate entities

**Context**: Primary key fields can be used uniquely identify rows of data, but cannot always uniquely identify the corresponding real-world entity represented by the data. Preventing duplicate records and maintaining unique data often cannot be accomplished by primary key constraints alone, additional uniqueness checks must be used to validate groups of attributes that can be used to uniquely identify entities.

For instance, in customer datasets, a `customer_id` can be created for all customer records, but duplicate customers (real world individuals represented by multiple rows of data) can still enter the dataset for a variety of reasons: inconsistent contact information provided by the customer themselves, errors in data entry, or bad data migrations.

**Goal**: Using uniqueness Expectations in GX Cloud or GX Core, identify potential duplicate entities in the sample customer dataset.

<Tabs
   defaultValue="gx_cloud"
   values={[
      {value: 'gx_cloud', label: 'GX Cloud'},
      {value: 'gx_core', label: 'GX Core'}
   ]}
>

<TabItem value="gx_cloud" label="GX Cloud">
Use the GX Cloud UI to walk through the following steps:

1. Create a Postgres Data Asset for the `uniqueness_customers` table using the following connection string:
  ```python title="Connection string"
  postgresql+psycopg2://try_gx:try_gx@postgres.workshops.greatexpectations.io/gx_learn_data_quality
  ```

2. Add an Expectation to validate the uniqueness of the `customer_id` column, which serves as a primary key for the dataset.
   * Expectation: Expect column values to be unique
   * Column: `customer_id`

3. Add two Expectations that validate the uniqueness of composite keys that should represent a single real-world entity (the customer).

   * Expect that individual customers have a unique government id, relative to their country.
      * Expectation: Expect compound columns to be unique
      * Column List: `country_code`, `government_id`
      * Ignore Row If: Any value is missing

   * Expect that individual customers have unique last name and phone number.
      * Expectation: Expect compound columns to be unique
      * Column List: `last_name`, `phone_number`
      * Ignore Row If: Any value is missing

4. Validate the `uniqueness_customers` Data Asset with the newly created Expectations.

5. Review the Validation Results. Under **Batches & run history**, select the individual Validation run (not **All Runs**) to view the sample unexpected values that were identified for failing Expectations.

**Result**:
Based on the sample unexpected values shown for each failing Expectation, you can see that two potential groups of duplicate customer records are identified.
</TabItem>

<TabItem value="gx_core" label="GX Core">
Run the following GX Core workflow:

```python title="Python" name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/uniqueness_resources/uniqueness_workflow.py full workflow"
```

**Result**:
```python title="Python output"
Expectation: expect_compound_columns_to_be_unique, Potential duplicates found:
[{'country_code': 'US', 'government_id': '123-45-6789'}, {'country_code': 'US', 'government_id': '123-45-6789'}]

Expectation: expect_compound_columns_to_be_unique, Potential duplicates found:
[{'last_name': 'Brown', 'phone_number': '+44 1224 587623'}, {'last_name': 'Brown', 'phone_number': '+44 1224 587623'}]
  ```

Parsing the Validation Result object for failing Expectations enables you to access a sample of the unexpected values that caused the validation to fail. These values can be used to identify duplicate rows, based on the definition of uniqueness for an individual customer.

</TabItem>

</Tabs>

* `country_code`: `US`, `government_id` : `123-45-6789`

   This result suggests that `customer_id` `1` and `5` represent the same customer, John Doe, identified by duplicate rows containing his unique US government id.

* `last_name`: `Brown`, `government_id` : `+44 1224 587623`

   This result suggests that `customer_id` `8` and `10` represent the same customer, Elizabeth (Liz) Brown, identified by duplicate rows containing her last name and phone number.


**GX solution**: GX Cloud and GX Core both enable validating data uniqueness in flexible ways: within single columns or across compound columns, across records in a dataset or fields within a record. The Validation Results returned by GX can be used to identify duplicate data in addition to monitoring uniqueness.

## Scenarios

### Detecting duplicate transactions

**Context**: In financial systems, duplicate transactions can lead to incorrect account balances, unhappy customers, and accounting discrepancies. Monitoring key fields for uniqueness helps detect and prevent such issues.

**GX solution**: Use `ExpectCompoundColumnsToBeUnique` to validate that the combination of fields that uniquely identify a transaction (e.g., timestamp, sender account, recipient account, amount) is unique across all rows.

### Ensuring integrity of customer records

**Context**: In a customer database, each customer should have a unique identifier. Duplicate customer IDs can lead to severe data integrity issues, such as incorrectly merged customer profiles, misdirected communications, or inaccurate analytics. If not caught early, resolving duplicate records can become a complex, error-prone, and resource-intensive process.

**GX solution**: Use `ExpectColumnValuesToBeUnique` to ensure that the customer ID column contains only unique values. If duplicates are found, investigate and resolve them to maintain data integrity.

### Detecting anomalies in user agent strings

**Context**: In web analytics, user agent strings provide information about visitors' browsers and devices. Anomalies in user agent strings, such as a low proportion of unexpected or unique values, could indicate bot traffic coming from a single source or other potential security issues.

**GX solution**: Use `ExpectColumnProportionOfUniqueValuesToBeBetween` to check that the proportion of unique user agent strings falls within an expected range. If the proportion is unusually low, investigate the traffic sources and patterns.

## Avoid common uniqueness analysis pitfalls

- **Not considering business context**: Understand specific uniqueness requirements for each dataset and use case. Blindly applying generic checks can lead to false alarms or missed issues.
- **Checking at the wrong granularity**: Validate uniqueness at the appropriate level, whether it's individual columns or combinations of columns, based on business requirements.
- **Mishandling missing or null values**: Decide whether to consider null values as distinct or ignore them in uniqueness validation. Be consistent to avoid skewed results.
- **Ignoring subtle differences**: Be aware of whitespace, case sensitivity, and type mismatches that could cause false negatives. Clean and normalize data before uniqueness checks.
- **Not monitoring over time**: Continuously monitor uniqueness metrics to detect changes or anomalies. Set up alerts and track unique value counts over time.
- **Focusing solely on uniqueness**: Combine uniqueness validation with other data quality dimensions, such as completeness, consistency, and validity, for a comprehensive approach.

## The path forward

Monitoring data for uniqueness is an essential technique in the effort to maintain high-quality data. However, when duplicate data is inadvertently introduced into your organization's data, uniqueness checks must be paired with effective data deduplication and entity resolution to fix the issue.

Uniqueness is an important measure of data quality, but is only one facet of a comprehensive approach to data quality. Effective data quality monitoring and management requires validation of data across other quality dimensions, such as completeness, schema, integrity, volume, and distribution. Explore our [data quality use cases](/reference/learn/data_quality_use_cases/dq_use_cases_lp.md) for more insights and best practices to expand your data validation to encompass key quality dimensions.