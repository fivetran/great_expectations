---
sidebar_label: 'Manage schedules'
title: 'Manage schedules'
description: Create and manage schedules for Validations in GX Cloud.
---

Use a schedule to automate data quality checks with GX-managed Expectations.

## Limitations

Recurring validations cannot be scheduled for the following:
- [API-managed Expectations](/cloud/expectations/expectations_overview.md#gx-managed-vs-api-managed-expectations).
- Data Assets from Azure Blob Storage, BigQuery, Google Cloud Storage, Pandas, or Spark Data Sources.

To automate data quality checks for these, use an [orchestrator](/cloud/connect/connect_airflow.md).


## Enable a schedule

1. In GX Cloud, select the relevant **Workspace** and then click **Data Assets**.

2. In the **Data Assets** list, click the Data Asset name.

3. Next to **No scheduled validation**, click <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/> **Edit schedule**.

4. Turn the Validation schedule **ON**.

5. Select a **Frequency**.

6. Select a **Start time** for the first run of the new schedule.

7. Click **Save**.

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