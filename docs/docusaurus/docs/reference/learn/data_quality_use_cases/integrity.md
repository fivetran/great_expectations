---
sidebar_label: 'Integrity'
title: 'Validate data integrity with GX'
---
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

Data integrity focuses on the relationships and dependencies between data elements. Is a fundamental aspect of ensuring data quality and trustworthiness. In today's complex data landscape, information is spread across multiple systems, tables, and platforms and maintaining proper relationships between data elements is critical. Failing to validate and preserve these relationships can lead to incorrect analyses, faulty business decisions, and compliance issues.

Consider these common data integrity challenges:

* **Referential integrity**: Ensuring that relationships between tables remain valid and consistent is crucial. For example, in a financial system, every transaction should link to valid accounts, and account balances should accurately reflect all related transactions.
* **Business rule compliance**: Data must adhere to established business logic and domain-specific constraints. An e-commerce platform, for instance, should validate that ordered quantities don't exceed available inventory and that shipping addresses match customer records.
* **Cross-column consistency**: Logical relationships between related columns within and across tables must be verified. For instance, in a healthcare system, diagnosis codes should align with prescribed medications, and treatment dates should fall within the authorized timeframe.
* **Value dependencies**: Hierarchies and dependencies in numerical and categorical data must be maintained. For example, a project management system should ensure that task start dates precede end dates and that parent tasks span the duration of their subtasks.

Failing to validate data relationships can result in discrepancies, incorrect calculations, and flawed insights, undermining the reliability and value of your data assets.

Great Expectations (GX) offers a robust framework for validating data integrity. It provides expressive Expectations, flexible validation workflows, and support for diverse data sources that enable data teams to implement comprehensive integrity checks across their data ecosystem.

This article demonstrates how to use GX to define and enforce data integrity rules through practical examples and best practices. It covers techniques for validating referential integrity, cross-table consistency, and compliance with business rules.

## Prerequisite knowledge

This article assumes basic familiarity with GX components and workflows. If you're new to GX, start with the [GX Cloud](/cloud/overview/gx_cloud_overview.md) and [GX Core](/core/introduction/introduction.mdx) overviews to familiarize yourself with key concepts and setup procedures.

## Data preview

The examples in this article use sample financial transfer and transfer balance data. The sample data is available from public Postgres database tables, as shown in the examples, and is also available in CSV format.

![Sample data relationship diagram](./integrity_resources/integrity_table_relationships.png)

