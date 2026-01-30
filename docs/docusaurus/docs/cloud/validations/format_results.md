---
title: Format results
description: Control the verbosity of your Validation Results.
hide_table_of_contents: true
---
import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

You can control the level of detail GX Cloud returns in your Validation Results to improve the clarity and efficiency of your data quality workflows. You can format your results to receive only the information you need, whether that’s a high-level pass/fail indicator for exploration, specific failing values for troubleshooting, or full failed rows for data cleansing.

Depending on your use case, you can format your Validation Results with either the GX Cloud UI or the GX Cloud API. 
- To format results from [GX-managed Expectations](/docs/cloud/expectations/expectations_overview.md#gx-managed-vs-api-managed-expectations), you can use either the UI or the API.
- To format results from [API-managed Expectations](/docs/cloud/expectations/expectations_overview.md#gx-managed-vs-api-managed-expectations), you must use the API.
- The UI provides a limited set of options for common combinations of more granular settings available through the API.
- The API gives you full control to make custom combinations of settings. 

No matter which interface you use to format your Validation Results, the configuration impacts the results you receive from both the GX Cloud UI and the GX Cloud API. 

<Tabs queryString="interface" groupId="interface" defaultValue='ui'>

<TabItem value="ui" label='UI'>


## Prerequisites
- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/docs/cloud/access/manage_access#roles-and-permissions) or greater.
- A Data Asset with [GX-managed Expectations](/docs/cloud/expectations/expectations_overview#gx-managed-vs-api-managed-expectations).

## Configure Validation Results
1. In the GX Cloud UI, select the relevant **Workspace** and then click **Data Assets**.
2. In the **Data Assets** list, click the Data Asset name.
3. Click **Settings**.
4. Choose what to include in your **Validation Results**. Here’s what is provided by each option:

   |                                             | Status                                     | Observed values (default)                   | Sample unexpected rows                      |
   |---------------------------------------------|--------------------------------------------|---------------------------------------------|---------------------------------------------|
   | Success or failure                          | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> |
   | Query to retrieve full unexpected results * | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> |
   | Success rate *                              | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> |
   | Observed computed values *                  | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> |
   | Number of missing or unexpected rows *      | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> |
   | Up to 25 sample unexpected values *         | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="No">❌ </span> |
   | Up to 25 sample unexpected rows *           | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="Yes">✅</span> |

   \* Note that this kind of detail is not returned by some types of Expectations, even if this kind of detail is generally supported in your selected configuration. For example, a Column Aggregate Expectation like [ExpectColumnMeanToBeBetween](https://greatexpectations.io/expectations/expect_column_mean_to_be_between/) will never return a sample of failed rows because it assesses an aggregate of values across rows. 

5. Click **OK** to save your selection. The new selection applies going forward. Historical Validation Results retain their original contents. 

For more information about how the opinionated options in the UI map to the more granular options in the API, see the [UI options reference table](/docs/cloud/validations/format_results?interface=api&results=ui_options#reference-tables).
</TabItem>
   
<TabItem value="api" label='API'>

## Prerequisites

- A [GX Cloud account](https://greatexpectations.io/cloud) with [Workspace Editor permissions](/docs/cloud/access/manage_access.md#roles-and-permissions) or greater.
- Your [Cloud credentials](/docs/cloud/connect/connect_python.md#get-your-credentials) saved in your [environment variables](/docs/cloud/connect/connect_python.md#set-your-credentials-as-environment-variables).
- A Data Asset with a [Checkpoint or Validation Definition](/cloud/validations/run_validations.md). You can use an automatically created GX-managed resource or a manually created resource.
- [Python version 3.10 to 3.13](https://www.python.org/downloads/).
- [An installation of the Great Expectations Python library](https://pypi.org/project/great-expectations/).

## Configure and apply a Result Format

Follow the steps below to select a base format, optionally configure additional settings available to your selection, and then apply the Result Format configuration to a Checkpoint or Validation Definition.

1. Create a dictionary and set the base format of your Validation Results as the value of the key `"result_format"`.  In order from least to most detail, the valid values for the `"result_format"` key are: 

   - `"BOOLEAN_ONLY"`
   - `"BASIC"`
   - `"SUMMARY"`
   - `"COMPLETE"`

   The default for Validation Results generated by GX-managed Checkpoints is `"BASIC"` with some [non-default additional settings](/docs/cloud/validations/format_results?interface=api&results=ui_options#reference-tables). The default for Validation Results generated by Validation Definitions and API-managed Checkpoints is `"SUMMARY"`.

   Select a value below to see example code for that Result Format and what information is returned at that level:

   <Tabs queryString="result_format_string" groupId="result_format_string" defaultValue='basic'>

   <TabItem value="boolean" label='"BOOLEAN_ONLY"'>
   When the `result_format` is `"BOOLEAN_ONLY"`, Validation Results by default do not include additional information in a `result` dictionary.  The successful evaluation of the Expectation is exclusively returned via the `True` or `False` value of the `success` key in the returned Validation Result.

   To create a `"BOOLEAN_ONLY"` Result Format configuration, use the following code:

   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/result_format.py - boolean_only Result Format"
   ```
   </TabItem>
   
   <TabItem value="basic" label='"BASIC"'>
   When the `result_format` is set to `"BASIC"`, the Validation Results of each Expectation include a `result` dictionary with information providing a basic explanation for why it failed or succeeded. The format is intended for quick feedback and it works well in Jupyter Notebooks.
   
   You can check the [result field reference table](/docs/cloud/validations/format_results?results=format#reference-tables) to see what information is provided in the `result` dictionary.
   
   To create a `"BASIC"` Result Format configuration, use the following code:
   
   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/result_format.py - basic Result Format"
   ```
   </TabItem>

   <TabItem value="summary" label='"SUMMARY"'>
   When the `result_format` key is set to `"SUMMARY"`, the Validation Results of each Expectation include a `result` dictionary with information that summarizes values to show why it failed or succeeded.  This format is intended for more detailed exploratory work and includes additional information beyond what is included by `BASIC`.
   
   You can check the [result field reference table](/docs/cloud/validations/format_results?results=format#reference-tables) to see what information is provided in the `result` dictionary.

   To create a `"SUMMARY"` Result Format configuration, use the following code:
   
   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/result_format.py - summary Result Format"
   ```
   </TabItem>

   <TabItem value="complete" label='"COMPLETE"'>
   When the `result_format` key is set to `"COMPLETE"`, the Validation Results of each Expectation include a `result` dictionary with all available information to explain why it failed or succeeded.  This format is intended for debugging pipelines or developing detailed regression tests and includes additional information beyond what is provided by `"SUMMARY"`.
   
   You can check the [result field reference table](/docs/cloud/validations/format_results?results=format#reference-tables) to see what information is provided in the `result` dictionary.
   
   To create a `"COMPLETE"` Result Format configuration, use the following code:
   
   ```python title="Python" name="docs/docusaurus/docs/cloud/validations/code_samples/result_format.py - complete Result Format"
   ```
   </TabItem>

   </Tabs>

2. Optional. Specify configurations for additional settings available to the base `result_format`.

   Once you have defined the base configuration in your `result_format` key, you can further tailor the format of your Validation Results by defining additional key/value pairs in your Result Format dictionary.

   Reference the table below for valid keys and how they influence the format of generated Validation Results:

   <Tabs queryString="result_format_string" groupId="result_format_string" defaultValue='basic'>

   <TabItem value="boolean" label='"BOOLEAN_ONLY"'>
   | Dictionary key                    | Purpose                                                                                                                                                                                                                    |
   |-----------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
   | `"return_unexpected_index_query"` | Return a query (or a set of indices) that allows you to retrieve the full set of unexpected results as well as the values of any identifying columns specified in `"unexpected_index_column_names"`. (Default is `False`). |
   | `"unexpected_index_column_names"` | Takes a list to define the column(s) that will be used to identify unexpected results returned. For example, primary key (PK) column(s) or other columns with unique identifiers.                                          |
   </TabItem>
   
   <TabItem value="basic" label='"BASIC"'>
    | Dictionary key                    | Purpose                                                                                                                                                                                                                                                                                                                                                                                                                  |
    | --------------------------------- |--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
    | `"include_unexpected_rows"`       | When `True`, GX Cloud returns up to 200 entire rows that violate the Expectation (default is `False`). Applies to Column Map, Column Pair Map, Multicolumn Map, and Unexpected Rows Expectations only. Note that [`ExpectColumnValuesToBeOfType`](https://greatexpectations.io/expectations/expect_column_values_to_be_of_type/) and [`ExpectColumnValuesToBeInTypeList`](https://greatexpectations.io/expectations/expect_column_values_to_be_in_type_list/) will return unexpected rows for only Pandas Data Sources. |
    | `"partial_unexpected_count"`      | Sets the number of results to include in `"partial_unexpected_list"` and `"unexpected_rows"` (default is 20). Set the value to zero to suppress the `"partial_unexpected_list"` output.                                                                                                                                                                                                                                                                           |
    | `"return_unexpected_index_query"` | Return a query (or a set of indices) that allows you to retrieve the full set of unexpected results as well as the values of any identifying columns specified in `"unexpected_index_column_names"`. (Default is `False`).                                                                                                                                                                                               |
    | `"unexpected_index_column_names"` | Takes a list to define the column(s) that will be used to identify unexpected results returned. For example, primary key (PK) column(s) or other columns with unique identifiers.                                                                                                                                                                                                                                        |
   </TabItem>

   <TabItem value="summary" label='"SUMMARY"'>
    | Dictionary key                    | Purpose                                                                                                                                                                                                                                                                                                                                                                                                                  |
    | --------------------------------- |--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
    | `"include_unexpected_rows"`       | When `True`, GX Cloud returns up to 200 entire rows that violate the Expectation (default is `False`). Applies to Column Map, Column Pair Map, Multicolumn Map, and Unexpected Rows Expectations only. Note that [`ExpectColumnValuesToBeOfType`](https://greatexpectations.io/expectations/expect_column_values_to_be_of_type/) and [`ExpectColumnValuesToBeInTypeList`](https://greatexpectations.io/expectations/expect_column_values_to_be_in_type_list/) will return unexpected rows for only Pandas Data Sources. |
    | `"partial_unexpected_count"`      | Sets the number of results to include in `"partial_unexpected_counts"`, `"partial_unexpected_list"`, `"partial_unexpected_index_list"`, and `"unexpected_rows"` (default is 20). Set the value to zero to suppress the `partial_unexpected_*` output.                                                                                                                                                                                                     |
    | `"return_unexpected_index_query"` | Return a query (or a set of indices) that allows you to retrieve the full set of unexpected results as well as the values of any identifying columns specified in `"unexpected_index_column_names"`. (Default is `False`).                                                                                                                                                                                               |
    | `"unexpected_index_column_names"` | Takes a list to define the column(s) that will be used to identify unexpected results returned. For example, primary key (PK) column(s) or other columns with unique identifiers.                                                                                                                                                                                                                                        |
   </TabItem>

   <TabItem value="complete" label='"COMPLETE"'>
    | Dictionary key                    | Purpose                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
    | --------------------------------- |----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
    | `"exclude_unexpected_values"`     | When running validations, a set of unexpected results' indices and values is returned.  Setting this value to `True` suppresses values from the output to only have indices (default is `False`).                                                                                                                                                                                                                                                              |
    | `"include_unexpected_rows"`       | When `True`, GX Cloud returns up to 200 entire rows that violate the Expectation (default is `False`). Applies to Column Map, Column Pair Map, Multicolumn Map, and Unexpected Rows Expectations only. Note that [`ExpectColumnValuesToBeOfType`](https://greatexpectations.io/expectations/expect_column_values_to_be_of_type/) and [`ExpectColumnValuesToBeInTypeList`](https://greatexpectations.io/expectations/expect_column_values_to_be_in_type_list/) will return unexpected rows for only Pandas Data Sources.                                       |
    | `"partial_unexpected_count"`      | Sets the number of results to include in `"partial_unexpected_counts"`, `"partial_unexpected_list"`, `"partial_unexpected_index_list"`, and `"unexpected_rows"` (default is 20). Set the value to zero to suppress the `partial_unexpected_*` output.                                                                                                                                                                                                                                           |
    | `"return_unexpected_index_query"` | Return a query (or a set of indices) that allows you to retrieve the full set of unexpected results as well as the values of any identifying columns specified in `"unexpected_index_column_names"`. Setting `"return_unexpected_index_query"` to `False` suppresses the output (default is `True`). |
    | `"unexpected_index_column_names"` | Takes a list to define the column(s) that will be used to identify unexpected results returned. For example, primary key (PK) column(s) or other columns with unique identifiers.                                                                                                                                                                                                                                                                              |
   </TabItem>

   </Tabs>

3. Apply the Result Format to a Checkpoint or Validation Definition.

   You can define a persistent Result Format configuration on a Checkpoint. The Result Format will be applied every time the Checkpoint is run.  For more information on retrieving or creating a Checkpoint, see [Run a Validation](/cloud/validations/run_validations.md).

   ```Python title="Saved Result Format" name="docs/docusaurus/docs/cloud/validations/code_samples/result_format.py - apply to Checkpoint"
   ```

   Alternatively, you can pass a `result_format` configuration at runtime to the `.run(...)` method of a Validation Definition.  This `result_format` configuration does not persist with the Validation Definition; it will apply to only the current execution of the `.run(...)` method. For more information on creating a Validation Definition, see [Run a Validation](/cloud/validations/run_validations.md).

   ```Python title="Runtime Result Format" name="docs/docusaurus/docs/cloud/validations/code_samples/result_format.py - apply to Validation Definition"
   ```

## Reference tables

<Tabs queryString="results" groupId="results" defaultValue='fields'>

   <TabItem value="fields" label="Information in result fields">
    The following table lists the fields that can be found in the `result` dictionary of a Validation Result, and what information is provided by that field.

    | Field within `result`         | Value                                                                                                                                                                                                  |
    |-------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
    | element_count                 | The total number of values in the column.                                                                                                                                                              |
    | missing_count                 | The number of missing values in the column.                                                                                                                                                            |
    | missing_percent               | The total percent of rows missing values for the column.                                                                                                                                               |
    | unexpected_count              | The total count of unexpected values in a column.                                                                                                                                                   |
    | unexpected_percent            | The overall percent of unexpected values in a column.                                                                                                                                                  |
    | unexpected_percent_nonmissing | The percent of unexpected values in a column, excluding rows that have no value for that column.                                                                                                       |
    | observed_value                | The aggregate statistic computed for the column. This only applies to Expectations that pertain to the aggregate value of a column, rather than the individual values in each row for the column.      |
    | partial_unexpected_list       | A partial list of values that violate the Expectation. (Up to 20 values by default.)                                                                                                                   |
    | partial_unexpected_index_list | A partial list of the unexpected values in the column, as defined by the columns in `unexpected_index_column_names`. (Up to 20 indices by default.)                                                    |
    | partial_unexpected_counts     | A partial list of values and counts, showing the number of times each of the unexpected values occurs. (Up to 20 unexpected value/count pairs by default.)                                              |
    | unexpected_index_list         | A list of the indices of the unexpected values in the column, as defined by the columns in `unexpected_index_column_names`. This only applies to Expectations that have a yes/no answer for each row.  |
    | unexpected_index_query        | A query that can be used to retrieve all unexpected values (SQL and Spark), or the full list of unexpected indices (Pandas). This only applies to Expectations that have a yes/no answer for each row. |
    | unexpected_list               | A list of up to 200 values that violate the Expectation.                                                                                                                                               |
    | unexpected_rows               | Up to 200 complete rows that violate the Expectation. The format depends on the Data Source. For example, a SQL Data Source will return a list of dictionaries while a Spark Data Source will return a DataFrame. Applies to Column Map, Column Pair Map, Multicolumn Map, and Unexpected Rows Expectations only. Note that [`ExpectColumnValuesToBeOfType`](https://greatexpectations.io/expectations/expect_column_values_to_be_of_type/) and [`ExpectColumnValuesToBeInTypeList`](https://greatexpectations.io/expectations/expect_column_values_to_be_in_type_list/) will return unexpected rows for only Pandas Data Sources. |
   </TabItem>

   <TabItem value="format" label="Result fields by base format">
    The following table lists the fields that can be found in the `result` dictionary of a Validation Result and the `result_format` levels that return that field. An * indicates the field is not returned by default but can be enabled through an additional setting. Meanwhile, ** indicates that the field is returned by default but can be disabled.

    | Fields within `result`             |BOOLEAN_ONLY    |BASIC           |SUMMARY         |COMPLETE        |
    -------------------------------------|----------------|----------------|----------------|-----------------
    | element_count                      |no              |yes             |yes             |yes             |
    | missing_count                      |no              |yes             |yes             |yes             |
    | missing_percent                    |no              |yes             |yes             |yes             |
    | unexpected_count                   |no              |yes             |yes             |yes             |
    | unexpected_percent                 |no              |yes             |yes             |yes             |
    | unexpected_percent_nonmissing      |no              |yes             |yes             |yes             |
    | observed_value                     |no              |yes             |yes             |yes             |
    | partial_unexpected_list            |no              |yes **          |yes **          |yes **          |
    | partial_unexpected_index_list      |no              |no              |yes **          |yes **          |
    | partial_unexpected_counts          |no              |no              |yes **          |yes **          |
    | unexpected_index_list              |no              |no              |no              |yes             |
    | unexpected_index_query             |yes *           |yes *           |yes *           |yes             |
    | unexpected_list                    |no              |no              |no              |yes             |
    | unexpected_rows                    |no              |yes *           |yes *           |yes *           |
   </TabItem>

   <TabItem value="result_format_keys" label="Result Format keys">
    The following table lists the valid keys for a Result Format dictionary and what their purpose is.  Not all keys are used by every `result_format` level.

    | Dictionary key                    | Purpose                                                                                                                                                                                                                                                                                                                                                                                                                               |
    | --------------------------------- |---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
    |`"result_format"`                  | Sets the fields to return in Validation Results.   Valid values are `"BASIC"`, `"BOOLEAN_ONLY"`, `"COMPLETE"`, and `"SUMMARY"` (default for GX-managed Checkpoints is `"BASIC"` with some [non-default additional settings](/docs/cloud/validations/format_results?interface=api&results=ui_options#reference-tables); default for Validation Definitions and API-managed Checkpoints is `"SUMMARY"`).                                                                                                                                                                   |
    | `"unexpected_index_column_names"` | Takes a list to define the column(s) that will be used to identify unexpected results returned. For example, primary key (PK) column(s) or other columns with unique identifiers.                                                                                                                                                                                      |
    |`"return_unexpected_index_query"`  | Return a query (or a set of indices) that allows you to retrieve the full set of unexpected results as well as the values of any identifying columns specified in `"unexpected_index_column_names"`. Setting `"return_unexpected_index_query"` to `False` suppresses the output (default is `True` for `"COMPLETE"` and `False` for `"BASIC"`, `"BOOLEAN_ONLY"`, and `"SUMMARY"`). |
    | `"partial_unexpected_count"`      | Sets the number of results to include in `"partial_unexpected_counts"`, `"partial_unexpected_list"`, `"partial_unexpected_index_list"`, and `"unexpected_rows"` if applicable (default is 20). Set the value to zero to suppress the `partial_unexpected_*` output.                                                                                                                                                                                                 |
    | `"exclude_unexpected_values"`     | When running validations, a set of unexpected results' indices and values is returned.  Setting this value to `True` suppresses values from the output to only have indices (default is `False`).                                                                                                                                                                                                                                     |
    | `"include_unexpected_rows"`       | When `True`, GX Cloud returns up to 200 entire rows that violate the Expectation (default is `False`). Applies to Column Map, Column Pair Map, Multicolumn Map, and Unexpected Rows Expectations only. Note that [`ExpectColumnValuesToBeOfType`](https://greatexpectations.io/expectations/expect_column_values_to_be_of_type/) and [`ExpectColumnValuesToBeInTypeList`](https://greatexpectations.io/expectations/expect_column_values_to_be_in_type_list/) will return unexpected rows for only Pandas Data Sources.              |
   </TabItem>

   <TabItem value="ui_options" label="UI options">
   In case you want to replicate one of the opinionated UI options for configuring Validation Results, here are the equivalent API configurations for each UI option.

   | UI option              | API configuration                                                                                                |
   |------------------------|------------------------------------------------------------------------------------------------------------------|
   | Status                 | `"result_format": "BOOLEAN_ONLY",`<br />`"return_unexpected_index_query": True,`                                 |
   | Observed values        | `"result_format": "BASIC",`<br />`"return_unexpected_index_query": True,`<br />`"partial_unexpected_count": 25,` |
   | Sample unexpected rows | `"result_format": "COMPLETE",`<br />`"partial_unexpected_count": 25,`<br />`"include_unexpected_rows": True,`    |
   </TabItem>


</Tabs>

</TabItem>

</Tabs>