---
sidebar_label: 'Connect GX Cloud to Databricks SQL'
title: 'Connect GX Cloud to Databricks SQL'
description: Connect GX Cloud to a Databricks SQL Data Source.
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

## Prerequisites

- You have a [GX Cloud account](https://greatexpectations.io/cloud) with [Admin or Editor permissions](/cloud/users/manage_users.md#roles-and-responsibilities).

- You have a Databricks SQL catalog, schema, and table.

- Optional. To improve data security, GX recommends creating a separate Databricks SQL [service principal](https://docs.databricks.com/en/admin/users-groups/service-principals.html#manage-service-principals-in-your-account) for your GX Cloud connection.

## Connect to a Databricks SQL Data Source and add a Data Asset

1. In GX Cloud, click **Data Assets** > **New Data Asset** > **New Data Source** > **Databricks SQL**.

2. Enter a meaningful name for the Data Source in the **Data Source name** field.

3. Enter a connection string in the **Connection string** field. The connection string format is:

   ```python title="Databricks SQL connection string"
   databricks://token:{token}@{host}:{port}?http_path={http_path}&catalog={catalog}&schema={schema}
   ```

   If you created a separate Databricks SQL service principal for your GX Cloud connection as recommended above, use those credentials in the connection string. 

4. Click **Connect**.

5. Select one or more tables to import as Data Assets.

6. Decide if you want to **Generate Expectations that detect column changes in selected Data Assets**.

7. Click **Add x Asset(s)**. 

8. Add an Expectation. See [Add an Expectation](/cloud/expectations/manage_expectations.md#add-an-expectation).