---
title: 'Automating data quality rules'
description: Generate AI-recommended data quality rules and use Anomaly Detection to more quickly achieve test coverage for your data.
---

With GX Cloud, you can automatically generate data quality rules to more quickly achieve test coverage for your data. This page provides an overview of the following options:

- Automating [Anomaly Detection](#anomaly-detection) rules.
- Generating [personalized AI-recommended rules](#personalized-recommendations-with-expectai-beta).

## Anomaly Detection

When you [add a new Data Asset](/cloud/data_assets/manage_data_assets.md), GX Cloud by default generates Expectations to detect anomalies in the following data quality issues. You can also automate Anomaly Detection for these when you [add Expectations](/cloud/expectations/manage_expectations.md#add-an-expectation) for an existing Data Asset.

- [Schema](#schema)
- [Volume](#volume)
- [Completeness](#completeness)
- Uniqueness (coming soon)



### Schema

To detect schema anomalies, we automatically generate a rule to [**expect table columns to match set**](/reference/learn/data_quality_use_cases/schema.md#expect-table-columns-to-match-set) using the Data Asset’s initial columns as the set to match. If the number or names of columns in the Data Asset change, this Expectation will fail.

### Volume

To detect anomalies in row count, we automatically generate a rule to [**expect table row count to be between**](/reference/learn/data_quality_use_cases/volume.md#expect-table-row-count-to-be-between) a forecasted range that tests that the current validation run doesn’t deviate significantly from historical patterns. For example, if there is a sudden increase when volume has been stable or stagnation in a season when volume typically grows, then this Expectation will fail.


### Completeness

To detect completeness anomalies, we automatically generate rules for every column to [**expect column values to not be null**](/reference/learn/data_quality_use_cases/missingness.md#expect-column-values-to-not-be-null) and/or [**expect column values to be null**](/reference/learn/data_quality_use_cases/missingness.md#expect-column-values-to-be-null). The Expectation(s) and parameters for a column depend on the column's initial null percentage.

- If a column initially has no null values, GX generates one completeness Expectation to test that the column continues to have 100% non-null values.
- If a column initially has all null values, GX generates one completeness Expectation to test that the column continues to have 100% null values.
- If a column starts with a mix of null and non-null values, GX generates two completeness Expectations with dynamic parameters to test that the null percentage stays close to the average of the last 5 Validation runs.

If the null percentage changes at all for a column that started with all null values or no null values, its generated completeness Expectation will fail. If the null percentage changes a bit for a column that started with a mix of null and non-null values, its generated completeness Expectations will pass; if the change is drastic, one of the generated completeness Expectations will fail. Which one fails depends on whether the null percentage increased or decreased.



## Personalized recommendations with ExpectAI <span class="beta">Beta</span>

[ExpectAI (BETA)](/cloud/expectations/manage_expectations.md#generate-expectations-with-expectai-beta) performs deep analysis on a given Data Asset to set Expectations based on patterns in the data. These AI-recommended data quality rules are sometimes based on anomalies detected in the data, so they may fail on the first validation to bring your attention to potential problems.  

