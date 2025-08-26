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

A Checkpoint executes one or more Validation Definitions and then performs a set of Actions based on the Validation Results each Validation Definition returns. This example will demonstrate how to create a `SlackNotificationAction`.

## Prerequisites
- A [GX Cloud account](https://greatexpectations.io/cloud) with your Cloud access token and Cloud organization token saved in your environment variables
- A Checkpoint.
- <PrereqPythonInstalled/>.
- <PrereqGxInstalled/>.

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
1. Retrieve the Checkpoint to append the Action to.

   ```python title="Python" name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - retrieve the Checkpoint"
   ```

1. Determine the Actions that the Checkpoint will automate.

   After a Checkpoint receives Validation Results from running a Validation Definition, it executes a list of Actions. The returned Validation Results determine what task is performed for each Action. Actions can include sending alerts when validations fail, or your own custom logic. The Actions list is executed once for each Validation Definition in a Checkpoint. The following is an example of how to append a `SlackNotificationAction` to the Action list of your Checkpoint.
    
   Actions can be found in the `great_expectations.checkpoint` module. All Action class names end with `*Action`.

   ```python title="Python" name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - create a SlackNotificationAction"
   ```

   :::tip Setting up an EmailAction is separate from Email alerts controlled through the UI
   Any `EmailActions` that are added to the list of Actions associated with a Checkpoint will activate separately from the Alerts controlled through the UI. For more information, see [Manage email alerts](docs/cloud/alerts/manage_email_alerts.md)

1. Append the Action to the Checkpoint Action list
   Append the newly-created Action to the Checkpoint Action list and save the Checkpoint.

   ```python title="Python" name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - save the Checkpoint"
   ```

</TabItem>

<TabItem value="sample_code" label="Sample code">

```python title="Python" name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - full code example" 
```

</TabItem>

</Tabs>
