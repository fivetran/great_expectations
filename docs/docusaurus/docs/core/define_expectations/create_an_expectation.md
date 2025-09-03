---
title: Create an Expectation
description: Create and modify an Expectation in Python.
---
import PrereqPythonInstalled from '../_core_components/prerequisites/_python_installation.md';
import PrereqGxInstalled from '../_core_components/prerequisites/_gx_installation.md';

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

An Expectation is a verifiable assertion about your data. Expectations make implicit assumptions about your data explicit, and they provide a flexible, declarative language for describing expected behavior. They can help you better understand your data and help you improve data quality.

## Prerequisites {#prerequisites-create-expectation}

- <PrereqPythonInstalled/>.
- <PrereqGxInstalled/>.

### Procedure {#procedure-create-expectation}

<Tabs 
   queryString="procedure"
   defaultValue="instructions"
   values={[
      {value: 'instructions', label: 'Instructions'},
      {value: 'sample_code', label: 'Sample code'}
   ]}
>

<TabItem value="instructions" label="Instructions">

1. Choose an Expectation to create.

   GX comes with many built in Expectations to cover your data quality needs.  You can find a catalog of these Expectations in the [Expectation Gallery](https://greatexpectations.io/expectations/).  When browsing the Expectation Gallery you can filter the available Expectations by the data quality issue they address and by the Data Sources they support.  There is also a search bar that will let you filter Expectations by matching text in their name or description.

   In your code, you will find the classes for Expectations in the `expectations` module:

   ```python title="Python"
   from great_expectations import expectations as gxe
   ```

2. Determine the Expectation's required parameters

   To determine the parameters your Expectation uses to evaluate data, reference the Expectation's entry in the [Expectation Gallery](https://greatexpectations.io/expectations/).  Under the **Args** section you will find a list of parameters that are necessary for the Expectation to be evaluated, along with the a description of the value that should be provided.

   Parameters that indicate a column, list of columns, table, Data Source, or severity must be provided when the Expectation is created. All other parameters can be set when the Expectation is created or be assigned a dictionary lookup that will allow them to be set at runtime.

   <a id="severity"></a>

3. Optional. Determine the Expectation's other parameters

   In addition to the parameters that are required for an Expectation to evaluate data, Expectations also support some optional parameters.  In the Expectations Gallery these are found under each Expectation's **Other Parameters** section.



   These parameters are:
   - `meta`: A dictionary of user-supplied metadata to store with an Expectation. This dictionary can be used to add notes about the purpose and intended use of an Expectation.
   - `mostly`: A special argument that allows for _fuzzy_ validation based on a percentage of successfully validated rows. If the percentage is at least the value set in the `mostly` parameter, the Expectation will return a `success` value of `true`.
   - `severity`: Indicates the impact of the Expectation failing. Accepted values are `critical`, `warning`, or `info`. Defaults to `critical` if not explicitly set. You can [trigger Actions](/core/trigger_actions_based_on_results/create_a_checkpoint_with_actions.md) based on severity levels or you can condition your data pipeline with the `get_maximum_severity_failure` helper method in the [`ExpectationSuiteValidationResult` class](/reference/api/core//ExpectationSuiteValidationResult_class.mdx). Note that if an Expectation fails to execute, the failure will be recorded as critical, regardless of the Expectation configuration, to bring your attention to the fact that your data is not being tested as intended.


4. Create the Expectation.
  
   Using the Expectation class you picked and the parameters you determined when referencing the Expectation Gallery, you can create your Expectation.

   <Tabs queryString="expectation_parameters" groupId="expectation_parameters" defaultValue='preset' values={[{label: 'Preset parameters', value:'preset'}, {label: 'Runtime parameters', value:'runtime'}]}>

   <TabItem value="preset" label="Preset parameters">
   
      In this example the `ExpectColumnMaxToBeBetween` Expectation is created and all of its parameters are defined in advance while leaving `strict_min` and `strict_max` as their default values:

      ```python title="Python" name="docs/docusaurus/docs/core/define_expectations/_examples/create_an_expectation.py - preset expectation"
      ```

   </TabItem>
   
   <TabItem value="runtime" label="Runtime parameters">

      Runtime parameters are provided by passing a dictionary to the `expectation_parameters` argument of a Checkpoint's `run()` method.
      
      To indicate which key in the `expectation_parameters` dictionary corresponds to a given parameter in an Expectation you define a lookup as the value of the parameter when the Expectation is created.  This is done by passing in a dictionary with the key `$PARAMETER` when the Expectation is created.  The value associated with the `$PARAMETER` key is the lookup used to find the parameter in the runtime dictionary.

      In this example, `ExpectColumnMaxToBeBetween` is created for both the `passenger_count` and the `fare` fields, and the values for `min_value` and `max_value` in each Expectation will be passed in at runtime.  To differentiate between the parameters for each Expectation a more specific key is set for finding each parameter in the runtime `expectation_parameters` dictionary:
   
      ```python title="Python" name="docs/docusaurus/docs/core/define_expectations/_examples/create_an_expectation.py - dynamic expectations"
      ```

      The runtime `expectation_parameters` dictionary for the above example would look like:
   
      ```python title="Python" name="docs/docusaurus/docs/core/define_expectations/_examples/create_an_expectation.py - example expectation_parameters"
      ``` 

   </TabItem>

   </Tabs>

</TabItem>

<TabItem value="sample_code" label="Sample code">

   ```python title="Python" name="docs/docusaurus/docs/core/define_expectations/_examples/create_an_expectation.py - full code example"
   ```

</TabItem>

</Tabs>

   

