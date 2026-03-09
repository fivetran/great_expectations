---
sidebar_label: 'Trigger actions'
title: 'Trigger actions'
description: Create and manage Actions based on the results of Validation runs.
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

Use Actions to notify the appropriate parties of the results of your Validation runs. Actions can be triggered on failure severity, Validation success, or all Validations. Validations are executed using Checkpoints, which each have a list of Actions that will be executed when each run has finished. By default, GX Cloud creates a Checkpoint for each Data Asset that you create. Optionally, you can also use a Checkpoint that you have created manually. This example will demonstrate how to create a `SlackNotificationAction` and append it to the list of Actions on a given Checkpoint.

:::tip Consider zero-code alerts instead
If you want to send notifications to email addresses, Slack, Microsoft Teams, PagerDuty, or ServiceNow, consider using [zero-code alerts](/cloud/alerts/alert_about_failures.md) instead of coding Actions. While Actions can be scaled programmatically, alerts give you more control over which severities of failures trigger which notifications. Alerts also give you the ability to @mention collaborators in Slack. 
:::

## Prerequisites
- A [GX Cloud account](https://greatexpectations.io/cloud).
- Your [Cloud credentials](/cloud/connect/connect_python.md#get-your-credentials) saved in your [environment variables](/cloud/connect/connect_python.md#set-your-credentials-as-environment-variables).
- A Checkpoint (either an automatically created GX-managed Checkpoint or a [manually created Checkpoint](/docs/cloud/validations/run_validations#api-managed-expectations-entire-asset)).
- [Python version 3.10 to 3.13](https://www.python.org/downloads/).
- [An installation of the Great Expectations Python library](https://pypi.org/project/great-expectations/).

## Procedure

<Tabs 
   queryString="procedure"
   defaultValue="instructions"
   values={[
      {value: 'instructions', label: 'Instructions'},
      {value: 'sample_code', label: 'Sample code'}
   ]}
>

<TabItem value="instructions" label="Instructions">
1. Import the relevant modules and instantiate your Context.
   ```python title="Python" name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - instantiate the Context"
   ```

2. Retrieve the Checkpoint to append the Action to.

   ```python title="Python" name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - retrieve the Checkpoint"
   ```

   :::tip The GX-managed Checkpoint name can be found through the UI
   For the Data Asset of interest, go to the **Expectations** tab. Then, click the code snippet icon next to the **Validate** button and click **Generate snippet**.
   :::

3. Define the Actions that the Checkpoint will trigger.
    
   The following is an example of how to define a [`SlackNotificationAction`](/reference/api/checkpoint/SlackNotificationAction_class.mdx).

   ```python title="Python" name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - create a SlackNotificationAction"
   ```

   In this example, `notify_on="failure"` means that the Slack notification will be triggered when the Validation Results include any [severity](/cloud/expectations/expectations_overview.md#failure-severity) of Expectation failure. Accepted values for `notify_on` are as follows:

   - `all`: Always trigger the Action when Validation Results are received.
   - `success`: Trigger the Action only when all Expectations succeed.
   - `failure`: Trigger the Action when any Expectation fails, regardless of failure severity.
   - `critical`: Trigger the Action when there's a critical Expectation failure. This may be an Expectation configured with critical severity or an Expectation of any severity that failed to execute. 
   - `warning`: Trigger the Action when there's a warning-level Expectation failure and no critical failures.
   - `info`: Trigger the Action when there's an info-level Expectation failure and no warning or critical failures. 


   :::note The highest severity takes precedence
   If a Validation Result includes a mix of warning and info failures, only Actions configured to notify on `warning`, `failure`, or `all` will be triggered. Any Actions configured to run on `info` will not be triggered.
   :::

4. Append the newly-created Action to the Checkpoint Action list and save the Checkpoint.

   ```python title="Python" name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - save the Checkpoint"
   ```

5. Optional. Run a Validation to ensure the newly-created Action is triggered as expected.
</TabItem>

<TabItem value="sample_code" label="Sample code">

```python title="Python" name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - full code example" 
```

</TabItem>

</Tabs>
