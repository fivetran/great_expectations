---
sidebar_label: 'Manage Validations'
title: 'Manage Validations'
description: Create and manage Validations in GX Cloud.
---

You can manually run a Validation through the GX Cloud UI. This is useful for exploring your data and fine-tuning your Expectations. To run recurring Validations, use a [schedule](/docs/cloud/schedules/manage_schedules.md) or an [orchestrator](/cloud/connect/connect_airflow.md).

:::tip Manual validations are for GX-managed Expectations only
To run a validation for an [API-managed Expectation](/cloud/expectations/manage_expectations.md#gx-managed-vs-api-managed-expectations), create and run a [Validation Definition](/core/run_validations/create_a_validation_definition.md).
:::

<!-- [//]: # (TODO: To learn more about Validations, see Validator.) -->

## Prerequisites

- You have created an [Expectation](/cloud/expectations/manage_expectations.md#add-an-expectation).

## Run a Validation

1. In GX Cloud, click **Data Assets**.

2. Click a Data Asset in the **Data Assets** list.

3. Click **Validate**.

4. When the confirmation message appears, click **See results**, or click the **Validations** tab and select the Validation in the **Batches & run history** pane.

5. Optional. Click **Share** to copy the URL for the Validation Results and share them with other users in your organization.

## Run a Validation on a subset of a Data Asset

If you've [defined a Batch](/cloud/expectations/manage_expectations.md#optional-define-a-batch), you can run a Validation on the latest Batch of data, or you can select a specific year, year and month, or year, month, and day period for the Validation. If a Batch is defined, Batch information appears on the Data Asset **Metrics** page and on the **Validations** page in the **Batches & run history** pane.

To run a Validation for a specific Batch, do the following:

1. In GX Cloud, click **Data Assets**.

2. Click a Data Asset in the **Data Assets** list.

3. Click **Validate**.

4. Select one of the following options:

    - **Latest** - Run the Validation on the latest Batch of data.

    - **Custom** - Select the **year**, **month**, or **day** to run the Validation on a Batch of data for a specific period.

5. Click **Run**.

6. When the confirmation message appears, click **See results**, or click the **Validations** tab and select the Validation in the **Batches & run history** pane.

7. Optional. Click **Share** to copy the URL for the Validation Results and share them with other users in your organization.

## View Validation run history

1. In GX Cloud, click **Data Assets**.

2. Click a Data Asset in the **Data Assets** list.

3. Click the **Validations** tab.

4. On the **Validations** page, select one of the following options:

    - To view only run validation failures, click **Failures Only**.

    - To view the run history for specific Validation, select a Validation in the **Batches & run history** pane.
    
    - To view the run history of all Validations, select **All Runs** to view a graph showing the Validation run history for all columns.

   :::tip Tip

   Items in run history with a calendar icon are run on a GX-managed schedule.

   :::

5. Optional. Hover over a circle in the Validation timeline to view details about a specific Validation run, including the observed values.

    ![Validation timeline detail](/img/view_validation_timeline_detail.png)
