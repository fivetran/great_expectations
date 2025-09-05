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

If your organization is on the [Enterprise plan](https://greatexpectations.io/pricing/), you can use workspaces to group your Data Assets and users by team or environment. Beyond improving security, this makes it easier for people to find and focus on what’s relevant to them.

When you create a Data Source or Data Asset, you create it within a single given workspace. They cannot be moved to different workspaces or associated with multiple workspaces. Users however can be granted access to any number of workspaces. A user can have different permissions in the different workspaces they belong to. 

You must be an [Organization Owner](#roles-and-permissions) to manage workspaces.

### Create a workspace

1. In GX Cloud, click **Workspaces**.
2. Click **New workspace**.
3. Enter a **Workspace name**.
4. Click **Create**.

Now you can [invite users](#invite-a-user) to collaborate in the workspace. Note that Organization Owners will automatically have access to the new workspace.

### Edit a workspace 

To change the name of a workspace, follow the below instructions. To change the membership of a workspace, [edit users](#edit-a-user-role).

1. In GX Cloud, click **Workspaces**.
2. Click <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/> **Edit workspace** for the workspace that you want to rename.
3. Change the **Workspace name**.
4. Click **Save**.

 When you rename a workspace, old links and integrations for that workspace will still function. But, you may want to let your team know about the change so they can find what they’re looking for in the GX Cloud UI. 

### Delete a workspace

 Note that you cannot delete the default workspace. To delete a non-default workspace, follow the below instructions.

1. In GX Cloud, click **Workspaces**.
2. Click <img src="/img/trash.png" alt="trash icon" width="20" height="20"/> **Delete workspace** for the workspace that you want to remove.
3. Review the warning and enter the workspace name to confirm you understand the consequences and want to proceed.
4. Click **Delete**.

## Users

 Workspace users can be members of multiple workspaces with different permissions. Organization Owners are always members of all workspaces with full permissions.

### Roles and permissions


The following table lists GX Cloud roles and permissions.

| User Role                                           | Organization Owner                          | Workspace Admin                             | Workspace Editor                           | Workspace Viewer                           |
|-----------------------------------------------------|---------------------------------------------|---------------------------------------------|--------------------------------------------|--------------------------------------------|
| Manage workspaces                                   | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="No">❌ </span> |
| Manage Organization Owners                          | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="No">❌ </span> |
| Manage organization access tokens                   | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="No">❌ </span> |
| Manage workspace users*                             | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="No">❌ </span> | <span role="img" aria-label="No">❌ </span> |
| Manage user access tokens*                          | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="No">❌ </span> |
| Manage Data Sources, Data Assets, and Expectations* | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="No">❌ </span> |
| View Validation Results*                            | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> | <span role="img" aria-label="Yes">✅</span> |

* Scoped to the workspace(s) the user belongs to.

## Invite a user

1. In GX Cloud, click **Users**.

2. Click **Invite User** and complete the following fields:

    - **Email** - Enter the user's email address.

    - **Role** - See [roles and permissions](#roles-and-permissions) for details on the options.

    - **Workspace** - If you’re adding a Workspace Admin, Editor, or Viewer, select a workspace. If you’re adding an Organization Owner, they will automatically have full access to all current and future workspaces. 

3. Click **Invite**.

    An email invitation is sent to the user.

## Edit a workspace user’s role

Workspace user permissions are managed on a workspace basis. To edit a user’s role across multiple workspaces, repeat the following steps. You can search for a user by email to make it easier to find all the workspaces they belong to.

1. In GX Cloud, click **Users**.

2. Find the workspace for which you want to edit a user’s role

3. Click <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/> **Edit user**  for the person you want to update.

4. Select a role and then click **Update User**. 

### Edit an Organization Owner’s role

Organization Owners have access to all workspaces. When you downgrade an Organization Owner’s role, you select one workspace for them to belong to. After that, you can [invite](#invite-a-user) them to additional workspaces as needed. 

1. In GX Cloud, click **Users**.
2. Click  <img src="/img/pencil.png" alt="pencil icon" width="20" height="20"/> **Edit user** for the Organization Owner you want to update.
3. Select a workspace **Role**.
4. Select a **Workspace**.
5. Click **Update User**.

### Delete a user’s access

Workspace user access is managed on a workspace basis. To remove a workspace user’s access across multiple workspaces, repeat the following steps. You can search for a user by email to make it easier to find all the workspaces they belong to. If you delete an Organization Owner, they lose access to all workspaces immediately.

1. In GX Cloud, click **Users**.
2. If you’re removing a workspace-level user’s access, find the workspace from which you want to remove the user.
3. Click <img src="/img/trash.png" alt="trash icon" width="20" height="20"/> **Remove user** for the person you want to remove.
4. Click **Yes, Remove This User**.


## Tokens

Tokens provide secure access to your GX Cloud entities though the GX Cloud API. 

:::tip Keep your tokens secure
Access tokens shouldn't be committed to version control software.
:::
 
Here is an overview of the different types of tokens.

| Token type                                  | User access token                                                                                                                                               | Organization access token                                                                                                                                                                       |
|---------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Token [permissions](#roles-and-permissions) | Inherited from the user a token belongs to.<br>If a user’s permissions are changed after a token is created, the token’s permissions are changed as well.       | Workspace Editor.                                                                                                                                                                               |
| Workspace scope                             | Inherited from the user a token belongs to.<br> <br>If a user’s workspace membership is changed after a token is created, the token’s scope is changed as well. | All workspaces.                                                                                                                                                                                 |
| Common use cases                            | Connecting Data Sources, adding Data Assets, and creating Expectations.                                                                                         | External application authentication for tasks such as orchestrating validation runs.                                                                                                            |
| Ownership                                   | Each Workspace Editor, Workspace Admin, or Organization Owner manages their own user access tokens.                                                             | Organization Owners collectively manage a pool of organization access tokens.<br> <br>If an Organization Owner is removed or demoted, organization access tokens they created are not affected. |

## Create a user access token

You can create your own user access tokens if you are a Workspace Editor, Workspace Admin, or Organization Owner.

1. In GX Cloud, click **Tokens**.
2. In the **User access token**s pane, click **Create user access token**.
3. In the **Token nam**e field, enter a name for the token that will help you quickly identify it.
4. Click **Create**.
5. Copy, paste, and then save the user access token as a text file or similar. The token can't be retrieved after you close the dialog.
6. Click **Close**.

## Create an organization access token

You must be an Organization Owner to create an organization access token. 

1. In GX Cloud, click **Tokens**.
2. In the **Organization access tokens** pane, click **Create organization access token**.
3. In the **Token name** field, enter a name for the token that will help you quickly identify it.
4. Click **Create**.
5. Copy, paste, and then save the organization access token as a text file or similar. The token can't be retrieved after you close the dialog.
6. Click **Close**.

## Delete a user or organization access token

1. In GX Cloud, click **Tokens**.
2. Click <img src="/img/trash.png" alt="trash icon" width="20" height="20"/> **Delete token** for the token you want to remove.
3. Click **Delete** to confirm.

