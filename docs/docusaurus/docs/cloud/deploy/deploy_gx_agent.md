---
title: 'Deploy the GX Agent'
id: deploy_gx_agent
description: Deploy the GX Agent to connect to your Data Source within your own environment.
toc_min_heading_level: 2
toc_max_heading_level: 2
---

import TabItem from '@theme/TabItem';
import Tabs from '@theme/Tabs';


The GX Agent is used to run an [agent-enabled deployment](/cloud/deploy/deployment_patterns.md#agent-enabled-deployment) of GX Cloud. If you are running a fully-hosted deployment or using the GX Cloud API, you do not need to deploy the GX Agent.

The GX Agent serves as an intermediary between GX Cloud and your organization's data stores. GX Cloud does not connect directly to your data in an agent-enabled deployment, and all data access occurs within the GX Agent. GX Cloud sends jobs to the GX Agent, the GX Agent executes these jobs against your data, and then sends the job results to GX Cloud.

If you use [ExpectAI](/cloud/overview/accelerating_test_coverage.md#expectai), the GX Agent uses your own OpenAI project to analyze samples of your data. Your OpenAI API key and all data processed by ExpectAI remain within your environment.

A local deployment of the GX Agent will allow you to test GX Cloud setup or processes from a single machine before moving to a shared production deployment. Alternatively, you can run the GX Agent in your deployment environment and leverage GX Cloud while connecting to Data Sources using your organization's environment and infrastructure, for enhanced control and security.


## Prerequisites

- You are an [Organization Owner](/cloud/access/manage_access.md#roles-and-permissions).
- You have a [Docker instance](https://docs.docker.com/get-docker/) or [kubectl](https://kubernetes.io/docs/tasks/tools/).
- Optional. If you want to use [ExpectAI](/cloud/overview/accelerating_test_coverage.md#expectai), you have an [OpenAI](https://openai.com/) project that allows [Model Usage](https://help.openai.com/en/articles/9186755-managing-projects-in-the-api-platform#h_d4737514e7) of `gpt-4o-2024-11-20`, and you can create an OpenAI API token.

## Enable the GX Agent

The GX Agent is not enabled by default in GX Cloud. To enable the GX Agent for your GX Cloud organization, request the Agent when adding a Data Source. The workflow depends on whether or not your workspace has any Data Sources yet.

<Tabs
  groupId="request-agent"
  defaultValue='none'
  values={[
  {label: 'No Data Sources yet', value:'none'},
  {label: 'Existing Data Sources', value:'some'},
  ]}>
<TabItem value="none">

1. Go to **Data Assets**.
2. Select a Data Source type.
3. Click **Request Agent**.

</TabItem>
<TabItem value="some">

1. Go to **Data Assets**.
2. Select **New Data Asset**.
3. Select **New Data Source**.
4. Select a Data Source type.
5. Click **Request Agent**.

</TabItem>
</Tabs>

You can continue following the steps below to deploy the GX Agent while you wait for it to be enabled for your organization.

## Get your credentials

You need your GX Cloud access token and organization ID to deploy the GX Agent. If you want to use [ExpectAI](/cloud/overview/accelerating_test_coverage.md#expectai), you will also need your OpenAI API key. Access tokens and API keys shouldn't be committed to version control software.

1. In GX Cloud, click **Tokens**.

2. In the **User access tokens** pane, click **Create user access token**.

3. In the **Token name** field, enter a name for the token that will help you quickly identify it.

4. Click **Create**.

5. Copy and then paste the user access token into a temporary file. The token can't be retrieved after you close the dialog.

6. Click **Close**.

7. Copy the value in the **Organization ID** field into the temporary file with your user access token and then save the file. 

8. Optional. If you want to use [ExpectAI](/cloud/overview/accelerating_test_coverage.md#expectai), go to your OpenAI dashboard’s [API keys](https://platform.openai.com/api-keys) page, create a new secret key with **Restricted** permissions that grant **Model capabilities: Write**, copy the secret key value into the temporary file with your GX credentials, and then save the file.

9. [Deploy the GX Agent](#deploy-the-gx-agent).

GX recommends deleting the temporary file after you set the environment variables.

## Deploy the GX Agent

The GX Agent allows you to securely access your data without connecting to it or interacting with it directly.

<Tabs
  groupId="deploy-agent"
  queryString="env-type"
  defaultValue='deployment'
  values={[
  {label: 'Deployment environment', value:'deployment'},
  {label: 'Local', value:'local'},
  ]}>
<TabItem value="deployment">

You can deploy the GX Agent container in any deployment environment where you can run Docker container images.

To learn how to deploy a Docker container image in a specific environment, see the following documentation:

- [Quickstart: Deploy a container instance in Azure using the Azure CLI](https://learn.microsoft.com/en-us/azure/container-instances/container-instances-quickstart)

- [Build and push a Docker image with Google Cloud Build](https://cloud.google.com/build/docs/build-push-docker-image)

- [Deploy Docker Containers on Amazon ECS](https://aws.amazon.com/getting-started/hands-on/deploy-docker-containers/)

You can deploy the GX Agent in any environment in which you create Kubernetes clusters. For example:

- [Amazon Elastic Kubernetes Service (EKS)](https://docs.aws.amazon.com/eks/latest/userguide/getting-started.html)

- [Microsoft Azure Kubernetes Service (AKS)](https://learn.microsoft.com/en-us/azure/architecture/reference-architectures/containers/aks-start-here)

- [Google Kubernetes Engine (GKE)](https://cloud.google.com/kubernetes-engine/docs)

- Any Kubernetes cluster version 1.21 or greater which uses standard Kubernetes

<Tabs
  groupId="connect-PostgreSQL"
  defaultValue='docker'
  values={[
  {label: 'Docker', value:'docker'},
  {label: 'Kubernetes', value:'kubernetes'},
  ]}>
<TabItem value="docker">

1. Download the GX Agent Docker container image from [Docker Hub](https://hub.docker.com/r/greatexpectations/agent).

2. After configuring your cloud service to run Docker containers, run the following Docker command to start the GX Agent: 

   ```bash title="Terminal input"
   docker run -it -e GX_CLOUD_ACCESS_TOKEN="<YOUR_ACCESS_TOKEN>" -e GX_CLOUD_ORGANIZATION_ID="<YOUR_ORGANIZATION_ID>" -e OPENAI_API_KEY="<YOUR_API_KEY>"  greatexpectations/agent:stable
    ```
    Replace `<YOUR_ACCESS_TOKEN>`, `<YOUR_ORGANIZATION_ID>`, and `<YOUR_API_KEY>` with the [credential values](#get-your-credentials) that you copied previously. If you don’t want to use [ExpectAI](/cloud/overview/accelerating_test_coverage.md#expectai), you can omit setting `OPENAI_API_KEY`.

3. Optional. If you created a temporary file to record your credentials, delete it.

4. Optional. Run the following command to use the GX Agent image as the base image and optionally add custom commands:

   ```bash title="Terminal input"
   FROM greatexpectations/agent:stable
   RUN echo "custom_commands"
   ```
5. Optional. Run the following command to rebuild the Docker image:

   ```bash title="Terminal input"
   docker build -t myorg/agent
   ```
6. Optional. Run `docker ps` or open Docker Desktop to confirm the agent is running.

</TabItem>
<TabItem value="kubernetes">

1. Install kubectl. See [Install Tools](https://kubernetes.io/docs/tasks/tools/).

2. Run the following command to provide the access credentials to the Kubernetes container:
    
   ```bash title="Terminal input"
   kubectl create secret generic gx-agent-secret \
   --from-literal=GX_CLOUD_ORGANIZATION_ID=YOUR_ORGANIZATION_ID \
   --from-literal=GX_CLOUD_ACCESS_TOKEN=YOUR_ACCESS_TOKEN \
   --from-literal=OPENAI_API_KEY=YOUR_API_KEY \
   ```
    Replace `YOUR_ORGANIZATION_ID`, `YOUR_ACCESS_TOKEN`, and `YOUR_API_KEY` with the [credential values](#get-your-credentials) that you copied previously. If you don’t want to use [ExpectAI](/cloud/overview/accelerating_test_coverage.md#expectai), you can omit setting `OPENAI_API_KEY`.

3. Optional. If you created a temporary file to record your credentials, delete it.

4. Create and save a file named `deployment.yaml`, with the following configuration:

   ```yaml title="deployment.yaml"
   apiVersion: apps/v1
   kind: Deployment
   metadata:
    name: gx-agent
    labels:
    app: gx-agent
    spec:
    replicas: 1
    selector:
    matchLabels:
    app: gx-agent
    template:
    metadata:
      labels:
        app: gx-agent
    spec:
      containers:
       name: gx-agent
        image: greatexpectations/agent:stable
        imagePullPolicy: Always
        envFrom:
        secretRef:
         name: gx-agent-secret
   ```
5. Run the following command to use the `deployment.yaml`configuration file to deploy the GX Agent:

   ```bash title="Terminal input"
   kubectl apply -f deployment.yaml
   ```
6. Optional. Run the following command to confirm the agent is running:

   ```bash title="Terminal input"
   kubectl logs -l app=gx-agent
   ```
7. Optional. Run the following command to terminate running resources gracefully:

   ```bash title="Terminal input"
   kubectl delete -f deployment.yaml
   kubectl delete secret gx-agent-secret
   ```

</TabItem>
</Tabs>
</TabItem>
<TabItem value="local">

1. Start the Docker Engine.

2. Run the following code to set environment variables, install GX Cloud and its dependencies, and start the GX Agent:

    ```bash title="Terminal input"
    docker run --rm --pull=always -e GX_CLOUD_ACCESS_TOKEN="<YOUR_ACCESS_TOKEN>" -e GX_CLOUD_ORGANIZATION_ID="<YOUR_ORGANIZATION_ID>" -e OPENAI_API_KEY="<YOUR_API_KEY>"  greatexpectations/agent:stable
    ```
   Replace `<YOUR_ACCESS_TOKEN>`, `<YOUR_ORGANIZATION_ID>`, and `<YOUR_API_KEY>` with the [credential values](#get-your-credentials) that you copied previously. If you don’t want to use [ExpectAI](/cloud/overview/accelerating_test_coverage.md#expectai), you can omit setting `OPENAI_API_KEY`.

3. In GX Cloud, confirm the GX Agent status is **Active Agent** and the icon is green. This indicates the GX Agent is active. If it isn't, repeat step 2 and confirm the `user_access_token` and `organization_id` values are correct.

    ![GX Agent status](/img/gx_agent_status.png)

4. Optional. If you created a temporary file to record your credentials, delete it.

5. Optional. Run `docker ps` or open Docker Desktop to confirm the agent is running.

    If you stop the GX Agent, close the terminal, and open a new terminal you'll need to set the environment variables again.

    To edit an environment variable, stop the GX Agent, edit the environment variable, save the change, and then restart the GX Agent.

</TabItem>
</Tabs>

## GX Agent versioning
GX uses a date-based versioning format for its weekly GX Agent Docker image releases: `YYYYMMMDD.#` for stable releases and `YYYYMMDD.#.dev#` for pre-releases. GX uses the `stable` and `dev` Docker image tags to identify the release type. The `stable` tag indicates the image is fully tested and ready for use. The `dev` tag indicates a pre-release image.
