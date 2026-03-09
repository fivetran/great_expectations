---
sidebar_label: 'Connect GX Cloud'
title: 'Connect GX Cloud'
hide_title: true
description: Connect GX Cloud to your deployment environment.
hide_feedback_survey: true
---

import LinkCardGrid from '@site/src/components/LinkCardGrid';
import LinkCard from '@site/src/components/LinkCard';
import OverviewCard from '@site/src/components/OverviewCard';

<OverviewCard title={frontMatter.title}>
  Connect GX Cloud to your deployment environment.
</OverviewCard>

<LinkCardGrid>
  <LinkCard topIcon label="Connect GX Cloud to Amazon S3" description="Start using GX Cloud with Amazon S3." to="/cloud/connect/connect_s3" icon="/img/s3_icon.png" />
  <LinkCard topIcon label="Connect GX Cloud to Databricks SQL" description="Start using GX Cloud with Databricks SQL." to="/cloud/connect/connect_databrickssql" icon="/img/databricks_icon.svg" />
  <LinkCard topIcon label="Connect GX Cloud to Microsoft Fabric" description="Start using GX Cloud with Microsoft Fabric." to="/cloud/connect/connect_fabric" icon="/img/fabric_icon.svg" />
  <LinkCard topIcon label="Connect GX Cloud to Microsoft SQL Server" description="Start using GX Cloud with Microsoft SQL Server." to="/cloud/connect/connect_sqlserver" icon="/img/sqlserver_icon.svg" />
  <LinkCard topIcon label="Connect GX Cloud to PostgreSQL" description="Start using GX Cloud with PostgreSQL." to="/cloud/connect/connect_postgresql" icon="/img/postgresql_icon.svg" />
  <LinkCard topIcon label="Connect GX Cloud to Redshift" description="Start using GX Cloud with Redshift." to="/cloud/connect/connect_redshift" icon="/img/redshift_icon.png" />
  <LinkCard topIcon label="Connect GX Cloud to Snowflake" description="Start using GX Cloud with Snowflake." to="/cloud/connect/connect_snowflake" icon="/img/snowflake_icon.png" />
  <LinkCard topIcon label="Connect to GX Cloud with Python" description="Start using GX Cloud with Python." to="/cloud/connect/connect_python" icon="/img/python_icon.svg" />
</LinkCardGrid>
