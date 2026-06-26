---
title: Create a Data Context
hide_table_of_contents: true
---
import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';

import GxData from '../_core_components/_data.jsx'

import QuickDataContext from './_create_a_data_context/_quick_start.md'
import FileDataContext from './_create_a_data_context/_file_data_context.md'
import EphemeralDataContext from './_create_a_data_context/_ephemeral_data_context.md'

A Data Context defines the storage location for metadata, such as your configurations for Data Sources, Expectation Suites, Checkpoints, and Data Docs. It also contains your Validation Results and the metrics associated with them, and it provides access to those objects in Python, along with other helper functions. 

All scripts that utilize GX Core should start with the creation of a Data Context.

The following are the available Data Context types:

- **File Data Context:** A persistent Data Context that stores metadata and configuration information as YAML files within a file system. File Data Contexts allow you to re-use previously configured Expectation Suites, Data Sources, and Checkpoints.

- **Ephemeral Data Context:** A temporary Data Context that stores metadata and configuration information in memory. This Data Context will not persist beyond the current Python session. Ephemeral Data Contexts are a good fit when you don’t need GX configuration to persist between runs—for example, when exploring data without saving results, running validations in CI where the environment is recreated on each run, or working in disposable or read-only compute (such as ephemeral containers or hosted notebooks) where there is no persistent filesystem.

<Tabs queryString="context_type" groupId="context_type" defaultValue='quick' values={[{label: 'Quick Start', value:'quick'}, {label: 'File', value:'file'}, {label: 'Ephemeral', value:'ephemeral'}]}>

<TabItem value="quick" label="Quick Start">
<QuickDataContext/>
</TabItem>

<TabItem value="file" label="File">
<FileDataContext/>
</TabItem>

<TabItem value="ephemeral" label="Ephemeral">
<EphemeralDataContext/>
</TabItem>

</Tabs>