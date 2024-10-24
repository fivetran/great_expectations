---
sidebar_label: 'Integrity'
title: 'Validate data integrity with GX'
---
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

Data integrity, which focuses on the relationships and dependencies between data elements, is a fundamental aspect of ensuring data quality and trustworthiness. In today's complex data landscapes, where information is spread across multiple systems, tables, and platforms, maintaining proper relationships between data elements is more critical than ever. Failing to validate and preserve these relationships can lead to incorrect analyses, faulty business decisions, and compliance issues.

Consider these common data integrity challenges:

* **Referential integrity**: Ensuring that relationships between tables remain valid and consistent is crucial. For example, in a financial system, every transaction should link to valid accounts, and account balances should accurately reflect all related transactions.
* **Business rule compliance**: Data must adhere to established business logic and domain-specific constraints. An e-commerce platform, for instance, should validate that ordered quantities don't exceed available inventory and that shipping addresses match customer records.
* **Cross-column consistency**: Logical relationships between related columns within and across tables must be verified. In a healthcare system, diagnosis codes should align with prescribed medications, and treatment dates should fall within the authorized timeframe.
* **Value dependencies**: Hierarchies and dependencies in numerical and categorical data must be maintained. For example, a project management system should ensure that task start dates precede end dates and that parent tasks span the duration of their subtasks.

Failing to validate these relationships can result in data discrepancies, incorrect calculations, and flawed insights, undermining the reliability and value of your data assets.

Great Expectations (GX) offers a robust framework for validating data integrity at scale. Its expressive Expectations, flexible validation workflows, and support for diverse data sources enable data teams to implement comprehensive integrity checks across their entire data ecosystem.

In this guide, we'll demonstrate how to use GX to define and enforce data integrity rules through practical examples and best practices. We'll cover techniques for validating referential integrity, cross-table consistency, and compliance with business rules.

## Prerequisite knowledge

This article assumes basic familiarity with GX components and workflows. If you're new to GX, start with the [GX Cloud](https://docs.greatexpectations.io/docs/cloud/overview/gx_cloud_overview) and [GX Core](https://docs.greatexpectations.io/docs/guides/overview) overviews to familiarize yourself with key concepts and setup procedures.

## Data preview

The examples in this guide use a sample dataset of financial transactions and transfer balances, provided from public Postgres database tables. The sample data is also available in CSV format for each table:


