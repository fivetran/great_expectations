---
title: Retrieve all unexpected rows
---
import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

import PrereqPythonInstalled from '../_core_components/prerequisites/_python_installation.md';
import PrereqGxInstalled from '../_core_components/prerequisites/_gx_installation.md';
import PrereqPreconfiguredDataContext from '../_core_components/prerequisites/_preconfigured_data_context.md';
import PrereqValidationDefinition from '../_core_components/prerequisites/_validation_definition.md';

By default, Validation Results include up to 200 unexpected rows in the `unexpected_rows` field.  If your data contains more than 200 failing rows, the `ValidationDefinition.get_unexpected_rows()` method lets you retrieve **all** of them.  It re-executes the Expectation's query against the same batch -- including any partitioning filters -- without the 200-row cap.

This method currently supports `UnexpectedRowsExpectation` on SQL and Spark Data Sources.

## Prerequisites

- <PrereqPythonInstalled/>.
- <PrereqGxInstalled/>.
- <PrereqPreconfiguredDataContext/>. In this guide the variable `context` is assumed to contain your Data Context.
- <PrereqValidationDefinition/> that includes an `UnexpectedRowsExpectation` and is backed by a SQL or Spark Data Source.

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

1. Retrieve your Validation Definition.

   ```python title="Python" name="docs/docusaurus/docs/core/run_validations/_examples/retrieve_all_unexpected_rows.py - retrieve Validation Definition"
   ```

2. Run the Validation Definition to get a result.

   If your Batch Definition uses partitioning, pass the appropriate `batch_parameters`:

   ```python title="Python" name="docs/docusaurus/docs/core/run_validations/_examples/retrieve_all_unexpected_rows.py - run validation"
   ```

3. Iterate over the results and call `get_unexpected_rows()` for each failing Expectation.

   Use `evr.expectation` to get the typed Expectation object from an `ExpectationValidationResult`, and pass `result.batch_parameters` to ensure the same batch is queried:

   ```python title="Python" name="docs/docusaurus/docs/core/run_validations/_examples/retrieve_all_unexpected_rows.py - retrieve unexpected rows"
   ```

   `get_unexpected_rows()` returns a `list[dict]` with one dictionary per failing row.  You can convert this to a DataFrame, write it to a quarantine table, or process it however you need.

</TabItem>

<TabItem value="sample_code" label="Sample code">

```python showLineNumbers title="Python" name="docs/docusaurus/docs/core/run_validations/_examples/retrieve_all_unexpected_rows.py - full code example"
```

</TabItem>

</Tabs>
