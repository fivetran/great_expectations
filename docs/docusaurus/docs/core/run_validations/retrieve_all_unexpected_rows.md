---
title: Retrieve all unexpected rows
description: Retrieve all failing rows from a custom SQL Expectation so you can quarantine them or process them however you need.
---
import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

import PrereqPythonInstalled from '../_core_components/prerequisites/_python_installation.md';
import PrereqGxInstalled from '../_core_components/prerequisites/_gx_installation.md';
import PrereqPreconfiguredDataContext from '../_core_components/prerequisites/_preconfigured_data_context.md';
import PrereqValidationDefinition from '../_core_components/prerequisites/_validation_definition.md';

By default, Validation Results summarize why Expectations failed or succeeded. The default verbosity is designed for exploratory work. If you need more details, you can [increase the verbosity](/core/trigger_actions_based_on_results/choose_a_result_format/choose_a_result_format.md) to return up to 200 failing rows for certain types of Expectations. While this is sufficient for many troubleshooting workflows, there may be times when you want to retrieve all the failing rows with no limit. For example, if you want to quarantine bad records, you'll need all the failing rows.  To support these use cases, GX Core provides the `ValidationDefinition.get_unexpected_rows()` method for use with the `UnexpectedRowsExpectation` class. You can use this method to return all rows that failed your custom SQL Expectations in the batch of data you validated.

## Prerequisites

- <PrereqPythonInstalled/>.
- <PrereqGxInstalled/>.
- <PrereqPreconfiguredDataContext/>. In this guide the variable `context` is assumed to contain your Data Context.
- <PrereqValidationDefinition/> that includes an `UnexpectedRowsExpectation`.

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

1. Retrieve your Validation Definition:

   :::tip You can use a Checkpoint instead.
   While this example shows how to retrieve all unexpected rows after running a Validation Definition, you can use the `ValidationDefinition.get_unexpected_rows()` method after running a [Checkpoint](/docs/core/trigger_actions_based_on_results/run_a_checkpoint.md). 
   :::


   ```python title="Python" name="docs/docusaurus/docs/core/run_validations/_examples/retrieve_all_unexpected_rows.py - retrieve Validation Definition"
   ```

2. Run the Validation Definition to get a result.

   If your [Batch Definition is partitioned](/core/connect_to_data/sql_data/sql_data.md?batch_definition=partitioned#create-a-batch-definition), pass the appropriate `batch_parameters`:

   ```python title="Python" name="docs/docusaurus/docs/core/run_validations/_examples/retrieve_all_unexpected_rows.py - run validation"
   ```

3. Iterate over the results and call `get_unexpected_rows()` for each failing custom SQL Expectation.

   The `get_unexpected_rows()` method only supports `UnexpectedRowsExpectation`.  If your Expectation Suite contains other Expectation types, check `isinstance(evr.expectation, UnexpectedRowsExpectation)` before calling the method.  If your Batch Definition uses partitioning, pass `result.batch_parameters`:

   ```python title="Python" name="docs/docusaurus/docs/core/run_validations/_examples/retrieve_all_unexpected_rows.py - retrieve unexpected rows"
   ```

   The `get_unexpected_rows()` method returns a `list[dict]` with one dictionary per failing row. You can convert this to a DataFrame, write it to a quarantine table, or process it however you need.

   :::note Runtime parameters

   If your Expectation uses the `$PARAMETER` syntax for [runtime parameters](/core/define_expectations/create_an_expectation.md?expectation_parameters=runtime),  pass your dictionary of parameter values with the `expectation_parameters` argument. Otherwise, you will get a `ValueError`.

   :::

</TabItem>

<TabItem value="sample_code" label="Sample code">

```python showLineNumbers title="Python" name="docs/docusaurus/docs/core/run_validations/_examples/retrieve_all_unexpected_rows.py - full code example"
```

</TabItem>

</Tabs>
