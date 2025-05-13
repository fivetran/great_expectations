---
sidebar_label: 'Integrate GX in a data pipeline'
title: 'Integrate GX in a data pipeline'
---
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import Admonition from '@theme/Admonition';
import GitHubMark from "../../../../static/img/github-mark-small.svg";


This tutorial provides working, hands-on examples of how to use GX to add data validation within a data pipeline. The tutorial is hosted on GitHub.

The tutorial provides a functioning deployment of GX, Airflow, JupyterLab, and Postgres that can be run locally using Docker compose. Educational content is provided as JupyterLab notebooks that can be interactively run and modified to learn and explore how GX integrates with a data pipeline.

The tutorial environment uses Airflow as the orchestrator and Postgres as the Data Source, but the examples can be adapted to any other [supported Data Source and orchestrator](/docs/application_integration_support).

:::tip Other options for Airflow specifically
For a more ergonomic interface and more flexibility, use the [Great Expectations Airflow Provider maintained by Astronomer](https://github.com/astronomer/airflow-provider-great-expectations/blob/main/docs/index.md) to validate data directly from a DAG.
:::

<Admonition type="cta" title="Access this tutorial on GitHub" icon={<GitHubMark/>}>

Click the link below to access the `tutorial-gx-in-the-data-pipeline` repo.

<a class="cta" href="https://github.com/greatexpectationslabs/tutorial-gx-in-the-data-pipeline">tutorial-gx-in-the-data-pipeline</a>

</Admonition>