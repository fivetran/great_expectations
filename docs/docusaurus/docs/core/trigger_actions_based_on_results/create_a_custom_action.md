---
title: Create a custom Action
description: Run custom logic based on validation results to integrate with 3rd-party tools and business workflows.
---
import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

import PrereqPythonInstalled from '../_core_components/prerequisites/_python_installation.md';
import PrereqGxInstalled from '../_core_components/prerequisites/_gx_installation.md';

TODO - intro

<h2>Prerequisites</h2>

- <PrereqPythonInstalled/>.
- <PrereqGxInstalled/>.

### Procedure

<Tabs 
   queryString="procedure"
   defaultValue="instructions"
   values={[
      {value: 'instructions', label: 'Instructions'},
      {value: 'sample_code', label: 'Sample code'}
   ]}
>

<TabItem value="instructions" label="Instructions">

1. Create a new custom Action class that inherits the ValidationAction class.

   ```python title="Python" name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - extend class" 
   ```

2. Choose a unique name for `type`

   ```python title="Python" name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - set type" 
   ```

3. Override the run method with the logic for the Action

   ```python title="Python" name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - override run" 
   ```

</TabItem>

<TabItem value="sample_code" label="Sample code">

```python title="Python" name="docs/docusaurus/docs/core/trigger_actions_based_on_results/_examples/create_a_custom_action.py - full code example" 
```

</TabItem>

</Tabs>