* `transfers`: This table captures contains a record of each financial transfer, including summary information of the `amount` and `transaction_date`. Transfer records contain foreign keys for records in related tables that provide additional detail about each transfer. [[CSV](https://raw.githubusercontent.com/great-expectations/great_expectations/develop/tests/test_sets/learn_data_quality_use_cases/integrity_transfers.csv)]


| transfer_id | amount  | transaction_date | transfer_balance_id | transfer_txn_id |
|-------------|---------|------------------|---------------------|-----------------|
| 1001        | 250.00  | 2024-01-15       | TB099     | TT1234 |
| 1002        | 40.00   | 2024-01-15       | TB101     | TT1235 |
| 1003        | 1195.00 | 2024-01-16       | TB102     | TT1236 |
| 1004        | 80.00   | 2024-01-16       | TB103     | TT1237 |

* `transfer_balance`: This table contains records that provide additional detail for sum-to-zero checks on each transfer, ensuring that the total debits and credits for each transaction balance out correctly, even with adjustments. [[CSV](https://raw.githubusercontent.com/great-expectations/great_expectations/develop/tests/test_sets/learn_data_quality_use_cases/integrity_transfer_balance.csv)]

| transfer_balance_id | total_amount | adjustment | sender_debit | recipient_credit |
|---------------------|--------------|------------|--------------|------------------|
| TB099   | 250.00          | 0.00       | -250.00      | 250.00           |
| TB101   | 40.00           | 0.00       | -40.00       | 40.00            |
| TB102   | 1195.00         | 5.00       | -1200.00     | 1195.00          |
| TB103   |  80.00          | 2.50       | -82.50       | 80.00            |

* `transfer_transaction`: This table contains records that capture transaction details about the transfer, including sender and recipient ids, transaction timestamps, and reference and confirmation numbers. [[CSV](https://raw.githubusercontent.com/great-expectations/great_expectations/develop/tests/test_sets/learn_data_quality_use_cases/integrity_transfer_transaction.csv)]

| transfer_txn_id | sender_id | sent_ts | sender_ref_no | recipient_id | received_ts | recipient_conf_code |
|-----------------|-----------|---------|---------------|--------------|-------------|---------------------|
| TT1234 | 501 | 2024-11-14T01:12:45Z | ABC-01 | 502 | 2024-11-14T01:12:46Z | ABC-01 |
| TT1235 | 502 | 2024-11-14T22:13:29Z | DEF-03 | 503 | 2024-11-14T22:14:01Z | DEF-03 |
| TT1236 | 503 | 2024-11-15T09:47:00Z | GHI-05 | 501 | 2024-11-15T09:47:59Z | GHI-05 |
| TT1237 | 504 | 2024-11-15T13:33:01Z | JKL-07 | 502 | 2024-11-15T13:33:36Z | JKL-07 |


Validating the integrity of this financial data involves checking the consistency and accuracy of relationships between the `transfers`, `transfer_balances`, and `transfer_transaction` tables, as well as verifying that business rules and constraints are met.

## Key integrity Expectations

Great Expectations provides a collection of Expectations, available in both GX Cloud and GX Core, that validate relationships between data elements within a single table. If you want to use these same Expectations to validate data relationships across multiple tables, you have two options:

1. Create a database view that joins the tables you want to validate, and then use the built-in Expectations to validate columns within the view.
2. Create custom SQL Expectations in [GX Cloud](/cloud/expectations/manage_expectations.md#custom-sql-expectations) or [GX Core](/core/customize_expectations/use_sql_to_define_a_custom_expectation.md) to validate relationships directly using a SQL query that references multiple tables.

This section covers the first option and presents built-in Expectations that can be applied to single tables, or SQL views that query multiple tables. The second option is explored in the [Example: Validate cross-table data integrity](#validate-cross-table-data-integrity) section that showcases how to create and use custom SQL Expectations for validating relationships across separate tables.

### Expect column pair values to be equal

Validates that values in one column match corresponding values in another column.

**Example**: Verify that the sender reference number and recipient confirmation code match for each transaction in the `transfer_transaction` table.

```python title="Python" name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/integrity_resources/integrity_expectations.py ExpectColumnPairValuesToBeEqual"
```

<small>View `ExpectColumnPairValuesToBeEqual` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_column_pair_values_to_be_equal).</small>


### Expect multicolumn sum to equal

Ensures that the sum of multiple columns equals an expected value, useful for validating financial calculations and balance checks.

**Example**: Validate sum-to-zero checks in the `transfer_balances` table.

```python title="Python" name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/integrity_resources/integrity_expectations.py ExpectMulticolumnSumToEqual"
```

<small>View `ExpectMulticolumnSumToEqual` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_multicolumn_sum_to_equal).</small>


### Expect column pair values A to be greater than B

Verifies that values in one column are consistently greater than related values in another column.

**Example**: Ensure that the transfer is always sent before it is received, using the timestamp columns in the `transfer_transaction` table.

```python title="Python" name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/integrity_resources/integrity_expectations.py ExpectColumnPairValuesAToBeGreaterThanB"
```

<small>View `ExpectColumnPairValuesAToBeGreaterThanB` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_column_pair_values_a_to_be_greater_than_b).</small>

<br/>
<br/>

:::tip[GX tips for integrity Expectations]
* Use custom SQL Expectations when built-in Expectations don't cover complex business rules.
* Consider performance implications when validating across multiple tables and large datasets.
:::

## Examples

### Incorporate business logic into data integrity checks

**Context**: Definitions of data quality are highly related to the real-world use of the related data, and data quality often needs to be defined using custom business rules and logic. This example showcases the application of a built-in Expectation to validate data integrity, and then the use of a custom SQL Expectation to refine the integrity check to incorporate business logic.

**Goal**: Use GX Cloud or GX Core to implement an integrity check using a built-in Expectation. Then, use a custom SQL Expectation to enforce additional additional business logic that defines integrity in more detail.

:::tip[Custom SQL Expectations]
Custom SQL Expectations fail when the provided SQL query returns one or more rows. Construct your queries to select unexpected rows based on the `where` clause.
:::

<Tabs
   defaultValue="gx_cloud"
   values={[
      {value: 'gx_cloud', label: 'GX Cloud'},
      {value: 'gx_core', label: 'GX Core'}
   ]}
>

<TabItem value="gx_cloud" label="GX Cloud">

Use the GX Cloud UI to implement the following steps:

1. Using the following connection string to create a Postgres Data Source, create a Data Asset for the `integrity_transfer_transaction` table:
   ```python title="Connection string"
   postgresql+psycopg2://try_gx:try_gx@postgres.workshops.greatexpectations.io/gx_learn_data_quality
   ```

2. Add an **Expect column pair values A to be greater than B** Expectation that expects that the time that the transaction was received (`received_ts`) is after the time that the transaction was sent (`sent_ts`).
   * Column A: `received_ts`
   * Column B: `sent_ts`

3. Validate the  `integrity_transfers` Data Asset with the Expectation and inspect the result. The Expectation passes, all transfers are received after they are sent.

4. Using the query below, create a custom SQL Expectation to further refine the business logic that defines this integrity check. The business logic constraint dictates that all transactions should be sent and received within 45 seconds.
   ```sql title="SQL query"
   select *
   from {batch}
   where extract(epoch from (age(received_ts, sent_ts))) > 45
   ```

5. Validate the `integrity_transfers` Data Asset once again, now with two Expectations.

6. Review the Validation Results. The increased specificity of the custom SQL Expectation enables you to see that one of the transfer transaction records has failed to meet the business logic-informed definition of integrity.

</TabItem>

<TabItem value="gx_core" label="GX Core">
Run the following GX Core workflow.

```python title="Python" name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/integrity_resources/integrity_workflow.py business logic workflow"
```

**Result**:
  * `validation_result_built_in_expectation["success"]` is `True`. All transfer transactions were received after they were sent, and the Expectation passes.
  * `validation_result_custom_sql_expectation["success"]` is `False`, as one of the transactions took longer than 45 seconds to send. The increased specificity of the custom SQL Expectation enables you to see that one of the transfer transaction records has failed to meet the business logic-informed definition of integrity.

</TabItem>
</Tabs>


**GX solution**: Both GX Cloud and GX Core offer a combination of built-in Expectations and custom SQL validation, providing the flexibility to handle common and bespoke data quality requirements.


### Validate cross-table data integrity

**Context**: Validating the relationships and dependencies between data elements that reside in different tables is common use case across a variety of industries. This example uses the sample financial data in the `transfers`, `transfer_balance`, and `transfer_transaction` tables to demonstrate how to validate the integrity of transfer amounts, adjustments, and balances across tables.

**Goal**: Use GX Cloud or GX Core and a implement custom SQL Expectation to validate data integrity across tables. Validate that the `transfers` table `amount` matches the corresponding `total_amount` in the `transfer_balance` table.

<Tabs
   defaultValue="gx_cloud"
   values={[
      {value: 'gx_cloud', label: 'GX Cloud'},
      {value: 'gx_core', label: 'GX Core'}
   ]}
>

<TabItem value="gx_cloud" label="GX Cloud">

Use the GX Cloud UI to implement the following steps:

1. Using the following connection string to create a Postgres Data Source, create Data Assets for the `integrity_transfers` and `integrity_transfer_balance` tables:
   ```python title="Connection string"
   postgresql+psycopg2://try_gx:try_gx@postgres.workshops.greatexpectations.io/gx_learn_data_quality
   ```

2. Add a custom SQL Expectation on the `integrity_transfers` Data Asset to validate that the `amount` column in `integrity_transfers` matches the `total_amount` column in the `integrity_transfer_balance` table. The `join` in the SQL query enables GX Cloud to validate integrity for for data that spans multiple tables.
   ```sql title="SQL query"
   select *
   from {batch} t
   join integrity_transfer_balance b using (transfer_balance_id)
   where t.amount <> b.total_amount
   ```

3. Validate the `integrity_transfers` table and review the successful the Validation Results.
</TabItem>

<TabItem value="gx_core" label="GX Core">
Run the following GX Core workflow.

```python title="Python" name="docs/docusaurus/docs/reference/learn/data_quality_use_cases/integrity_resources/integrity_workflow.py cross-table workflow"
```

**Result**: `validation_result["success"]` is `True` and the cross-table integrity validation passes.
</TabItem>
</Tabs>


**GX solution**: Both GX Cloud and GX Core can be used to implement comprehensive integrity checks that span multiple tables and validate complex business rules.

## Scenarios

The following scenarios provide insight into how Great Expectations can help enforce data integrity across various domains. By combining built-in Expectations with custom SQL checks, organizations can create comprehensive validation frameworks that catch inconsistencies, prevent data quality problems, and ensure compliance with business rules and regulations.

### Cross-system financial reconciliation

**Context**: Financial institutions need to ensure data consistency across multiple systems for accurate reporting and compliance. Transactions must be recorded identically across systems, and balances must reconcile perfectly.

**GX solution**: Use custom SQL Expectations to compare transaction details across systems. Apply `ExpectMulticolumnSumToEqual` to validate that accounting entries balance within each system. Create additional custom SQL Expectations to ensure transaction totals reconcile across all systems.

### Product inventory and order validation

**Context**: E-commerce platforms must maintain accurate inventory tracking and order processing to prevent overselling, delays, and customer dissatisfaction.

**GX solution**: Use `ExpectColumnPairValuesAToBeGreaterThanB` to verify that ordered quantities don't exceed inventory. Implement custom SQL Expectations to ensure shipping addresses match customer records. Leverage `ExpectMulticolumnSumToEqual` to validate that order totals equal the sum of line item amounts.

### Healthcare data compliance

**Context**: Healthcare organizations must maintain data integrity across systems to ensure high-quality care, accurate diagnoses, and proper reimbursement while complying with regulations.

**GX solution**: Use custom SQL Expectations to ensure treatments link to valid patient records and that billing codes align with treatment plans. Apply `ExpectColumnPairValuesToBeEqual` to verify key patient identifiers match across systems. Implement additional custom SQL Expectations to validate consistency between diagnosis codes and prescribed medications.

## Avoid common data integrity pitfalls

* **Neglecting to validate data across multiple systems**: Many organizations focus on validating data within individual systems but fail to ensure consistency when data is integrated or transferred between systems. This can lead to discrepancies and inaccuracies that impact downstream processes and decision-making.

* **Overlooking the importance of referential integrity**: Failing to enforce referential integrity can result in orphaned records, invalid references, and data inconsistencies. Teams should prioritize validating relationships between tables and ensure that foreign key constraints are properly maintained.

* **Relying solely on application-level validations**: While application-level checks are important, they may not catch all data integrity issues, particularly when data is modified outside the application or when integrating data from external sources. Implementing database-level constraints and validations is crucial for maintaining data integrity.

* **Inadequate handling of `NULL` values**: `NULL` values can introduce ambiguity and complicate data integrity checks. Teams should establish clear policies for handling `NULLS` and ensure that validation rules account for their presence.

* **Lack of comprehensive data quality monitoring**: Data integrity issues can arise over time due to changes in source systems, data processing pipelines, or business rules. Implementing continuous data quality monitoring and alerting is essential for proactively identifying and addressing integrity problems before they impact downstream consumers.

* **Insufficient testing of data transformations**: Data transformations and ETL processes can introduce integrity issues if not thoroughly tested. Teams should validate the accuracy and consistency of transformed data, ensuring that business rules and relationships are preserved throughout the data pipeline.

## The path forward

Data integrity is a critical component of a comprehensive data quality strategy. By leveraging Great Expectations' built-in and custom validation capabilities, you can enforce integrity rules across your data landscape, ensuring consistency, accuracy, and compliance. Maintaining data integrity is an ongoing process. Regular validation, monitoring, and issue resolution are crucial for sustaining data trust and driving better outcomes.

However, data integrity is not the only aspect of data quality. To maintain trustworthy datasets, you must also address [other data quality dimensions](/reference/learn/data_quality_use_cases/dq_use_cases_lp.md) such as schema, completeness, distribution, and volume. Start by prioritizing critical data assets and incrementally expand your validation coverage to encompass these dimensions.