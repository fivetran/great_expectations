---
sidebar_label: 'Transformation'
title: 'Transformation'
---

Data analysts often face the challenge of ensuring that aggregate data remains consistent as it flows through different transformation layers. It’s also critical to standardize records effectively during these transformations to maintain accuracy and comparability across datasets. Additionally, identifying and addressing errant or anomalous data points—whether by removing them or flagging them for further review—is an ongoing concern.

![tbd](/img/integration-medallion.png)

### How can GX Cloud help solve these problems?

GX Cloud can be implemented effectively within a medallion architecture to help surface data quality issues at each transformation stage. For example, consider bronze layer subscription data consisting of 1,000 rows. If 100 of these rows contain shipping dates that are earlier than their transaction dates, this indicates a problem. GX Cloud allows you to create Expectations that flag such inconsistencies automatically, alerting various teams within the organization. The analytics team can be alerted to investigate potential transformation issues. Meanwhile, although data ingestion may have been technically complete and accurate from a raw data standpoint, the sales team may need to correct the records at the source, since some issues may not be discovered until transformation has occurred. Implementing GX Cloud within the medallion framework enables proactive detection and resolution of such issues before they impact downstream analysis or reporting.

![tbd](/img/integration-transformation.png)