1. `transactions` table ([CSV](https://raw.githubusercontent.com/great-expectations/great_expectations/develop/tests/test_sets/learn_data_quality_use_cases/integrity_transactions.csv)):

```
| transaction_id | sender_id | recipient_id | amount  | transaction_date | reference_number | confirmation_code |
|----------------|-----------|--------------|---------|------------------|------------------|-------------------|
| 1001           | 501       | 502          | 250.00  | 2024-01-15       | 1001             | 1001              |
| 1002           | 502       | 503          | 40.00   | 2024-01-15       | 1002             | 1002              |
| 1003           | 503       | 501          | 1200.00 | 2024-01-16       | 1003             | 1003              |
| 1004           | 504       | 502          | 80.00   | 2024-01-16       | 1004             | 1004              |
```

2. `transfer_balances` table ([CSV](https://raw.githubusercontent.com/great-expectations/great_expectations/develop/tests/test_sets/learn_data_quality_use_cases/integrity_transfer_balances.csv)):

```
| transaction_id | transfer_amount | adjustment | sender_debit | recipient_credit |
|----------------|-----------------|------------|--------------|------------------|
| 1001           | 250.00          | 0.00       | -250.00      | 250.00           |
| 1002           | 40.00           | 0.00       | -40.00       | 40.00            |
| 1003           | 1200.00         | 5.00       | -1200.00     | 1195.00          |
| 1004           | 80.00           | 2.50       | -80.00       | 82.50            |
```

In this dataset, the `transactions` table captures the details of each financial transaction, including the sender, recipient, amount, and associated reference and confirmation codes. The `transaction_balance` table provides additional information for sum-to-zero checks on each transfer, ensuring that the total debits and credits for each transaction balance out correctly, even with adjustments.

Validating the integrity of this financial data involves checking the consistency and accuracy of relationships between the `transactions` and `transfer_balances` tables, as well as verifying that business rules and constraints are met.

## Key distribution Expectations

Great Expectations provides several Expectations designed for validating relationships between data elements within a single table. However, if you want to validate data relationships across multiple tables, the current built-in Data Integrity Expectations won't work out of the box. To overcome this limitation, you have two options:

1. Create a view on the database that combines the tables you want to validate, and then use the built-in Expectations on that view.
2. Create custom SQL Expectations to validate relationships directly in the database.

In this section, we'll cover the first option by discussing built-in Expectations that can be applied to a combined view of multiple tables. Later, in the "Example: Validate cross-table balance integrity" section, we'll explore the second option, demonstrating how to create and use custom SQL Expectations for validating relationships across separate tables.

:::TODO:::

![Add an integrity Expectation in GX Cloud](integrity_resources/integrity_add_expectation.gif)

### Expect Column Pair Values To Be Equal

Validates that values in one column match corresponding values in another column.

**Use Case**: Verify that the reference number and confirmation code match for each transaction.

```python
gxe.ExpectColumnPairValuesToBeEqual(
    column_A="reference_number",
    column_B="confirmation_code"
)
```

<small>View `ExpectColumnPairValuesToBeEqual` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_column_pair_values_to_be_equal).</small>


### Expect Multicolumn Sum To Equal

Ensures that the sum of multiple columns equals an expected value, useful for validating financial calculations and balance checks.

**Use Case**: Validate sum-to-zero checks in the `transfer_balances` table.

```python
gxe.ExpectMulticolumnSumToEqual(
    column_list=["adjustment", "sender_debit", "recipient_credit"],
    sum_total=0.0
)
```

<small>View `ExpectMulticolumnSumToEqual` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_multicolumn_sum_to_equal).</small>


### Expect Column Pair Values A To Be Greater Than B

Verifies that values in one column are consistently greater than related values in another column.

**Use Case**: Ensure transfer amounts are always greater than or equal to adjustments.

```python
gxe.ExpectColumnPairValuesAToBeGreaterThanB(
    column_A="transfer_amount",
    column_B="adjustment",
    or_equal=True
)
```

<small>View `ExpectColumnPairValuesAToBeGreaterThanB` in the [Expectation Gallery](https://greatexpectations.io/expectations/expect_column_pair_values_a_to_be_greater_than_b).</small>

<br/>
<br/>

:::tip[GX tips for integrity Expectations]
- Use custom SQL Expectations when built-in Expectations don't cover complex business rules
- Combine multiple Expectations to create comprehensive integrity checks
- Consider performance implications when validating across large datasets
:::

## Example: Validate cross-table balance integrity

**Context**: In this example, we'll use the sample `transactions` and `transfer_balances` tables to demonstrate how to validate the integrity of transfer amounts, adjustments, and balances between related tables. Ensuring consistency across these tables is crucial for accurate financial reporting and auditing.

**Goal**: Using GX Cloud or GX Core, implement integrity validations that:
1. Ensure `transaction_id` is consistent between the `transactions` and `transfer_balances` tables
2. Verify that the `transfer_amount` in `transfer_balances` matches the absolute value of `sender_debit` for each transaction
3. Validate that `recipient_credit` equals `transfer_amount` plus `adjustment` for each record in `transfer_balances`

<Tabs
   defaultValue="gx_cloud"
   values={[
      {value: 'gx_cloud', label: 'GX Cloud'},
      {value: 'gx_core', label: 'GX Core'}
   ]}
>

<TabItem value="gx_cloud" label="GX Cloud">

Use the GX Cloud UI to implement the following steps:

1. Create Postgres Data Assets for both the `transactions` and `account_balances` tables using the connection string:
   ```
   postgresql+psycopg2://try_gx:try_gx@postgres.workshops.greatexpectations.io/gx_learn_data_quality
   ```

2. Add an **Expect column values to match those from another table** Expectation to validate `transaction_id` consistency:
   * Column: `transaction_id`
   * Reference table: `transactions`
   * Reference column: `transaction_id`

3. Add a Custom SQL Expectation to verify `transfer_amount` matches `sender_debit`:
   ```sql
   SELECT COUNT(*) = 0 FROM (
     SELECT t.transaction_id
     FROM transfer_balances t
     JOIN transactions x ON t.transaction_id = x.transaction_id
     WHERE t.transfer_amount != ABS(x.sender_debit)
   ) violations
   ```

4. Add another Custom SQL Expectation to validate `recipient_credit` calculation:
   ```sql
   SELECT COUNT(*) = 0 FROM (
     SELECT transaction_id
     FROM transfer_balances
     WHERE recipient_credit != (transfer_amount + adjustment)
   ) violations
   ```

5. Click **Validate** to run the integrity checks and analyze the results.

</TabItem>

<TabItem value="gx_core" label="GX Core">
Run the following GX Core workflow.

:::TODO replace this pseudo-code with proper GX Core

```
# Load data assets for transactions and transfer_balances tables
transactions_data_asset = load_data_asset("transactions")
transfer_balances_data_asset = load_data_asset("transfer_balances")

# Create validators for each data asset
transactions_validator = create_validator(transactions_data_asset)
transfer_balances_validator = create_validator(transfer_balances_data_asset)

# Define Expectation for transaction_id consistency
transfer_balances_validator.expect_column_values_to_match_those_from_a_different_table(
    column="transaction_id",
    reference_table=transactions_data_asset,
    reference_column="transaction_id"
)

# Implement custom SQL Expectation for transfer_amount validation
transfer_balances_validator.expect_custom_sql_query_to_have_result(
    query="SELECT COUNT(*) = 0 FROM (...JOIN query to check transfer_amount...)",
    result={'result': True}
)

# Implement custom SQL Expectation for recipient_credit validation
transfer_balances_validator.expect_custom_sql_query_to_have_result(
    query="SELECT COUNT(*) = 0 FROM (...query to check recipient_credit calculation...)",
    result={'result': True}
)

# Create and run Checkpoint with both validators
checkpoint = create_checkpoint(transactions_validator, transfer_balances_validator)
checkpoint_result = run_checkpoint(checkpoint)

# Review validation results and take action as needed
if not checkpoint_result.success:
    investigate_and_resolve_issues(checkpoint_result)
else:
    proceed_with_data_pipeline()
```

</TabItem>
</Tabs>

The validations in this example ensure that the `transaction_id` values match between the two tables, enforcing referential integrity. The custom SQL Expectations verify that the `transfer_amount` in `transfer_balances` aligns with the `sender_debit` in `transactions`, and that the `recipient_credit` is correctly calculated as the sum of `transfer_amount` and `adjustment`.

**GX solution**: Using either GX Cloud or GX Core, we can implement comprehensive integrity checks that span multiple tables and validate complex business rules. The combination of built-in Expectations and custom SQL validation provides the flexibility to handle sophisticated financial data quality requirements.

## Scenarios

These scenarios demonstrate how Great Expectations can help enforce data integrity across various domains. By combining built-in Expectations with custom SQL checks, organizations can create comprehensive validation frameworks that catch inconsistencies, prevent data quality issues, and ensure compliance with business rules and regulations.

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

- Neglecting to validate data across multiple systems: Many organizations focus on validating data within individual systems but fail to ensure consistency when data is integrated or transferred between systems. This can lead to discrepancies and inaccuracies that impact downstream processes and decision-making.

- Overlooking the importance of referential integrity: Failing to enforce referential integrity can result in orphaned records, invalid references, and data inconsistencies. Teams should prioritize validating relationships between tables and ensure that foreign key constraints are properly maintained.

- Relying solely on application-level validations: While application-level checks are important, they may not catch all data integrity issues, particularly when data is modified outside the application or when integrating data from external sources. Implementing database-level constraints and validations is crucial for maintaining data integrity.

- Inadequate handling of NULL values: NULL values can introduce ambiguity and complicate data integrity checks. Teams should establish clear policies for handling NULLs and ensure that validation rules account for their presence.

- Lack of comprehensive data quality monitoring: Data integrity issues can arise over time due to changes in source systems, data processing pipelines, or business rules. Implementing continuous data quality monitoring and alerting is essential for proactively identifying and addressing integrity problems before they impact downstream consumers.

- Insufficient testing of data transformations: Data transformations and ETL processes can introduce integrity issues if not thoroughly tested. Teams should validate the accuracy and consistency of transformed data, ensuring that business rules and relationships are preserved throughout the data pipeline.

## The path forward

Data integrity is a critical component of a comprehensive data quality strategy. By leveraging Great Expectations' built-in and custom validation capabilities, you can enforce integrity rules across your data landscape, ensuring consistency, accuracy, and compliance.

However, data integrity is not the only aspect of data quality. To build truly trustworthy data pipelines, you must also address [other data quality dimensions like missingness, distribution, and freshness](/reference/learn/data_quality_use_cases/dq_use_cases_lp.md). Start by prioritizing critical data assets and incrementally expand your validation coverage to encompass these dimensions.

Remember, maintaining data integrity is an ongoing process. Regular validation, monitoring, and issue resolution are crucial for sustaining data trust and driving better outcomes.

The key takeaway? Embrace data integrity validation as a foundational practice, and continually iterate on your data quality strategy to create a culture of trust and reliability. With Great Expectations, you have the tools to make it happen.

