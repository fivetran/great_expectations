---
title: Create a custom Action
description: Run custom logic based on Validation Results to integrate with 3rd-party tools and business workflows.
---
import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

import PrereqPythonInstalled from '../_core_components/prerequisites/_python_installation.md';
import PrereqGxInstalled from '../_core_components/prerequisites/_gx_installation.md';

Great Expectations provides [Actions for common workflows](/application_integration_support.md#integrations) such as sending emails and updating Data Docs. If these don't meet your needs, you can create a custom Action to integrate with different tools or apply custom business logic based on Validation Results. Example use cases for custom Actions include:
- Opening tickets in an issue tracker when Validation runs fail.
- Triggering different webhooks depending on which Expectations fail.
- Running follow-up ETL jobs to fill in missing values.  

A custom Action can do anything that can be done with Python code.

To create a custom Action, you subclass the `ValidationAction` class, overriding the `type` attribute with a unique name and the `run()` method with custom logic.


## Prerequisites

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

1. Create a new custom Action class that inherits the `ValidationAction` class.

   ```python title="Python" name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - extend class" 
   ```

2. Set a unique name for `type`.

   ```python title="Python" name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - set type" 
   ```

3. Override the `run()` method with the logic for the Action.

   ```python title="Python" name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - override run" 
   ```

</TabItem>

<TabItem value="sample_code" label="Sample code">

```python title="Python" name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - full code example" 
```

</TabItem>

</Tabs>

Now you can use your custom Action like you would any built-in Action. [Create a Checkpoint with Actions](/core/trigger_actions_based_on_results/create_a_checkpoint_with_actions.md) to start automating responses to Validation Results.