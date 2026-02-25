---
title: 'Accelerating test coverage'
description: Use automations and AI to more quickly achieve test coverage for your data.
---

GX Cloud provides several conveniences to help you more quickly achieve test coverage for your data. This page provides an overview of the following options:

- Automating [Anomaly Detection](#anomaly-detection) rules.
- Generating [personalized AI-recommended rules](#personalized-ai-recommended-rules).
- Generating [code for custom SQL Expectations](#code-for-custom-sql-expectations). 

:::note Data Source support
Some options aren't supported for some Data Sources. See [Manage Data Sources](/docs/cloud/data_sources/manage_data_sources.md#workflow-and-feature-support) for details.
:::

## Anomaly Detection

When you [add a new Data Asset](/cloud/data_assets/manage_data_assets.md) with the GX Cloud UI, you can have GX Cloud generate Expectations to detect anomalies in the following data quality issues. You can also automate Anomaly Detection for these when you [add Expectations](/cloud/expectations/manage_expectations.md#create-an-expectation) with the GX Cloud UI for an existing Data Asset.

- [Schema](#schema)
- [Volume](#volume)
- [Completeness](#completeness)
- Uniqueness (coming soon)



### Schema

To detect schema anomalies, we generate a rule to [**expect table columns to match set**](/reference/learn/data_quality_use_cases/schema.md#expect-table-columns-to-match-set) using the Data Asset’s initial columns as the set to match. If the number or names of columns in the Data Asset change, this Expectation will fail.

### Volume

To detect anomalies in row count, we generate a rule to [**expect table row count to be between**](/reference/learn/data_quality_use_cases/volume.md#expect-table-row-count-to-be-between) a forecasted range that tests that the current validation run doesn’t deviate significantly from historical patterns. For example, if there is a sudden increase when volume has been stable or stagnation in a season when volume typically grows, then this Expectation will fail.


### Completeness

To detect completeness anomalies, we generate rules for every column to [**expect column proportion of non-null values to be between**](/reference/learn/data_quality_use_cases/missingness.md#expect-column-proportion-of-non-null-values-to-be-between) a forecasted range that depends on the column's initial proportion of non-null values.

- If a column initially has no null values, GX Cloud generates a rule to test that the column continues to have no null values.
- If a column initially has all null values, GX Cloud generates a rule to test that the column continues to have all null values.
- If a column starts with a mix of null and non-null values, GX Cloud generates a rule that tests that the current validation run doesn’t deviate significantly from historical patterns.

If the proportions change at all for a column that started with all null values or no null values, its generated completeness Expectation will fail. If the proportions change a bit for a column that started with a mix of null and non-null values, its generated completeness Expectation will pass; if the change is drastic, the generated completeness Expectation will fail.

## ExpectAI
ExpectAI is an analytical AI tool that powers several features in GX Cloud.


### Personalized AI-recommended rules
When you [generate Expectations](/cloud/expectations/manage_expectations.md#generate-expectations), ExpectAI performs deep analysis on a given Data Asset to set Expectations based on patterns in the data. These AI-recommended data quality rules are sometimes based on anomalies detected in the data, so they may fail on the first validation to bring your attention to potential problems.  

### Code for custom SQL Expectations
To simplify working with [custom SQL Expectations](/cloud/expectations/expectations_overview.md#custom-sql-expectations), you can use ExpectAI to generate a SQL query based on a natural language prompt you provide and a data profile GX Cloud automatically provides.


