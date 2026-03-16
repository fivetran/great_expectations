---
title: "Run Validations"
description: Validate your Expectations against your data and explore the results.
hide_feedback_survey: true
hide_title: true
---

import LinkCardGrid from '@site/src/components/LinkCardGrid';
import LinkCard from '@site/src/components/LinkCard';
import OverviewCard from '@site/src/components/OverviewCard';

<OverviewCard title={frontMatter.title}>
  Validate your Expectations against your data and explore the results.
</OverviewCard>


<LinkCardGrid>

  <LinkCard 
    topIcon 
    label="Create a Validation Definition"
    description="Use a Validation Definition to associate a Batch Definition with an Expectation Suite."
    to="/core/run_validations/create_a_validation_definition" 
    icon="/img/expectation_icon.svg" 
  />

  <LinkCard 
    topIcon 
    label="Run a Validation Definition"
    description="Run a Validation Definition using predefined defaults or parameters defined at runtime."
    to="/core/run_validations/run_a_validation_definition" 
    icon="/img/expectation_icon.svg" 
  />

  <LinkCard 
    topIcon 
    label="Retrieve all unexpected rows"
    description="Fetch every failing row from an UnexpectedRowsExpectation without the 200-row cap."
    to="/core/run_validations/retrieve_all_unexpected_rows" 
    icon="/img/expectation_icon.svg" 
  />

</LinkCardGrid>