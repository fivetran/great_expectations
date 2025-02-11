# Automating data quality rules

With GX Cloud, you can automatically generate data quality rules to more quickly achieve test coverage for your data. This page provides an overview of options for automating data quality rules.

- You can generate basic rules as part of adding a new Data Asset.
- You can generate personalized AI-recommened rules for an existing Data Asset.

## Monitor common issues

When you [add a new Data Asset](/cloud/data_assets/manage_data_assets.md#add-a-data-asset-from-a-new-data-source), GX Cloud by default automatically generates Expectations to test the following common data quality issues.
- [Schema](#schema)
- [Volume](#volume)
- Completeness (coming soon)
- Uniqueness (coming soon)


### Schema

To detect schema changes, we automatically generate a rule to **expect table columns to match set** using the Data Asset’s initial columns as the set to match. If the number or names of columns in the Data Asset change, this Expectation will fail.

### Volume

To detect non-increasing volume, we automatically generate a rule to **expect table row count to be between** with dynamic parameters that test that the current validation run has more rows than the previous run. If the row count shrinks or stays the same between runs, this Expectation will fail.

## Personalize recommendations with ExpectAI (BETA)

[ExpectAI (BETA)](/cloud/expectations/manage_expectations.md#generate-expectations-with-expectai-beta) performs deep analysis on a given Data Asset to set Expectations based on patterns in the data. These AI-recommended data quality rules are sometimes based on anomalies detected in the data, so they may fail on the first validation to bring your attention to potential problems.  

