---
sidebar_label: 'Transformation'
title: 'Transformation'
description: Learn how GX can be implemented to ensure aggregate data is consistent through transformation layers.
---

Data analysts often face the challenge of ensuring that aggregate data remains consistent as it flows through different transformation layers. It’s also critical to standardize records effectively during these transformations to maintain accuracy and comparability across datasets. Additionally, identifying and addressing errant or anomalous data points—whether by removing them or flagging them for further review—is an ongoing concern.

![Example data warehouse with bronze layer to cleanse tables, silver layer to combine tables, and gold layer to calculate aggregates.](/img/integration-medallion.png)
This sample data pipeline shows the progression of data through the medallion architecture.

### How can GX Cloud help solve these problems?

GX Cloud can be implemented within a medallion architecture to help surface data quality issues at each transformation stage. For example, consider a bronze layer for cleansing data. GX Cloud allows you to create Expectations that flag errors and inconsistencies, such as typos and differences in data types. Next, consider a silver layer for combining data. Expectations can be set up to detect logical errors between columns in a combined silver table that couldn't be detected across disparate bronze tables, like if the shipping date occurs before the payment date. In both cases, the analytics team can be alerted to investigate potential transformation issues. Meanwhile, although data ingestion may have been technically complete and accurate from a raw data standpoint, the sales team may need to correct the records at the source, since some issues may not be discovered until transformation has occurred. Implementing GX Cloud within the medallion framework enables proactive detection and resolution of such issues before they impact downstream analysis or reporting.

![Expectations on the bronze layer such as "Expect column values to be between" and "Expect column values to be of type" help clean data before it gets combined in the silver layer. Custom SQL Expectations on the silver layer test that data adheres to business requirements.](/img/integration-transformation.png)
GX Cloud can be implemented to ensure that a variety of different data transformations have been completed correctly. Above are some examples of data transformations and the corresponding Expectations that can be used to validate them.