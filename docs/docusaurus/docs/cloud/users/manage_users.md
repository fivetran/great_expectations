---
sidebar_label: 'Manage access'
title: 'Manage access'
description: Manage GX Cloud users and access tokens.
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

| User Role                                           | Organization Owner | Workspace Admin | Workspace Editor | Workspace Viewer |
|-----------------------------------------------------|--------------------|-----------------|------------------|------------------|
| Manage workspaces                                   | <span role="img" aria-label="Yes">✅</span>                  | ❌               | ❌                | ❌                |
| Manage Organization Owners                          | ✅                  | ❌               | ❌                | ❌                |
| Manage organization access tokens                   | ✅                  | ❌               | ❌                | ❌                |
| Manage workspace users*                             | ✅                  | ✅               | ❌                | ❌                |
| Manage user access tokens*                          | ✅                  | ✅               | ✅                | ❌                |
| Manage Data Sources, Data Assets, and Expectations* | ✅                  | ✅               | ✅                | ❌                |
| View Validation Results*                            | ✅                  | ✅               | ✅                | ✅                |








## Invite a user

1. In GX Cloud, click **Users**.

2. Click **Invite User** and complete the following fields:

    - **Email** - Enter the user's email address.

    - **Organization Role** - Select **Viewer**, **Editor**, or **Admin**. Viewers can view Validation Results, Editors can create and edit Expectations and can create access tokens, and Admins can perform all GX Cloud administrative functions.

3. Click **Invite**.

    An email invitation is sent to the user.

## Edit a user role

1. In GX Cloud, click **Users**.

2. Click the options menu for a user and select **Edit**.

3. Select an organization role and then click **Update User**. 

## Delete a user

1. In GX Cloud, click **Users**.

2. Click the options menu for a user and select **Delete**.

3. Click **Yes, Remove This User**.

## Create a user access token

You'll need your user access token and organization ID when you set your environment variables.

Access tokens shouldn't be committed to version control software.

1. In GX Cloud, click **Tokens**.

2. In the **User access tokens** pane, click **Create user access token**.

3. In the **Token name** field, enter a name for the token that will help you quickly identify it.

4. Click **Create**.

5. Copy, paste, and then save the user access token as a text file or similar. The token can't be retrieved after you close the dialog.

6. Click **Close**.

## Create an organization access token

Organization access tokens are typically required for external application authentication. These external applications complete tasks such as scheduled pipeline runs on behalf of your organization. 

1. In GX Cloud, click **Tokens**.

2. In the **Organization access tokens** pane, click **Create organization access token**.

3. In the **Token name** field, enter a name for the token that will help you quickly identify it.

4. Click **Create**.

5. Copy, paste, and then save the organization access token as a text file or similar. The token can't be retrieved after you close the dialog.

6. Click **Close**.

## Delete a user or organization access token

1. In GX Cloud, click **Tokens**.

2. In the **User access tokens** or **Organization access tokens** panes, click **Delete Token**.

3. Click **Delete**.

