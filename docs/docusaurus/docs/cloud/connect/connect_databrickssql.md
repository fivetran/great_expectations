---
sidebar_label: 'Connect GX Cloud to Databricks SQL'
title: 'Connect GX Cloud to Databricks SQL'
description: Connect GX Cloud to a Databricks SQL Data Source.
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

## Prerequisites

- You have a [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/cloud/access/manage_access.md#roles-and-permissions) or greater.

- You have a Databricks SQL catalog, schema, and table or view.

- Optional. To improve data security, GX recommends creating a separate Databricks SQL [service principal](https://docs.databricks.com/en/admin/users-groups/service-principals.html#manage-service-principals-in-your-account) for your GX Cloud connection.

## Connect to a Databricks SQL Data Source and add a Data Asset

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets** > **New Data Asset** > **New Data Source** > **Databricks SQL**.

2. Enter a meaningful name for the Data Source in the **Data Source name** field.

3. Enter a connection string in the **Connection string** field. The connection string format is:

   ```python title="Databricks SQL connection string"
   databricks://token:{token}@{host}:{port}?http_path={http_path}&catalog={catalog}&schema={schema}
   ```

   If you created a separate Databricks SQL service principal for your GX Cloud connection as recommended above, use those credentials in the connection string. 

4. Click **Connect**.

5. Select one or more tables or views to import as Data Assets.

6. Click **Add x Asset(s)**.

7. Decide which [Anomaly Detection](/docs/cloud/overview/accelerating_test_coverage.md#anomaly-detection) options you want to enable. By default, GX Cloud adds [warning-severity](/docs/cloud/expectations/expectations_overview.md#failure-severity) Expectations to detect **Schema** and **Volume** anomalies. You can de-select recommendations you’d like to opt out of. You can choose to generate Expectations to detect **Completeness** anomalies.

8. Click **Start monitoring** or **Finish**.


## Next steps

- [Add an Expectation](/cloud/expectations/manage_expectations.md#create-an-expectation).
- [Run a Validation](/cloud/validations/run_validations.md)
- [Configure an alert](/cloud/alerts/manage_email_alerts.md)
