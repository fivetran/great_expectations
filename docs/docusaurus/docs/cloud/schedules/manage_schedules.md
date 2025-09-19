---
sidebar_label: 'Manage schedules'
title: 'Manage schedules'
description: Create and manage schedules for Validations in GX Cloud.
---

Use a schedule to automate data quality checks with GX-managed Expectations. When you add your first Expectation in the GX Cloud UI for a Data Asset, including when you choose to auto-generate Expectations for Anomaly Detection, we enable a default schedule for that Asset's GX-managed Expectations. By default, GX-managed Expectations are scheduled to run every 24 hours. The first run will be at the start of the next hour after you add your first Expectation in the Cloud UI. You can keep the default schedule, edit it, or disable it.

:::note Schedules are for GX-managed Expectations only
To automate data quality checks for [API-managed Expectations](/cloud/expectations/manage_expectations.md#gx-managed-vs-api-managed-expectations), use an [orchestrator](/cloud/connect/connect_airflow.md).
:::


## Edit a schedule

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. In the **Data Assets** list, click the Data Asset name.

3. Next to the current schedule, click <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/> **Edit schedule**.

4. Change the **Frequency** and/or the **Start time** for the first run of the new schedule.

5. Click **Save**.

## Disable a schedule

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. In the **Data Assets** list, click the Data Asset name.

3. Next to the current schedule, click <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/> **Edit schedule**.

4. Pause the schedule using the **ON**/**OFF** toggle.

5. Click **Save**.