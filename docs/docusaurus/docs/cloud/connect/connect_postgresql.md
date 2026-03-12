---
sidebar_label: 'Connect GX Cloud to PostgreSQL'
title: 'Connect GX Cloud to PostgreSQL'
description: Connect GX Cloud to a PostgreSQL Data Source.
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

## Prerequisites

- You have a [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/cloud/access/manage_access.md#roles-and-permissions) or greater.

- You have a PostgreSQL database, schema, and table or view.

- Optional. [pgAdmin](https://www.pgadmin.org/download/).


## Connect to a PostgreSQL Data Source and add a Data Asset

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets** > **New Data Asset** > **New Data Source** > **PostgreSQL**.

2. Enter a meaningful name for the Data Source in the **Data Source name** field.

3. Enter a connection string in the **Connection string** field. The connection string format is:
   
   ```python title="PostgreSQL connection string"
   postgresql+psycopg2://YourUserName:YourPassword@YourHostName:5432/YourDatabaseName?options=-csearch_path%3DYourSchemaName
   ```

4. Click **Connect**.

5. Select one or more tables or views to import as Data Assets.

6. Click **Add x Asset(s)**.

7. Decide which [Anomaly Detection](/docs/cloud/overview/accelerating_test_coverage.md#anomaly-detection) options you want to enable. By default, GX Cloud adds [warning-severity](/docs/cloud/expectations/expectations_overview.md#failure-severity) Expectations to detect **Schema** and **Volume** anomalies. You can de-select recommendations you’d like to opt out of. You can choose to generate Expectations to detect **Completeness** anomalies.

8. Click **Start monitoring** or **Finish**.


## Next steps

- [Add an Expectation](/cloud/expectations/manage_expectations.md#add-an-expectation)
- [Run a Validation](/cloud/validations/run_validations.md)
- [Configure an alert](/cloud/alerts/alert_about_failures.md)


