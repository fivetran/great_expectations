---
sidebar_label: 'Manage access'
title: 'Manage access'
description: Manage your organization's access to GX Cloud.
---

With GX Cloud’s access control options, you can ensure security and make collaboration more efficient. This page covers configuration for multiple workspaces, individual users, and access tokens. 

:::tip Want to configure SSO?
SSO is available on the Enterprise plan. Contact sales to [upgrade to Enterprise](https://greatexpectations.io/pricing/). 
:::

## Workspaces

GX Cloud helps you spread the work of managing data quality across your business, so you can use knowledge from various stakeholders to ensure high standards. GX Cloud offers multiple workspaces to organizations on the [Enterprise plan](https://greatexpectations.io/pricing/) to support collaborating with many teams in GX Cloud without compromising on security or structure within the application. With workspaces, you can group your Data Sources, Data Assets, and users in flexible ways. For example, you might create different workspaces based on the following:

- Functions (e.g., engineering and finance) 
- Medallion architecture (e.g., Bronze, Silver, and Gold layers)

Workspaces help keep your data quality efforts clear, relevant, and secure, no matter how complex your business is. Here's one example of how an organization might use multiple workspaces.

![Example organization with two workspaces that demonstrates the following principles. Organization Owners have full access to all workspaces. Other users have permissions granted on a workspace basis. Each Data Source and Data Asset belongs to a single workspace. A given table can be added as a Data Asset in multiple workspaces. Expectations are specific to each Data Asset.](/img/workspaces.png)


Keep the following in mind when using workspaces:
- Your organization must be on the Enterprise plan to use multiple workspaces. Contact sales to [upgrade to Enterprise](https://greatexpectations.io/pricing/). 
- You must be an [Organization Owner](#roles-and-permissions) to manage workspaces.
- To use the GX Cloud API in an organization with multiple workspaces, your [GX library](https://pypi.org/project/great-expectations/) version must be >= 1.6.0. 


### Create a workspace

1. In GX Cloud, click **Workspaces**.
2. Click **New workspace**.
3. Enter a **Workspace name**.
4. Click **Create**.

Now you can [invite users](#invite-a-user) to collaborate in the workspace. Note that Organization Owners will automatically have access to the new workspace.

### Edit a workspace 

To change the name of a workspace, follow the instructions below. To change the membership of a workspace, [edit users](#edit-a-workspace-users-role).

1. In GX Cloud, click **Workspaces**.
2. Click <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/> **Edit workspace** for the workspace that you want to rename.
3. Change the **Workspace name**.
4. Click **Save**.

When you rename a workspace, old links and integrations for that workspace will still function. But, you may want to let your team know about the change so they can find what they’re looking for in the GX Cloud UI. 

### Delete a workspace

To delete a workspace, follow the instructions below.

1. In GX Cloud, click **Workspaces**.
2. Click <img src="/img/trash.png" alt="trash icon" width="20" height="20"/> **Delete workspace** for the workspace that you want to remove.
3. Review the warning and enter the workspace name to confirm you understand the consequences and want to proceed.
4. Click **Delete**.

## Users

Workspace users can be members of multiple workspaces with different permissions. Organization Owners are always members of all workspaces with full permissions.

### Roles and permissions


The following table lists GX Cloud roles and permissions.

| User role                                            | Organization Owner                          | Workspace Admin                             | Workspace Editor                           | Workspace Viewer                           |
|------------------------------------------------------|---------------------------------------------|---------------------------------------------|--------------------------------------------|--------------------------------------------|
| Manage workspaces                                    | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="No">❌ </span> |
| Manage Organization Owners                           | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="No">❌ </span> |
| Manage organization access tokens                    | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="No">❌ </span> |
| Manage workspace users *                             | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="No">❌ </span> |
| Manage workspace integrations *                      | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="No">❌ </span> |
| Manage user access tokens *                          | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="No">❌ </span> |
| Manage Data Sources, Data Assets, and Expectations * | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="No">❌ </span> |
| View history for Data Assets and Expectations *      | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> |
| View Validation Results *                            | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> |

\* Scoped to the workspace(s) the user belongs to.

### Invite a user

1. In GX Cloud, click **Users**.

2. Click **Invite user** and complete the following fields:

    - **Workspace** - If you’re adding a Workspace Admin, Editor, or Viewer, select a workspace. If you’re adding an Organization Owner, they will automatically have full access to all current and future workspaces. 

    - **Email** - Enter the user's email address.
       :::note Allowed email domains
       To help keep your business secure,  your GX Cloud organization has an allowlist of email domains that all user email addresses must belong to. By default, the allowlist includes the email domain of the Organization Owner who created the organization. To request changes to your organization’s email domain allowlist, have an Organization Owner [contact support](mailto:support@greatexpectations.io).
       :::

    - **Role** - See [roles and permissions](#roles-and-permissions) for details on the options.

3. Click **Send invitation**.

    An email invitation is sent to the user.

### Edit a workspace user’s role

Workspace user permissions are managed on a workspace basis. To edit a user’s role across multiple workspaces, repeat the following steps. You can search for a user by email to make it easier to find all the workspaces they belong to.

1. In GX Cloud, click **Users**.

2. Find the workspace for which you want to edit a user’s role.

3. Click <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/> **Edit user**  for the person you want to update.

4. Select a role and then click **Update user**. 

### Edit an Organization Owner’s role

Organization Owners have access to all workspaces. When you downgrade an Organization Owner’s role, you select one workspace for them to continue to belong to. After that, you can [invite](#invite-a-user) them to additional workspaces as needed. 

1. In GX Cloud, click **Users**.
2. Find the workspace you want the downgraded user to continue to belong to.
3. Click  <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/> **Edit user** for the Organization Owner you want to update.
4. Select a workspace **Role**.
5. Click **Update user**.

### Delete a user’s access

Workspace user access is managed on a workspace basis. To remove a workspace user’s access across multiple workspaces, repeat the following steps. You can search for a user by email to make it easier to find all the workspaces they belong to. If you delete an Organization Owner, they lose access to all workspaces immediately. If you delete a user from all of their workspaces, they lose all access to GX Cloud.

1. In GX Cloud, click **Users**.
2. If you’re removing a workspace-level user’s access, find the workspace from which you want to remove the user.
3. Click <img src="/img/trash.png" alt="trash icon" width="20" height="20"/> **Remove user** for the person you want to remove.
4. Click **Remove**.

:::note Alerts are managed separately
When you delete a user’s access, any [alerts](/cloud/alerts/alert_about_failures.md) configured with that user as a recipient are left as they are. Depending on the reason for removing the user, you may want to update your alert configuration so that the person no longer receives notifications about failing Expectations.
:::

## Tokens

Tokens provide secure access to your GX Cloud entities through the GX Cloud API. 

:::tip Keep your tokens secure
Access tokens shouldn't be committed to version control software.
:::
 
Here is an overview of the different types of tokens.

| Token type                                  | User access token                                                                                                                                                                                                                                                                                                         | Organization access token                                                                                                                                                                           |
|---------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Token [permissions](#roles-and-permissions) | Inherited from the user the token belongs to, capped by the user's role at the time the token was created.<br /><br />If a user’s permissions are changed after a token was created, the token’s permissions are changed as well, except that token permissions will never exceed the role the user had when the token was created. | Workspace Editor.                                                                                                                                                                                   |
| Workspace scope                             | Inherited from the user a token belongs to.<br /> <br />If a user’s workspace membership is changed after a token is created, the token’s scope is changed as well.                                                                                                                                                       | All workspaces.                                                                                                                                                                                     |
| Common use cases                            | Connecting Data Sources, adding Data Assets, and creating Expectations.                                                                                                                                                                                                                                                   | External application authentication for tasks such as deploying the GX Agent or orchestrating validation runs.                                                                                                                |
| Ownership                                   | Each Workspace Editor, Workspace Admin, or Organization Owner manages their own user access tokens.                                                                                                                                                                                                                       | Organization Owners collectively manage a pool of organization access tokens.<br /> <br />If an Organization Owner is removed or demoted, any organization access tokens they created are not affected. |


### Create a user access token

You can create your own user access tokens if you are a Workspace Editor, Workspace Admin, or Organization Owner.

1. In GX Cloud, click **Tokens**.
2. In the **User access tokens** pane, click **Create user access token**.
3. In the **Token name** field, enter a name for the token that will help you quickly identify it.
4. Click **Create**.
5. Copy, paste, and then save the user access token as a text file or similar. The token can't be retrieved after you close the dialog.
6. Click **Close**.

### Create an organization access token

You must be an Organization Owner to create an organization access token. 

1. In GX Cloud, click **Tokens**.
2. In the **Organization access tokens** pane, click **Create organization access token**.
3. In the **Token name** field, enter a name for the token that will help you quickly identify it.
4. Click **Create**.
5. Copy, paste, and then save the organization access token as a text file or similar. The token can't be retrieved after you close the dialog.
6. Click **Close**.

### Delete a user or organization access token

1. In GX Cloud, click **Tokens**.
2. Click <img src="/img/trash.png" alt="trash icon" width="20" height="20"/> **Delete token** for the token you want to remove.
3. Click **Delete** to confirm.

