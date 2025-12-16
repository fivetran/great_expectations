---
sidebar_label: 'Validations'
title: 'Validations'
hide_title: true
description: Validate that your data conforms to your Expectations.
hide_feedback_survey: true
---

import LinkCardGrid from '@site/src/components/LinkCardGrid';
import LinkCard from '@site/src/components/LinkCard';
import OverviewCard from '@site/src/components/OverviewCard';

<OverviewCard title={frontMatter.title}>
  A Validation runs selected Expectations against a Data Asset to validate the data defined by that Data Asset.
</OverviewCard>

<LinkCardGrid>
  <LinkCard topIcon label="Run Validations" description="Validate that your data conforms to your Expectations." to="/cloud/validations/run_validations" icon="/img/checkpoint_icon.svg"/>

  <LinkCard topIcon label="Format results" description="Control the verbosity of your Validation Results." to="/cloud/validations/format_results" icon="/img/example_cases_icon.svg"/>
</LinkCardGrid>