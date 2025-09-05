---
sidebar_label: 'Trigger actions'
title: 'Trigger actions'
description: Create and manage Actions based on the results of Validation runs.
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

import PrereqPythonInstalled from '../../core/_core_components/prerequisites/_python_installation.md';
import PrereqGxInstalled from '../../core/_core_components/prerequisites/_gx_installation.md';
import PrereqPreconfiguredDataContext from '../../core/_core_components/prerequisites/_preconfigured_data_context.md';
import PrereqValidationDefinition from '../../core/_core_components/prerequisites/_validation_definition.md';

Use Actions to notify the appropriate parties of the results of your Validation runs. These Actions can be triggered for either successful or failed Validation runs. Validations are executed using Checkpoints, which each have a list of Actions that will be executed when each run has finished. By default, GX Cloud creates a Checkpoint for each Data Asset that you create. Optionally, you can also use a Checkpoint that you have created manually. This example will demonstrate how to create a `SlackNotificationAction` and append it to the list of Actions on a given Checkpoint.

## Prerequisites
- A [GX Cloud account](https://greatexpectations.io/cloud).
- Your [Cloud credentials](/cloud/connect/connect_python.md#get-your-credentials) saved in your [environment variables](/cloud/connect/connect_python.md#set-your-credentials-as-environment-variables).
- A Checkpoint (either an automatically created GX-managed one or a manually created one).
- [Python version 3.9 to 3.12](https://www.python.org/downloads/).
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
   For the Data Asset of interest, go to the **Validations** tab. If you have more than one **Expectation Suite**, select the **GX-managed** one. Then, click the code snippet icon next to the **Validate** button and click **Generate snippet**.

3. Define the Actions that the Checkpoint will trigger.
    
   The following is an example of how to define a [`SlackNotificationAction`](/reference/api/checkpoint/SlackNotificationAction_class.mdx).

   ```python title="Python" name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - create a SlackNotificationAction"
   ```

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
