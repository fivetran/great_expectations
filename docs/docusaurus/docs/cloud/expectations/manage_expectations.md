---
sidebar_label: "Manage Expectations"
title: "Manage Expectations"
description: Create and manage Expectations in GX Cloud.
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

You can manually create Expectations via both the UI and API, and use several different GX Cloud features to generate Expectations via the UI.

This page provides instructions for working with Expectations. To learn about Expectation types and options, see the [Expectations overview](/cloud/expectations/expectations_overview.md). To learn about the Expectation changelog at the Data Asset level, visit [Manage Data Assets](/cloud/data_assets/manage_data_assets.md#view-data-asset-history).

## Create an Expectation

<Tabs 
   queryString="expectations-interface"
   defaultValue="ui"
   values={[
      {value: 'ui', label: 'UI'},
      {value: 'api', label: 'API'}
   ]}
>

<TabItem value="ui" label="UI">

You must have a [Data Asset](/cloud/data_assets/manage_data_assets.md) before creating an Expectation.

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. In the **Data Assets** list, click the Data Asset name.

3. Click **New Expectation**.

4. Select a data quality issue to test for or an option for writing your own test.

   :::tip Options for accelerating test coverage
   If you are using a [supported Data Source](/docs/cloud/data_sources/manage_data_sources), you can use the following to speed up test creation:
   - If you selected the **Schema**, **Volume**, or **Completeness** data quality issue, you will have the **Automatic** option to generate Expectations for [Anomaly Detection](/cloud/overview/accelerating_test_coverage.md#anomaly-detection). Generated Expectations will default to warning severity, which you can edit later. If you instead want to create your own rules, click **Manual**.
   - If you selected custom **SQL**, you will have the option to **Generate SQL** with [ExpectAI](#generate-sql). You can write your own SQL if you prefer.
   :::

5. Select an Expectation type.

6. Complete the mandatory and optional fields for the Expectation.

7. Click **Save** or click **Save & Add More** and then repeat steps 4 through 7 to add additional Expectations.

8. Optional. [Run an ad hoc Validation](/cloud/validations/run_validations.md).

9. Optional. Configure recurring Validations. See [Manage schedules](/docs/cloud/schedules/manage_schedules).

</TabItem>

<TabItem value="api" label="API">

You must have the following prerequisites fulfilled before creating an Expectation:

- Your [Cloud credentials](/cloud/connect/connect_python.md#get-your-credentials) saved in your [environment variables](/cloud/connect/connect_python.md#set-your-credentials-as-environment-variables).
- [Python version 3.10 to 3.13](https://www.python.org/downloads/).
- [An installation of the Great Expectations Python library](https://pypi.org/project/great-expectations/).

Follow the steps below to configure an Expectation and add it to an Expectation Suite:

1. Create a Data Context object.

   ```python title="Python" name="docs/docusaurus/docs/cloud/expectations/examples/create_an_expectation_for_cloud.py - get cloud context" 
   ```

2. Choose an Expectation to create.

   GX Cloud comes with many Expectations to cover your data quality needs. You can find a catalog of these Expectations in the [Expectation Gallery](https://greatexpectations.io/expectations/). When browsing the Expectation Gallery, you can filter the available Expectations by the data quality issue they address and by the Data Sources they support. There is also a search bar that will let you filter Expectations by matching text in their name or description.

3. Determine the Expectation's required parameters.

   To determine the parameters your Expectation uses to evaluate data, reference the Expectation's entry in the [Expectation Gallery](https://greatexpectations.io/expectations/).  Under the **Args** section you will find a list of parameters that are necessary for the Expectation to be evaluated, along with a description of the value(s) that should be provided.

4. Optional. Determine the Expectation's other parameters.

   In addition to the parameters that are required for an Expectation to evaluate data, Expectations also support some optional parameters.  In the Expectations Gallery these are found under each Expectation's **Other Parameters** section.

   Examples of these parameters are:
   - `meta`: A dictionary of user-supplied metadata to store with an Expectation. This dictionary can be used to add notes about the purpose and intended use of an Expectation.
   - `mostly`: A special argument that allows for _fuzzy_ validation based on a percentage of successfully validated rows. If the percentage is at least the value set in the `mostly` parameter, the Expectation will return a `success` value of `true`.
   - `severity`: Indicates the impact of the Expectation failing. Accepted values are `critical`, `warning`, or `info`. Defaults to `critical` if not explicitly set. You can [trigger Actions](/cloud/alerts/trigger_actions.md) based on severity levels or you can condition your data pipeline with the `get_maximum_severity_failure` helper method in the [`ExpectationSuiteValidationResult` class](/reference/api/core//ExpectationSuiteValidationResult_class.mdx). Note that if an Expectation fails to execute, the failure will be recorded as critical, regardless of the Expectation configuration, to bring your attention to the fact that your data is not being tested as intended.

   <details>
      <summary>Restrict an Expectation to specific rows</summary>

      To restrict an Expectation to a subset of the data retrieved in a Batch, use the `row_condition` argument. The `row_condition` argument takes a boolean expression built with Python objects. Rows will be validated for the Expectation when the `row_condition` expression evaluates to `True`. Conversely, if the `row_condition` evaluates to `False`, the corresponding row will not be validated for the Expectation.


      To support complex business use cases, logical clauses can be combined with AND / OR relationships within the `row_condition` argument.

      ```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/row_conditions.py - determine expression"
      ```

   An Expectation can have up to 100 condition statements grouped in any number of condition blocks.

      Here are some examples of how to create common patterns in row conditions:

      - **A and B**.
         ```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/row_conditions.py - a and b"
         ```

      - **A or B**.
         ```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/row_conditions.py - a or b"
         ```

      - **(A and B) or (C and D)**.
         ```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/row_conditions.py - a and b or c and d"
         ```

      - **A and (B or C)**. This pattern is not supported verbatim, but you can achieve the same result with **(A and B) or (A and C)**.
         ```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/row_conditions.py - a and b or c"
         ```

      The following comparison operators are supported: `==`, `!=`, `>`, `<`, `>=`, `<=`, `is_in`, `is_not_in`, `is_null`, `is_not_null`. Here are some examples of using different kinds of operators:

      ```python title="Python" name="docs/docusaurus/docs/core/customize_expectations/_examples/row_conditions.py - operators"
      ```


   Expectations that have different row conditions are treated as unique, even if they are of the same type, apply to the same column, and belong to the same Expectation Suite. This allows you to validate your data through multiple lenses.

   Note that the following Expectations do not accept the `row_condition` argument:
      - `expect_column_to_exist`
      - `expect_query_results_to_match_comparison`
      - `expect_table_columns_to_match_ordered_list`
      - `expect_table_columns_to_match_set`
      - `expect_table_column_count_to_be_between`
      - `expect_table_column_count_to_equal`
      - `unexpected_rows_expectation`
   </details>

5. Create the Expectation.
  
   Using the Expectation class you picked and the parameters you determined when referencing the Expectation Gallery, you can create your Expectation.

   In this example, the `ExpectColumnMaxToBeBetween` Expectation is created with a range of acceptable values that will be evaluated inclusively. 

      ```python title="Python" name="docs/docusaurus/docs/cloud/expectations/examples/create_an_expectation_for_cloud.py - preset expectation"
      ```

6. Create or get an Expectation Suite.

   An Expectation Suite is used to group Expectations. All Expectations need to be added to an Expectation Suite before they can be associated with a Data Asset via a Validation Definition. All of the Expectations that are grouped within an Expectation Suite will be evaluated together whenever the Validation Definition runs.

   Create an Expectation Suite and add it to your Data Context:
      ```python title="Python" name="docs/docusaurus/docs/cloud/expectations/examples/create_an_expectation_for_cloud.py - create expectation suite"
      ```

   Optional. If you already have an API-managed Expectation Suite, get it from your Data Context:

      ```python title="Python" name="docs/docusaurus/docs/cloud/expectations/examples/create_an_expectation_for_cloud.py - get expectation suite"
      ```

7. Add the Expectation to the Expectation Suite.

      ```python title="Python" name="docs/docusaurus/docs/cloud/expectations/examples/create_an_expectation_for_cloud.py - add expectation to suite"
      ```
   
8.  If your Expectation Suite is not yet associated with a Data Asset through a Validation Definition, you must set up this relationship before you can validate your Expectations. Visit [Run Validations](/docs/cloud/validations/run_validations/#api-managed-expectations-entire-asset) to learn how to do so.

</TabItem>
</Tabs>

## Save time with ExpectAI

ExpectAI is an analytical AI tool that you can use to generate tests.

### Generate Expectations

To accelerate test coverage, you can use ExpectAI to generate recommended Expectations for a Data Asset. These will be personalized based on an analysis of a sample of your data.

Keep the following requirements in mind when working with ExpectAI:
- The Data Asset's Data Source must be AlloyDB, Amazon Aurora PostgreSQL, Citus, Databricks SQL, Neon, PostgreSQL, Redshift, or Snowflake.
- Generated Expectations will default to warning severity, which you can edit later.
- If your organization is using an [agent-enabled deployment](/cloud/deploy/deployment_patterns.md), you must [deploy the GX Agent](/cloud/deploy/deploy_gx_agent.md#deploy-the-gx-agent) with credentials for your own LLM.

To add AI-recommended Expectations:
1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.
2. In the **Data Assets** list, click the Data Asset name.
3. Click **Generate Expectations**.
   :::note This might take a few minutes
   ExpectAI may take a few minutes to analyze your data and recommend personalized Expectations. You can navigate away from the page while ExpectAI works in the background. GX will send an email when your recommended Expectations are ready for review.
   :::
4. Review the recommended Expectations and **Approve** (✓) or **Reject** (✗) them within 48 hours. After 48 hours, any remaining recommendations will be discarded.
5. Optional. [Run an ad hoc Validation](/cloud/validations/run_validations.md).
6. Optional. [Edit](#edit-an-expectation) AI-generated Expectations based on the insights you get from running a Validation and your data quality needs.

### Generate SQL

To simplify working with [custom SQL Expectations](/cloud/expectations/expectations_overview.md#custom-sql-expectations), you can use ExpectAI to generate a SQL query based on a natural language prompt you provide and a data profile GX Cloud automatically provides.

For example, imagine you have a New York City taxi trip dataset with columns named `pickup_borough`, `vehicle_type`, and `passenger_count`. If you [add a custom SQL Expectation](#create-an-expectation) with a **Prompt for SQL generation** like `sedan rides in Manhattan shouldn't have more than 4 passengers` then ExpectAI would generate a SQL query similar to the following:

```sql title="SQL query"
SELECT
*
FROM
{batch}
WHERE
pickup_borough = 'Manhattan'
AND vehicle_type = 'Sedan'
AND passenger_count > 4
```

Keep the following requirements in mind when working with ExpectAI:
- The Data Asset's Data Source must be AlloyDB, Amazon Aurora PostgreSQL, Citus, Databricks SQL, Neon, PostgreSQL, Redshift, or Snowflake.
- If your organization is using an [agent-enabled deployment](/cloud/deploy/deployment_patterns.md), you must [deploy the GX Agent](/cloud/deploy/deploy_gx_agent.md#deploy-the-gx-agent) with credentials for your own LLM.

## Edit an Expectation

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. In the **Data Assets** list, click the Data Asset name.

3. Find the Expectation that you want to edit.

4. Click <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/> **Edit Expectation** for the Expectation that you want to edit.

5. Edit the Expectation configuration.

6. Click **Save**.

:::note Severity changes apply going forward
If you edit the **Severity** of an Expectation, note that historical validation results will continue to indicate the severity that was recorded at the time of an Expectation failure. The newly assigned severity will apply to future validation failures only. 
:::

## Delete an Expectation

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. In the **Data Assets** list, click the Data Asset name.

3. Find the Expectation that you want to delete.

4. Click <img src="/img/trash.png" alt="trash icon" width="20" height="20"/> **Delete Expectation** for the Expectation that you want to delete.

   :::tip You can delete Expectations in bulk
    If you want to delete all Expectations that test for a certain data quality issue, you can instead click <img src="/img/trash.png" alt="trash icon" width="20" height="20"/> **Bulk-delete Expectations** for the relevant category.
    :::

5. Click **Delete**.


