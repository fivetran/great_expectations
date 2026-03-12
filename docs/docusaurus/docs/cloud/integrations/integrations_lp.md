---
sidebar_label: 'Integrations'
title: 'Integrations'
hide_title: true
description: Integrate GX Cloud with third-party tools to get the most out of your data quality efforts.
hide_feedback_survey: true
---

import LinkCardGrid from '@site/src/components/LinkCardGrid';
import LinkCard from '@site/src/components/LinkCard';
import OverviewCard from '@site/src/components/OverviewCard';

<OverviewCard title={frontMatter.title}>
  Integrate GX Cloud with third-party tools to get the most out of your data quality efforts.
</OverviewCard>

<LinkCardGrid>
  <LinkCard topIcon label="Atlan" description="Surface data quality insights in Atlan’s metadata layer." to="/cloud/integrations/integrate_atlan" icon="/img/atlan_logo.png"/>

  <LinkCard topIcon label="Airflow" description="Validate data directly from a DAG." to="/cloud/integrations/integrate_airflow" icon="/img/airflow_icon.png"/>

  <LinkCard topIcon label="Slack" description="Enable configuring alerts that @mention stakeholders or yourself in Slack." to="/cloud/integrations/integrate_slack" icon="/img/slack_logo.svg"/>
</LinkCardGrid>