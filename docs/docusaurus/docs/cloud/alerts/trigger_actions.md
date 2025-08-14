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
- <PrereqValidationDefinition/>.
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

1. Retrieve the Validation Definition(s) that the Checkpoint will run.

   The Validation Definition(s) can be found either by using the Validation Definition name or by iterating through the list of Validation Definitions available through the Data Context. Both approaches are shown below.

   ```python title="Python" name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - create a Validation Definitions list"
   ```

1. Determine the Actions that the Checkpoint will automate.

   After a Checkpoint receives Validation Results from running a Validation Definition, it executes a list of Actions. The returned Validation Results determine what task is performed for each Action. Actions can include sending alerts when validations fail, or your own custom logic. The Actions list is executed once for each Validation Definition in a Checkpoint. The following is an example of how to create an Action list that will trigger a `SlackNotificationAction`.
    
   Actions can be found in the `great_expectations.checkpoint` module. All action class names end with `*Action`.

   ```python title="Python" name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - define an Action list"
   ```

1. Optional. Choose the Result Format
    
   When a Checkpoint is created you can adjust the verbosity of the Validation Results it generates by setting a Result Format. A Checkpoint's Result Format will be applied to all Validation Results in the Checkpoint every time they are run. By default, a Checkpoint uses a `SUMMARY` result format: it indicates the success or failure of each Expectation in a Validation Definition, along with a partial set of the observed values and metrics that indicate why the Expectation succeeded or failed.
    
   For more information on configuring a Result Format, see Choose a [Result Format](docs/core/trigger_actions_based_on_results/choose_a_result_format/choose_a_result_format.md).

1. The Checkpoint class is available from the great_expectations module. You instantiate a Checkpoint by providing the lists of Validation Definitions and Actions that you previously created, as well as a unique name for the Checkpoint, to the Checkpoint class. The Checkpoint's Result Format can optionally be set, as well:

   ```python title="Python" name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - create a Checkpoint"
   ```

1. Add the Checkpoint to your Data Context.
   Once you create a Checkpoint you should save it to your Data Context for future use:

   ```python title="Python" name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_checkpoint_with_actions.py - save the Checkpoint"
   ```

</TabItem>

</Tabs>
