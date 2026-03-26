---
sidebar_label: 'Create a custom action'
title: 'Create a custom action'
description: Run custom logic based on Validation Results.
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

Great Expectations Cloud provides [zero-code alerts](/cloud/alerts/alert_about_failures.md) and [programmable built-in Actions](cloud/alerts/trigger_actions.md) for common workflows, such as sending emails and Microsoft Teams notifications. If these don't meet your needs, you can create a custom Action to integrate with different tools, such as Atlassian Jira, or apply custom business logic based on Validation Results. Example use cases for custom Actions include:

- Opening tickets in an issue tracker when Validation runs fail.
- Triggering different webhooks depending on which Expectations fail.
- Running follow-up ETL jobs to fill in missing values.

A custom Action can do anything that can be done with Python code.

To create a custom Action, you subclass the `ValidationAction` class, overriding the `type` attribute with a unique name and the `run()` method with custom logic.

## Prerequisites
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
1. Create a new custom Action class that inherits the `ValidationAction` class.

   ```python title="Python" name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_custom_action.py - extend class" 
   ```

2. Set a unique name for `type`.

   ```python title="Python" name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_custom_action.py - set type" 
   ```

3.  Optional. Add any additional fields your Action requires at runtime. Actions are built on Pydantic models. Define the field name as a class-level attribute on your Action, and annotate it with the correct type. When you instantiate the Action, pass the field value into the Action `init` method. Your Action will have access to these values within your custom `run` method through `self.<MY_FIELD_NAME>`. The example below shows how to include fields for accessing a Jira API.

      ```python title="Python" name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_custom_action.py - add custom fields"
      ```

4. Override the `run()` method with the logic for the Action. The example below shows how to create a Jira ticket using the additional fields you added in the previous step.

   ```python title="Python" name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_custom_action.py - override run" 
   ```

</TabItem>

<TabItem value="sample_code" label="Sample code">

```python title="Python" name="docs/docusaurus/docs/cloud/alerts/_examples/create_a_custom_action.py - full code example" 
```

</TabItem>

</Tabs>

Now you can use your custom Action through the GX Cloud API like you would any built-in Action. [Trigger your custom Action](cloud/alerts/trigger_actions.md) to start automating responses to Validation Results.

## Limitations

Keep the following limitations in mind when using custom Actions.

- When using a [fully-hosted deployment](cloud/deploy/deployment_patterns.md#fully-hosted-deployment), if you add a custom Action to your GX-managed checkpoint, you will no longer be able to use the **Validation schedule** or the **Validate** button in the UI. 
- When using an [agent-enabled deployment](cloud/deploy/deployment_patterns.md#agent-enabled-deployment),  if you add a custom Action to your GX-managed checkpoint, you will no longer be able to use the **Validation schedule** or the **Validate** button in the UI unless you [customize the GX Agent image](cloud/deploy/deploy_gx_agent.md#deploy-the-gx-agent) with a command for your custom Action.