module.exports = {
  gx_core: [
    {
      type: 'category',
      label: 'Introduction to GX Core',
      link: { type: 'doc', id: 'core/introduction/introduction' },
      items: [
        {
          type: 'doc',
          id: 'core/introduction/gx_overview',
          label: 'GX Core overview'
        },
        {
          type: 'doc',
          id: 'core/introduction/try_gx',
          label: 'Try GX Core'
        }
      ],
    },
    {
      type: 'category',
      label: 'Set up a GX environment',
      link: { type: 'doc', id: 'core/set_up_a_gx_environment/set_up_a_gx_environment' },
      items: [
        {
          type: 'doc',
          id: 'core/set_up_a_gx_environment/install_python',
          label: 'Install Python'
        },
        {
          type: 'doc',
          id: 'core/set_up_a_gx_environment/install_gx',
          label: 'Install GX'
        },
        {
          type: 'doc',
          id: 'core/set_up_a_gx_environment/install_additional_dependencies',
          label: 'Install additional dependencies'
        },
        {
          type: 'doc',
          id: 'core/set_up_a_gx_environment/create_a_data_context',
          label: 'Create a Data Context'
        }
      ]
    },
    {
      type: 'category',
      label: 'Connect to data',
      link: { type: 'doc', id: 'core/connect_to_data/connect_to_data' },
      items: [
        {
          type: 'doc',
          id: 'core/connect_to_data/sql_data/sql_data',
          label: 'Connect to SQL data'
        },
        {
          type: 'doc',
          id: 'core/connect_to_data/filesystem_data/filesystem_data',
          label: 'Connect to Filesystem data'
        },
        {
          type: 'doc',
          id: 'core/connect_to_data/dataframes/dataframes',
          label: 'Connect to data in Dataframes'
        },
      ]
    },
    {
      type: 'category',
      label: 'Define Expectations',
      link: { type: 'doc', id: 'core/define_expectations/define_expectations' },
      items: [
        {
          type: 'doc',
          id: 'core/define_expectations/create_an_expectation',
          label: 'Create an Expectation'
        },
        {
          type: 'doc',
          id: 'core/define_expectations/retrieve_a_batch_of_test_data',
          label: 'Retrieve a Batch of sample data'
        },
        {
          type: 'doc',
          id: 'core/define_expectations/test_an_expectation',
          label: 'Test an Expectation'
        },
        {
          type: 'doc',
          id: 'core/define_expectations/organize_expectation_suites',
          label: 'Organize Expectations into an Expectation Suite'
        },
      ]
    },
    {
      type: 'category',
      label: 'Run Validations',
      link: { type: 'doc', id: 'core/run_validations/run_validations' },
      items: [
        { type: 'doc', id: 'core/run_validations/create_a_validation_definition' },
        { type: 'doc', id: 'core/run_validations/run_a_validation_definition' },
      ]
    },
    {
      type: 'category',
      label: 'Trigger actions based on results',
      link: { type: 'doc', id: 'core/trigger_actions_based_on_results/trigger_actions_based_on_results' },
      items: [
        { type: 'doc', id: 'core/trigger_actions_based_on_results/create_a_checkpoint_with_actions' },
        { type: 'doc', id: 'core/trigger_actions_based_on_results/create_a_custom_action' },
        { type: 'doc', id: 'core/trigger_actions_based_on_results/choose_a_result_format/choose_a_result_format' },
        { type: 'doc', id: 'core/trigger_actions_based_on_results/run_a_checkpoint' },
      ]
    },
    {
      type: 'category',
      label: 'Customize Expectations',
      link: { type: 'doc', id: 'core/customize_expectations/customize_expectations' },
      items: [
        { type: 'doc', id: 'core/customize_expectations/expectation_conditions' },
        { type: 'doc', id: 'core/customize_expectations/define_a_custom_expectation_class' },
        { type: 'doc', id: 'core/customize_expectations/use_sql_to_define_a_custom_expectation' },
      ]
    },
    {
      type: 'category',
      label: 'Configure project settings',
      link: { type: 'doc', id: 'core/configure_project_settings/configure_project_settings' },
      items: [
        { type: 'doc', id: 'core/configure_project_settings/configure_metadata_stores/configure_metadata_stores' },
        { type: 'doc', id: 'core/configure_project_settings/configure_data_docs/configure_data_docs' },
        { type: 'doc', id: 'core/configure_project_settings/configure_credentials/configure_credentials' },
        { type: 'doc', id: 'core/configure_project_settings/access_secrets_managers/access_secrets_managers' },
        { type: 'doc', id: 'core/configure_project_settings/toggle_analytics_events/toggle_analytics_events' }
      ]
    },
    {
      type: 'doc',
      id: 'oss/changelog',
      label: 'Changelog'
    },
    {
      type: 'doc',
      id: 'core/introduction/community_resources',
      label: 'Community resources'
    }
  ],
  gx_cloud: [
    {
      type: 'category',
      label: 'GX Cloud overview',
      link: { type: 'doc', id: 'cloud/overview/gx_cloud_overview' },
      items: [
        {
          type: 'link',
          label: 'GX Cloud concepts',
          href: '/docs/cloud/overview/gx_cloud_overview#gx-cloud-concepts',
        },
        {
          type: 'link',
          label: 'GX Cloud workflow',
          href: '/docs/cloud/overview/gx_cloud_overview#gx-cloud-workflow',
        },
        {
          type: 'link',
          label: 'GX Cloud architecture',
          href: '/docs/cloud/overview/gx_cloud_overview#gx-cloud-architecture',
        },
      ]
    },
    {
      type: 'category',
      label: 'Deploy GX Cloud',
      link: { type: 'doc', id: 'cloud/deploy/deploy_lp' },
      items: [
        'cloud/deploy/deployment_patterns',
        'cloud/deploy/deploy_gx_agent',
      ]
    },
    {
      type: 'category',
      label: 'Connect GX Cloud',
      link: { type: 'doc', id: 'cloud/connect/connect_lp' },
      items: [
        'cloud/connect/connect_postgresql',
        'cloud/connect/connect_snowflake',
        'cloud/connect/connect_databrickssql',
        'cloud/connect/connect_airflow',
        'cloud/connect/connect_python',
      ]
    },
    {
      type: 'category',
      label: 'Manage Data Assets',
      link: { type: 'doc', id: 'cloud/data_assets/manage_data_assets' },
      items: [
        {
          type: 'link',
          label: 'Add a Data Asset from a new Data Source',
          href: '/docs/cloud/data_assets/manage_data_assets#add-a-data-asset-from-a-new-data-source',
        },
        {
          type: 'link',
          label: 'Add a Data Asset from an existing Data Source',
          href: '/docs/cloud/data_assets/manage_data_assets#add-a-data-asset-from-an-existing-data-source',
        },
        {
          type: 'link',
          label: 'View Data Asset metrics',
          href: '/docs/cloud/data_assets/manage_data_assets#view-data-asset-metrics',
        },
        {
          type: 'link',
          label: 'Edit a Data Asset',
          href: '/docs/cloud/data_assets/manage_data_assets#edit-a-data-asset',
        },
        {
          type: 'link',
          label: 'Delete a Data Asset',
          href: '/docs/cloud/data_assets/manage_data_assets#delete-a-data-asset',
        },
        {
          type: 'link',
          label: 'Edit Data Source settings',
          href: '/docs/cloud/data_assets/manage_data_assets#edit-data-source-settings',
        },
        {
          type: 'link',
          label: 'Data Source credential management',
          href: '/docs/cloud/data_assets/manage_data_assets#data-source-credential-management',
        },
      ]
    },
    {
      type: 'category',
      label: 'Manage Expectations',
      link: { type: 'doc', id: 'cloud/expectations/manage_expectations' },
      items: [
        {
          type: 'link',
          label: 'Available Expectations',
          href: '/docs/cloud/expectations/manage_expectations#available-expectations',
        },
        {
          type: 'link',
          label: 'Custom SQL Expectations',
          href: '/docs/cloud/expectations/manage_expectations#custom-sql-expectations',
        },
        {
          type: 'link',
          label: 'Dynamic Parameters',
          href: '/docs/cloud/expectations/manage_expectations#dynamic-parameters',
        },
        {
          type: 'link',
          label: 'Expectation condition',
          href: '/docs/cloud/expectations/manage_expectations#expectation-condition',
        },
        {
          type: 'link',
          label: 'Add an Expectation',
          href: '/docs/cloud/expectations/manage_expectations#add-an-expectation',
        },
        {
          type: 'link',
          label: 'Optional. Define a Batch',
          href: '/docs/cloud/expectations/manage_expectations#optional-define-a-batch',
        },
        {
          type: 'link',
          label: 'Edit an Expectation',
          href: '/docs/cloud/expectations/manage_expectations#edit-an-expectation',
        },
        {
          type: 'link',
          label: 'Delete an Expectation',
          href: '/docs/cloud/expectations/manage_expectations#delete-an-expectation',
        },
        {
          type: 'link',
          label: 'GX-managed vs. API-managed Expectations',
          href: '/docs/cloud/expectations/manage_expectations#gx-managed-vs-api-managed-expectations',
        },
      ]
    },
    {
      type: 'category',
      label: 'Manage Validations',
      link: { type: 'doc', id: 'cloud/validations/manage_validations' },
      items: [
        {
          type: 'link',
          label: 'Run a Validation',
          href: '/docs/cloud/validations/manage_validations#run-a-validation',
        },
        {
          type: 'link',
          label: 'Run a Validation on a subset of a Data Asset',
          href: '/docs/cloud/validations/manage_validations#run-a-validation-on-a-subset-of-a-data-asset',
        },
        {
          type: 'link',
          label: 'View Validation run history',
          href: '/docs/cloud/validations/manage_validations#view-validation-run-history',
        },
      ]
    },
    {
      type: 'category',
      label: 'Manage schedules',
      link: { type: 'doc', id: 'cloud/schedules/manage_schedules' },
      items: [
        {
          type: 'link',
          label: 'Edit a schedule',
          href: '/docs/cloud/schedules/manage_schedules#edit-a-schedule',
        },
        {
          type: 'link',
          label: 'Disable a schedule',
          href: '/docs/cloud/schedules/manage_schedules#disable-a-schedule',
        },
      ]
    },
    {
      type: 'category',
      label: 'Manage alerts',
      link: { type: 'doc', id: 'cloud/alerts/manage_alerts' },
      items: [
        {
          type: "link",
          label: "Email alert default settings",
          href: "/docs/cloud/alerts/manage_alerts#email-alert-default-settings"
        },
        {
          type: "link",
          label: "Update an email alert",
          href: "/docs/cloud/alerts/manage_alerts#update-an-email-alert"
        },
      ]
    },
    {
      type: 'category',
      label: 'Manage users and access tokens',
      link: { type: 'doc', id: 'cloud/users/manage_users' },
      items: [
        {
          type: 'link',
          label: 'Roles and responsibilities',
          href: '/docs/cloud/users/manage_users#roles-and-responsibilities',
        },
        {
          type: 'link',
          label: 'Invite a user',
          href: '/docs/cloud/users/manage_users#invite-a-user',
        },
        {
          type: 'link',
          label: 'Edit a user role',
          href: '/docs/cloud/users/manage_users#edit-a-user-role',
        },
        {
          type: 'link',
          label: 'Delete a user',
          href: '/docs/cloud/users/manage_users#delete-a-user',
        },
        {
          type: 'link',
          label: 'Create a user access token',
          href: '/docs/cloud/users/manage_users#create-a-user-access-token',
        },
        {
          type: 'link',
          label: 'Create an organization access token',
          href: '/docs/cloud/users/manage_users#create-an-organization-access-token',
        },
        {
          type: 'link',
          label: 'Delete a user or organization access token',
          href: '/docs/cloud/users/manage_users#delete-a-user-or-organization-access-token',
        },
      ]
    },
    {
      type: 'link',
      label: 'Request a demo for GX Cloud',
      href: 'https://www.greatexpectations.io/demo',
      className: 'request-demo-sidebar',
    },
  ],
  gx_apis: [
    {
      type: 'category',
      label: 'GX API',
      link: {
        type: 'doc',
        id: 'reference/index'
      },
      items: [
        {
          type: 'autogenerated',
          dirName: 'reference/api'
        }
      ]
    },
  ],
  learn: [
    'reference/learn/migration_guide',
    {
      type: 'category',
      label: 'Data quality use cases',
      link: { type: 'doc', id: 'reference/learn/data_quality_use_cases/dq_use_cases_lp' },
      items: [
        'reference/learn/data_quality_use_cases/distribution',
        'reference/learn/data_quality_use_cases/freshness',
        'reference/learn/data_quality_use_cases/integrity',
        'reference/learn/data_quality_use_cases/missingness',
        'reference/learn/data_quality_use_cases/schema',
        'reference/learn/data_quality_use_cases/uniqueness',
        'reference/learn/data_quality_use_cases/volume'
      ]
    },
    {
      type: 'category',
      label: 'Integration tutorials',
      link: { type: 'doc', id: 'reference/learn/integrations/integrations_lp' },
      items: [
        'reference/learn/integrations/data_pipeline_tutorial',
        'reference/learn/integrations/dbt_tutorial',
      ]
    },
    'reference/learn/glossary'
  ],
}

