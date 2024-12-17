---
sidebar_label: 'Connect GX Cloud to Snowflake'
title: 'Connect GX Cloud to Snowflake'
description: Connect GX Cloud to a Snowflake Data Source.
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

## Prerequisites

- You have a [GX Cloud account](https://greatexpectations.io/cloud) with [Admin or Editor permissions](/cloud/users/manage_users.md#roles-and-responsibilities).

- You have a Snowflake database, schema, and table.

- You have a [Snowflake account](https://docs.snowflake.com/en/user-guide-admin) with USAGE privileges on the table, database, and schema you are validating, and you have SELECT privileges on the table you are validating.
   - Optional. To improve data security, GX recommends using a separate Snowflake user service account to connect to GX Cloud.
   - Optional. To streamline automations and improve security, you can connect to Snowflake with key-pair authentication instead of a password. Note that this requires using GX Core in combination with GX Cloud.

- Optional. You can use an existing Snowflake warehouse, but GX recommends creating a separate warehouse for GX Cloud to simplify cost management and optimize performance.

## Optional. Create a separate Snowflake user and warehouse

Depending on your Snowflake permissions, you may need to ask an admin on your team to create a separate Snowflake user for your GX Cloud connection.

1. In Snowflake Snowsight, click **Projects** > **Worksheets** > **Add** > **SQL Worksheet**.

2. Paste the following code into the SQL worksheet.

   ```sql title="Snowflake Snowsight"
   use role accountadmin;
   create user if not exists gx_user password='<YOUR_PASSWORD>';
   create role if not exists gx_role;
   grant role gx_role to user gx_user;

   -- GX recommends creating a separate warehouse for GX Cloud to simplify cost 
   -- management and optimize resource consumption. 
   create warehouse if not exists gx_wh
   warehouse_size=xsmall
   auto_suspend=10
   auto_resume=true
   initially_suspended=true;
   grant usage, operate on warehouse gx_wh to role gx_role; 

   -- Replace <YOUR_DATABASE> and <YOUR_SCHEMA> with the names of the databases
   -- and schemas you want to test in GX Cloud.
   grant usage on database <YOUR_DATABASE> to role gx_role;
   grant usage on schema <YOUR_DATABASE>.<YOUR_SCHEMA> to role gx_role;
   grant select on all tables in schema <YOUR_DATABASE>.<YOUR_SCHEMA> to role gx_role;
   grant select on future tables in schema <YOUR_DATABASE>.<YOUR_SCHEMA> to role gx_role; 
   -- Gives the user with the gx_role role access to all future tables in the defined schema.
   ```

   - Replace `YOUR_PASSWORD` with your value and `YOUR_DATABASE` and `YOUR_SCHEMA` with the names of the database and schema you want to access in GX Cloud.
   - `grant select on future tables in schema <YOUR_DATABASE>.<YOUR_SCHEMA> to role gx_role;` is optional and gives the user with the `gx_role` role access to all future tables in the defined schema.
   - The settings in the code example optimize cost and performance. Adjust them to suit your business requirements.

3. Select **Run All** to define your user password, create a new GX role (`gx_role`), assign the password and role to a new user (`gx_user`), create a new warehouse (`gx_wh`), and allow the user with the `gx_role` role to access data on the Snowflake database and schema.

   ![Snowflake Run All](/img/run_all.png)


## Connect to a Snowflake Data Source and add a Data Asset

:::tip To connect with key-pair authentication, use GX Core
To connect to a Snowflake Data Source using key-pair authentication instead of a password, do the following using GX Core: 

1. [Create a Cloud Data Context](/core/set_up_a_gx_environment/create_a_data_context.md?context_type=gx_cloud).
2. Pass your private key when you [create a Data Source](/core/connect_to_data/sql_data/sql_data.md) in the Cloud Data Context.

Then, you can use GX Cloud to [add a Data Asset](/cloud/data_assets/manage_data_assets.md#add-a-data-asset-from-an-existing-data-source) from that Data Source.
:::

1. In GX Cloud, click **Data Assets** > **New Data Asset** > **New Data Source** > **Snowflake**.

2. Enter a meaningful name for the Data Source in the **Data Source name** field.

3. Select whether you will enter your connection details as either separate **Input parameters** or a consolidated **Connection string**.

4. Supply your connection details depending on the method you chose in the previous step.  If you created a separate Snowflake user for your GX Cloud connection as recommended above, use those credentials in your connection details.

   - If you chose **Input parameters**, complete the following fields:

      - **Account identifier**: Enter your Snowflake organization and account name separated by a hyphen (`oraganizationname-accountname`) or your account name and a legacy account locator separated by a period (`accountname.region`). The legacy account locator value must include the geographical region. For example, `us-east-1`. 
    
         To locate your Snowflake organization name, account name, or legacy account locator values see [Finding the Organization and Account Name for an Account](https://docs.snowflake.com/en/user-guide/admin-account-identifier#finding-the-organization-and-account-name-for-an-account) or [Using an Account Locator as an Identifier](https://docs.snowflake.com/en/user-guide/admin-account-identifier#using-an-account-locator-as-an-identifier).
    
      - **Username**: Enter the username you use to access Snowflake.

      - **Password**: Enter a Snowflake password. To improve data security, GX recommends using a Snowflake service account to connect to GX Cloud.

      - **Database**: Enter the name of the Snowflake database where the data you want to validate is stored. In Snowsight, click **Data** > **Databases**. In the Snowflake Classic Console, click **Databases**.
 
      - **Schema**: Enter the name of the Snowflake schema (table) where the data you want to validate is stored.

      - **Warehouse**: Enter the name of your Snowflake database warehouse. In Snowsight, click **Admin** > **Warehouses**. In the Snowflake Classic Console, click **Warehouses**.

      - **Role**: Enter your Snowflake role.

   - If you chose **Connection string** enter it with a format of:

      ```python title="Snowflake connection string"
      snowflake://<USER>:<PASSWORD>@<ACCOUNT_IDENTIFIER>/<DATABASE>/<SCHEMA>?warehouse=<WAREHOUSE>&role=<ROLE>
      ```
   
5. Click **Connect**. 

6. Select one or more tables to import as Data Assets.

7. Decide if you want to **Generate Expectations that detect column changes in selected Data Assets**.

8. Click **Add x Asset(s)**. 

9. Add an Expectation. See [Add an Expectation](/cloud/expectations/manage_expectations.md#add-an-expectation).


