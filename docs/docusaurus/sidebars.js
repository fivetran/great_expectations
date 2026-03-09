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
      ]
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
        }
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
        }
      ]
    },
    {
      type: 'category',
      label: 'Run Validations',
      link: { type: 'doc', id: 'core/run_validations/run_validations' },
      items: [
        { type: 'doc', id: 'core/run_validations/create_a_validation_definition' },
        { type: 'doc', id: 'core/run_validations/run_a_validation_definition' }
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
        { type: 'doc', id: 'core/trigger_actions_based_on_results/run_a_checkpoint' }
      ]
    },
    {
      type: 'category',
      label: 'Customize Expectations',
      link: { type: 'doc', id: 'core/customize_expectations/customize_expectations' },
      items: [
        { type: 'doc', id: 'core/customize_expectations/row_conditions' },
        { type: 'doc', id: 'core/customize_expectations/define_a_custom_expectation_class' },
        { type: 'doc', id: 'core/customize_expectations/use_sql_to_define_a_custom_expectation' },
        { type: 'doc', id: 'core/customize_expectations/define_a_multi_source_expectation' }
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
      label: 'Introduction',
      link: { type: 'doc', id: 'cloud/gx_cloud_lp' },
      items: [
        'cloud/overview/gx_cloud_overview',
        'cloud/overview/accelerating_test_coverage',
        'cloud/overview/data_health'
      ]
    },
    {
      type: 'category',
      label: 'Deploy GX Cloud',
      link: { type: 'doc', id: 'cloud/deploy/deploy_lp' },
      items: [
        'cloud/deploy/deployment_patterns',
        'cloud/deploy/deploy_gx_agent'
      ]
    },
    {
      type: 'category',
      label: 'Connect GX Cloud',
      link: { type: 'doc', id: 'cloud/connect/connect_lp' },
      items: [
        'cloud/connect/connect_s3',
        'cloud/connect/connect_databrickssql',
        'cloud/connect/connect_fabric',
        'cloud/connect/connect_sqlserver',
        'cloud/connect/connect_postgresql',
        'cloud/connect/connect_redshift',
        'cloud/connect/connect_snowflake',
        'cloud/connect/connect_python'
      ]
    },
    {
      type: 'doc',
      label: 'Manage Data Sources',
      id: 'cloud/data_sources/manage_data_sources'
    },
    {
      type: 'doc',
      label: 'Manage Data Assets',
      id: 'cloud/data_assets/manage_data_assets'
    },
    {
      type: 'category',
      label: 'Expectations',
      link: { type: 'doc', id: 'cloud/expectations/expectations_lp' },
      items: [
        'cloud/expectations/expectations_overview',
        'cloud/expectations/manage_expectations'
      ]
    },
    {
      type: 'category',
      label: 'Validations',
      link: { type: 'doc', id: 'cloud/validations/validations_lp' },
      items: [
        'cloud/validations/run_validations',
        'cloud/validations/format_results'
      ]
    },
    {
      type: 'doc',
      label: 'Manage schedules',
      id: 'cloud/schedules/manage_schedules'
    },
    {
      type: 'category',
      label: 'Respond to results',
      link: { type: 'doc', id: 'cloud/alerts/alerts_lp' },
      items: [
        { type: 'doc', id: 'cloud/alerts/alert_about_failures' },
        { type: 'doc', id: 'cloud/alerts/trigger_actions' },
        { type: 'doc', id: 'cloud/alerts/custom_actions' }
      ]
    },
    {
      type: 'doc',
      label: 'Manage access',
      id: 'cloud/access/manage_access'
    },
    {
      type: 'category',
      label: 'Integrations',
      link: { type: 'doc', id: 'cloud/integrations/integrations_lp' },
      items: [
        'cloud/integrations/integrate_atlan',
        'cloud/integrations/integrate_airflow',
        'cloud/integrations/integrate_slack'
      ]
    },
    {
      type: 'link',
      label: 'Request a demo for GX Cloud',
      href: 'https://www.greatexpectations.io/demo',
      className: 'request-demo-sidebar'
    }
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
    }
  ],
  learn: [
    {
      type: 'category',
      label: 'GX in your data pipeline',
      link: { type: 'doc', id: 'reference/learn/gx_in_your_data_pipeline/gx_in_your_data_pipeline_lp' },
      items: [
        'reference/learn/gx_in_your_data_pipeline/ingestion',
        'reference/learn/gx_in_your_data_pipeline/transformation',
        'reference/learn/gx_in_your_data_pipeline/delivery'
      ]
    },
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
        'reference/learn/data_quality_use_cases/volume',
        'reference/learn/data_quality_use_cases/unstructured_data'
      ]
    },
    {
      type: 'category',
      label: 'Integration tutorials',
      link: { type: 'doc', id: 'reference/learn/integrations/integrations_lp' },
      items: [
        'reference/learn/integrations/data_pipeline_tutorial',
        'reference/learn/integrations/dbt_tutorial'
      ]
    },
    'reference/learn/glossary'
  ]
}
