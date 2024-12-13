# DataSource and Expectation Integration Tests
Most of the tests in this directory make use of a few utilities that help load data into various data sources.
The following sections provide an overview of how it works.

## Overview of the primary classes

The following is a rough class diagram of the main classes involved in test testing utilities.
* DataSourceTestConfig is the public interface; instance are passed to `parameterize_batch_for_data_sources`
    * Holds optional schema information
    * Knows about pymarks
* BatchTestSetup these are instantiated behind the scenes
    * Holds data
    * Knows about the actual data source
    * Sets up / tears down data

```mermaid
classDiagram
    class DataSourceTestConfig
    class BatchTestSetup

    DataSourceTestConfig <|-- PostgreSQLDatasourceTestConfig
    DataSourceTestConfig <|-- SnowflakeDatasourceTestConfig
    BatchTestSetup <|-- PostgresBatchTestSetup
    BatchTestSetup <|-- SnowflakeBatchTestSetup

    <<Abstract>> DataSourceTestConfig
    <<Abstract>> BatchTestSetup

    DataSourceTestConfig : +str label
    DataSourceTestConfig : +str pytest_marks
    DataSourceTestConfig : +dict column_types
    DataSourceTestConfig : +create_batch_setup(data) BatchTestSetup

    BatchTestSetup  : +DataSourceTestConfig config
    BatchTestSetup  : +dict data
    BatchTestSetup  : +setup()
    BatchTestSetup  : +teardown()
    BatchTestSetup  : +make_batch() Batch

    DataSourceTestConfig  --> BatchTestSetup: creates
```

## Overview of the main flow
The following shows the rough flow when running tests with `parameterize_batch_for_data_sources` and the `batch_for_datasource` fixture.

Some names have been truncated in the the diagram

An overview of the main pieces:

* test: this is the test you are writing
* parameterize_batch: `parameterize_batch_for_data_sources`
* `batch_for_datasource`: fixture that pulls in the batch for you
* _batch_setup: `_batch_setup_for_datasource`. fixture that handles caching test configs and calling setup
* cached_setups: ensures that identical TestSetups are only setup / torn down once to improve performance

```mermaid
sequenceDiagram
    participant test
    participant parameterize_batch
    participant batch_for_datasource
    participant _batch_setup
    participant cached_setups

    test->>parameterize_batch: [TestConfig], data
    note right of parameterize_batch: pytest.parameterize(label)
    note right of parameterize_batch: makes TestSetups available to _batch_setup
    loop For each TestConfig
        parameterize_batch-->>_batch_setup: pytest.parametrize(TestConfig)
    end

    loop For each TestConfig
        test-->>batch_for_datasource: requests batch
        batch_for_datasource-->>_batch_setup: requests TestSetup
        opt If new TestConfig
            _batch_setup->>_batch_setup: TestConfig.create_batch_setup
            _batch_setup->>cached_setups: cache PostgresBatchTestSetup
        end
        _batch_setup->>cached_setups: get TestSetup
        cached_setups->>_batch_setup: TestSetup
        _batch_setup-->>batch_for_datasource: TestSetup
        batch_for_datasource-->>batch_for_datasource: TestSetup.make_batch()
        batch_for_datasource-->>test: batch
        test->>test: Do test
    end

    test-->>cached_setups: teardown
    loop For each TestSetup
        cached_setups->>cached_setups: TestSetup.teardown()
    end

```
