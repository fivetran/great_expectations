---
sidebar_label: 'Connect GX Cloud to PostgreSQL'
title: 'Connect GX Cloud to PostgreSQL'
description: Connect GX Cloud to a PostgreSQL Data Source.
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

## Prerequisites

- You have a [GX Cloud account](https://greatexpectations.io/cloud) with [Admin or Editor permissions](/cloud/users/manage_users.md#roles-and-responsibilities).

- You have a PostgreSQL database, schema, and table.

- Optional. To improve data security, GX recommends creating a separate PostgreSQL user for your GX Cloud connection.

- Optional. [pgAdmin](https://www.pgadmin.org/download/).

## Optional. Create a separate PostgreSQL user

1. In pgAdmin, select a database.

2. Click **Tools** > **Query Tool**.

3. Paste the following code into the **Query** pane to create and assign the `gx_role` role and allow GX Cloud to access all `public` schemas and tables on a specific database.

   ```sql title="pgAdmin"
    -- Create and assign the gx_role role and allow GX Cloud 
    -- to access all public schemas and tables on a specific database
    CREATE ROLE gx_role WITH LOGIN PASSWORD '<your_password>';
    GRANT CONNECT ON DATABASE <your_database> TO gx_role;
    GRANT USAGE ON SCHEMA public TO gx_role;
    GRANT SELECT ON ALL TABLES in SCHEMA public TO gx_role;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO gx_role
   ```

   - Replace `<your_password>` and `<your_database>` with your own values.
   - `ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO gx_role;` is optional and gives the `gx_role` user access to all future tables in the defined schema.

4. Click **Execute/Refresh**.

## Connect to a PostgreSQL Data Source and add a Data Asset

1. In GX Cloud, click **Data Assets** > **New Data Asset** > **New Data Source** > **PostgreSQL**.

2. Enter a meaningful name for the Data Source in the **Data Source name** field.

3. Enter a connection string in the **Connection string** field. The connection string format is:
   
   ```python title="PostgreSQL connection string"
   postgresql+psycopg2://YourUserName:YourPassword@YourHostName:5432/YourDatabaseName
   ```
   
   If you created a separate PostgreSQL user for your GX Cloud connection as recommended above, use those credentials in the connection string.

4. Click **Connect**.

5. Select one or more tables to import as Data Assets.

6. Decide if you want to **Generate Expectations that detect column changes in selected Data Assets**.

7. Click **Add x Asset(s)**. 

8. Add an Expectation. See [Add an Expectation](/cloud/expectations/manage_expectations.md#add-an-expectation).

