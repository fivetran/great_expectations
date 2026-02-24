---
title: 'Deployment patterns'
id: deployment_patterns
description: Explore GX Cloud deployment patterns.
toc_min_heading_level: 2
toc_max_heading_level: 2
---

GX Cloud deployment patterns are defined by how GX Cloud connects to your data. The primary deployment pattern is a [fully-hosted deployment](#fully-hosted-deployment).

| Deployment pattern | Summary | When to use |
| :-- | :-- | :-- |
| [Fully-hosted](#fully-hosted-deployment) | GX Cloud connects directly to your data through a secure, cloud-to-cloud connection. If you use [ExpectAI](/cloud/overview/accelerating_test_coverage.md#expectai), it is powered by a GX LLM. | You want to get started quickly and securely with GX Cloud and use direct Data Source connections. |
| [Agent-enabled](#agent-enabled-deployment) | GX Cloud connects to your data through the GX Agent, a utility that you run in your environment. The Agent serves as an intermediary between GX Cloud and your data; in this deployment pattern, GX Cloud does not connect directly to your data. If you want to use [ExpectAI](/cloud/overview/accelerating_test_coverage.md#expectai), you will provide an LLM API key to the Agent so that it can perform data analysis using your own LLM. | You want to connect to Data Sources using your organization's environment and infrastructure, for enhanced control and security. |

If your GX Cloud organization has [multiple workspaces](/cloud/access/manage_access.md#workspaces), note that each deployment pattern applies at the organization level. All workspaces in your organization must use the same deployment pattern. 


## Fully-hosted deployment

In a fully-hosted deployment, GX Cloud connects directly to your organization's data using a cloud-to-cloud connection with encrypted communication.  If you use [ExpectAI](/cloud/overview/accelerating_test_coverage.md#expectai), samples of your data are sent to a GX LLM for analysis. Fully-hosted deployments are the quickest way to get started with GX Cloud.

![GX Cloud has a web UI, storage, and backend managed by Great Expectations.](./deployment_images/fully_hosted_deployment.png)

If you are using a fully-hosted deployment, ensure that the following GX Cloud IPs are in your organization's allow list for ingress traffic.
- `44.209.54.123`
- `54.235.167.60`
- `34.194.243.19`

## Agent-enabled deployment

In an agent-enabled deployment, the GX Agent runs in your environment and serves as an intermediary between GX Cloud and your data. GX Cloud sends jobs to the GX Agent, the GX Agent connects to and interacts with your data, and the GX Agent reports job results back to GX Cloud. If you use [ExpectAI](/cloud/overview/accelerating_test_coverage.md#expectai), the GX Agent uses your own LLM to analyze samples of your data. Your LLM API key and all data processed by ExpectAI remain within your environment. AI usage is billed to your own LLM account.

![GX Cloud has a web UI, storage, and backend managed by Great Expectations.](./deployment_images/agent_enabled_deployment.png)

The GX Agent is a Docker container that can be run in your organization's deployment environment or locally. See [Deploy the GX Agent](/cloud/deploy/deploy_gx_agent.md) for setup details.
