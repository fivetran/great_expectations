---
sidebar_label: 'Connect GX Cloud to Snowflake'
title: 'Connect GX Cloud to Snowflake'
description: Connect GX Cloud to a Snowflake Data Source.
---

## Prerequisites

- You have a [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/cloud/access/manage_access.md#roles-and-permissions) or greater.
- You have a Snowflake database, schema, and table or view.
- You have a [Snowflake account](https://docs.snowflake.com/en/user-guide-admin) with USAGE privileges on the table or view, database, and schema you are validating, and you have SELECT privileges on the table or view you are validating.
- You have [configured and stored an unencrypted private key and public key](https://docs.snowflake.com/en/user-guide/key-pair-auth) for Snowflake key-pair authentication.
   :::warning Password authentication is deprecated
   Snowflake has deprecated password authentication and will remove support for it entirely in the future. Set up new Data Sources with key-pair authentication. If you have older Snowflake Data Sources using password authentication, update them to use key-pair authentication. For more information about the deprecation, see [Snowflake's documentation](https://docs.snowflake.com/en/user-guide/security-mfa-rollout).
   :::

## Connect to a Snowflake Data Source and add a Data Asset

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets** > **New Data Asset** > **New Data Source** > **Snowflake**.

2. Enter a meaningful name for the Data Source in the **Data Source name** field.

3. Confirm that you are entering your **Connection details** as **Input parameters** using **Key-pair** authentication.

4. Supply your connection details.

   - **Account identifier**: Enter your Snowflake organization and account name separated by a hyphen (`oraganizationname-accountname`) or your account name and a legacy account locator separated by a period (`accountname.region`). The legacy account locator value must include the geographical region. For example, `us-east-1`. 
    
      To locate your Snowflake organization name, account name, or legacy account locator values see [Finding the Organization and Account Name for an Account](https://docs.snowflake.com/en/user-guide/admin-account-identifier#finding-the-organization-and-account-name-for-an-account) or [Using an Account Locator as an Identifier](https://docs.snowflake.com/en/user-guide/admin-account-identifier#using-an-account-locator-as-an-identifier).
    
   - **Username**: Enter the username you use to access Snowflake.

   - **Private key**: Enter your unencrypted private key value. Do not include the start and end markers `-----BEGIN/END PRIVATE KEY-----`.

   - **Database**: Enter the name of the Snowflake database where the data you want to validate is stored. In Snowsight, click **Data** > **Databases**. In the Snowflake Classic Console, click **Databases**.
 
   - **Schema**: Enter the name of the Snowflake schema where the data you want to validate is stored.

   - **Warehouse**: Enter the name of your Snowflake database warehouse. In Snowsight, click **Admin** > **Warehouses**. In the Snowflake Classic Console, click **Warehouses**.

   - **Role**: Enter your Snowflake role.
   
5. Click **Connect**.

6. Select one or more tables or views to import as Data Assets.

7. Click **Add x Asset(s)**.

8. Decide which [Anomaly Detection](/docs/cloud/overview/accelerating_test_coverage.md#anomaly-detection) options you want to enable. By default, GX Cloud adds [warning-severity](/docs/cloud/expectations/expectations_overview.md#failure-severity) Expectations to detect **Schema** and **Volume** anomalies. You can de-select recommendations you’d like to opt out of. You can choose to generate Expectations to detect **Completeness** anomalies.

9. Click **Start monitoring** or **Finish**.


## Next steps

- [Add an Expectation](/cloud/expectations/manage_expectations.md#create-an-expectation)
- [Run a Validation](/cloud/validations/run_validations.md)
- [Configure an alert](/cloud/alerts/alert_about_failures.md)


