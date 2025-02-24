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
      type: 'doc',
      label: 'GX Cloud overview',
      id: 'cloud/overview/gx_cloud_overview'
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
      type: 'doc',
      label: 'Manage Data Assets',
      id: 'cloud/data_assets/manage_data_assets'
    },
    {
      type: 'doc',
      label: 'Manage Expectations',
      id: 'cloud/expectations/manage_expectations'
    },
    {
      type: 'doc',
      label: 'Manage Validations',
      id: 'cloud/validations/manage_validations'
    },
    {
      type: 'doc',
      label: 'Manage schedules',
      id: 'cloud/schedules/manage_schedules'
    },
    {
      type: 'doc',
      label: 'Manage alerts',
      id: 'cloud/alerts/manage_alerts'
    },
    {
      type: 'doc',
      label: 'Manage users and access tokens',
      id: 'cloud/users/manage_users'
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

