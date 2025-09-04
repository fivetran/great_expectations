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
  <LinkCard topIcon label="Manage email alerts" description="Configure and manage email alerts for your Data Assets." to="/cloud/alerts/manage_email_alerts" icon="/img/email_action_icon.svg" />
  <LinkCard topIcon label="Trigger actions" description="Create and manage Actions based on the results of Validation runs." to="/cloud/alerts/trigger_actions" icon="/img/actions_icon.svg" />
</LinkCardGrid>
