---
sidebar_label: 'Data quality use cases'
title: 'Data quality use cases'
hide_title: true
description: Example data quality use cases and implementations with GX Cloud and GX Core.
hide_feedback_survey: true
pagination_next: null
pagination_prev: null
---

import LinkCardGrid from '@site/src/components/LinkCardGrid';
import LinkCard from '@site/src/components/LinkCard';
import OverviewCard from '@site/src/components/OverviewCard';

<OverviewCard title={frontMatter.title}>
  Learn how to use GX to address key data quality scenarios.
</OverviewCard>

A comprehensive data quality strategy relies on a multidimensional approach to achieving and maintaining high-quality data. GX enables you to define and validate data quality checks across a variety of data quality and observability dimensions.

<LinkCardGrid>

  <LinkCard topIcon label="Distribution" description="Validate that data values adhere to expected ranges." to="/reference/learn/data_quality_use_cases/distribution" icon="/img/actions_icon.svg"/>

  <LinkCard topIcon label="Freshness" description="Verify that data is available within expected timeframes." to="/reference/learn/data_quality_use_cases/freshness" icon="/img/actions_icon.svg"/>

  <LinkCard topIcon label="Integrity" description="Validate relationships and dependencies between data." to="/reference/learn/data_quality_use_cases/integrity" icon="/img/actions_icon.svg"/>

  <LinkCard topIcon label="Missingness" description="Identify gaps in data to maintain data completeness." to="/reference/learn/data_quality_use_cases/missingness" icon="/img/actions_icon.svg"/>

  <LinkCard topIcon label="Schema" description="Verify that data structure conforms to established rules." to="/reference/learn/data_quality_use_cases/schema" icon="/img/actions_icon.svg"/>

  <LinkCard topIcon label="Uniqueness" description="Validate that distinct values are present only once." to="/reference/learn/data_quality_use_cases/uniqueness" icon="/img/actions_icon.svg"/>

  <LinkCard topIcon label="Volume" description="Validate that record quantity falls within expected bounds." to="/reference/learn/data_quality_use_cases/volume" icon="/img/actions_icon.svg"/>

</LinkCardGrid>