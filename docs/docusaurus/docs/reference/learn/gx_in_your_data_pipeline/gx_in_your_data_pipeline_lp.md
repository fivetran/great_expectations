---
sidebar_label: 'GX in your data pipeline'
title: 'GX in your data pipeline'
hide_title: true
description: Learn where GX can be integrated into a data pipeline to manage and monitor data quality.
hide_feedback_survey: true
pagination_next: null
pagination_prev: null
---

import LinkCardGrid from '@site/src/components/LinkCardGrid';
import LinkCard from '@site/src/components/LinkCard';
import OverviewCard from '@site/src/components/OverviewCard';

<OverviewCard title={frontMatter.title}>
  Learn where GX can be integrated into a data pipeline to manage and monitor data quality.
</OverviewCard>

<LinkCardGrid>

  <LinkCard topIcon label="Ingestion" description="Validate raw data before writing it to your data warehouse so that you can quarantine bad records and identify bugs in your source system." to="/reference/learn/gx_in_your_data_pipeline/ingestion" icon="/img/install_icon.svg"/>

  <LinkCard topIcon label="Transformation" description="Check the results of transformations in your warehouse and condition pipeline steps based on validation success or failure." to="/reference/learn/gx_in_your_data_pipeline/transformation" icon="/img/actions_icon.svg"/>

  <LinkCard topIcon label="Delivery" description="Ensure unexpected patterns reveal business insights rather than data quality issues." to="/reference/learn/gx_in_your_data_pipeline/delivery" icon="/img/example_cases_icon.svg"/>

</LinkCardGrid>