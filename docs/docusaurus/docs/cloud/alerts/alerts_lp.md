---
sidebar_label: 'Respond to results'
title: 'Respond to results'
hide_title: true
description: Respond to the results of your Validation runs.
hide_feedback_survey: true
---

import LinkCardGrid from '@site/src/components/LinkCardGrid';
import LinkCard from '@site/src/components/LinkCard';
import OverviewCard from '@site/src/components/OverviewCard';

<OverviewCard title={frontMatter.title}>
  Set up and manage the responses to your Validation runs.
</OverviewCard>

<LinkCardGrid>
  <LinkCard topIcon label="Alert about failures" description="Configure and manage alerts for your Data Assets with a no-code workflow." to="/cloud/alerts/alert_about_failures" icon="/img/alarm_icon.png" />
  <LinkCard topIcon label="Trigger actions" description="Programmatically create and manage Actions based on the results of Validation runs." to="/cloud/alerts/trigger_actions" icon="/img/actions_icon.svg" />
  <LinkCard topIcon label="Create a custom action" description="Apply custom business logic based on Validation Results." to="/cloud/alerts/custom_actions" icon="/img/add_feature_icon.svg" />
</LinkCardGrid>
