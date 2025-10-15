---
sidebar_label: 'Ingestion'
title: 'Ingestion'
description: Learn how GX can help improve your data quality at the ingestion phase of your data pipeline.
---

Ingesting raw data into a data pipeline can be a complex and often error-prone process, with various challenges that can impact the efficiency and reliability of processes downstream that rely on it. Below are some key challenges and potential pitfalls that can happen during this phase of the data pipeline:

- **Incomplete data**: Raw data can often contain gaps or missing values, resulting in incomplete records. This can occur due to various reasons like system failures, human input errors, interruptions in data collection processes, and so on. Identifying when data is missing or incomplete is critical at this stage of the data pipeline.

- **Duplicate data**: Redundant data records can be ingested, especially in streaming pipelines or systems with unreliable deduplication logic, leading to inflated analytics and inaccurate statistics, ultimately resulting in wrong conclusions and misguided decisions. 

- **Schema drift**: The structure of the incoming data can sometimes change over time. When the schema drift is drastic, it can lead to downstream issues like failed jobs or corrupted data. However, more subtle changes can go unnoticed, leading to poor decision-making or inaccurate models.


### How can GX Cloud help solve these problems?
GX Cloud gives you the freedom to decide when and how to validate your data. If the raw data has already been ingested to a staging area within your data warehouse, GX Cloud can connect directly to it and run Validations to ensure the integrity of the staged raw data. Alternatively, you can create in-memory Data Assets, allowing you to run Validations on your data before it lands in your data warehouse, thereby allowing you to take steps like deduplication and value backfilling.

![Example of how GX Cloud can detect issues as raw data is imported into a data warehouse. Expectations like 'Expect column values to be unique' and 'Expect column values to not be null' can be used to clean data.](/img/integration-ingestion.png)

GX Cloud offers the ability to either schedule validation runs directly through the UI on a time interval of your choice, or by using the API to trigger validation runs immediately after ingestion is complete. With both methods, you will have timely feedback on the health of your data and be able to take action to correct errors before they propagate downstream.
