from __future__ import annotations

import logging
import pathlib
from collections import defaultdict
from pprint import pformat as pf
from typing import TYPE_CHECKING

import pytest

from great_expectations.core.yaml_handler import YAMLHandler

if TYPE_CHECKING:
    from great_expectations.data_context import FileDataContext

yaml = YAMLHandler()

LOGGER = logging.getLogger(__name__)


@pytest.fixture
def taxi_data_samples_dir() -> pathlib.Path:
    return (
        pathlib.Path(__file__).parent.parent.parent / "test_sets" / "taxi_yellow_tripdata_samples"
    ).resolve(strict=True)


@pytest.mark.filesystem
def test_add_fluent_datasource_are_persisted_without_duplicates(
    empty_file_context: FileDataContext,
    db_file: pathlib.Path,
):
    context = empty_file_context
    datasource_name = "save_ds_test"

    context.data_sources.add_sqlite(name=datasource_name, connection_string=f"sqlite:///{db_file}")

    yaml_path = pathlib.Path(context.root_directory, context.GX_YML)
    assert yaml_path.exists()

    yaml_dict: dict = yaml.load(yaml_path.read_text())
    print(pf(yaml_dict, depth=2))
    assert datasource_name in yaml_dict["fluent_datasources"]


@pytest.mark.filesystem
def test_assets_are_persisted_on_creation_and_removed_on_deletion(
    empty_file_context: FileDataContext,
    db_file: pathlib.Path,
):
    context = empty_file_context

    # ensure empty initial state
    yaml_path = pathlib.Path(context.root_directory, context.GX_YML)
    assert yaml_path.exists()
    assert not yaml.load(yaml_path.read_text()).get("fluent_datasources")

    datasource_name = "my_datasource"
    asset_name = "my_asset"

    context.data_sources.add_sqlite(
        name=datasource_name, connection_string=f"sqlite:///{db_file}"
    ).add_query_asset(asset_name, query='SELECT name FROM sqlite_master WHERE type = "table"')

    fds_after_add: dict = yaml.load(yaml_path.read_text())["fluent_datasources"]  # type: ignore[assignment] # json union
    assert asset_name in fds_after_add[datasource_name]["assets"]

    context.fluent_datasources[datasource_name].delete_asset(asset_name)

    fds_after_delete: dict = yaml.load(yaml_path.read_text())["fluent_datasources"]  # type: ignore[assignment] # json union
    assert asset_name not in fds_after_delete[datasource_name].get("assets", {})


# This test is parameterized by the fixture `empty_contexts`, which now resolves to a
# filesystem context only (the GX Cloud branch has been shut down).
def test_context_add_or_update_datasource(
    unset_gx_env_variables: None,
    empty_contexts: FileDataContext,
    # db_file: pathlib.Path, TODO: sqlite deser broken
    taxi_data_samples_dir: pathlib.Path,
):
    context = empty_contexts

    context.data_sources.add_pandas_filesystem(
        name="save_ds_test", base_directory=taxi_data_samples_dir
    ).add_csv_asset(
        name="my_asset",
    )

    # add_or_update should be idempotent
    context.data_sources.add_or_update_pandas_filesystem(
        name="save_ds_test", base_directory=taxi_data_samples_dir
    )


# This test is parameterized by the fixture `empty_contexts`, which now resolves to a
# filesystem context only (the GX Cloud branch has been shut down).
def test_context_add_and_then_update_datasource(
    unset_gx_env_variables: None,
    empty_contexts: FileDataContext,
    taxi_data_samples_dir: pathlib.Path,
):
    context = empty_contexts

    datasource1 = context.data_sources.add_pandas_filesystem(
        name="update_ds_test", base_directory=taxi_data_samples_dir
    )

    # add_or_update should be idempotent
    datasource2 = context.data_sources.update_pandas_filesystem(
        name="update_ds_test", base_directory=taxi_data_samples_dir
    )

    assert datasource1 == datasource2

    # modify a field
    datasource2.base_directory = pathlib.Path(__file__)
    datasource3 = context.data_sources.update_pandas_filesystem(datasource2)

    assert datasource1 != datasource3
    assert datasource2 == datasource3


# This test is parameterized by the fixture `empty_contexts`, which now resolves to a
# filesystem context only (the GX Cloud branch has been shut down).
def test_update_non_existant_datasource(
    unset_gx_env_variables: None,
    empty_contexts: FileDataContext,
    taxi_data_samples_dir: pathlib.Path,
):
    context = empty_contexts

    with pytest.raises(ValueError, match="I_DONT_EXIST"):
        context.data_sources.update_pandas_filesystem(
            name="I_DONT_EXIST", base_directory=taxi_data_samples_dir
        )


@pytest.mark.filesystem
def test_data_connectors_are_built_on_config_load(
    cloud_storage_get_client_doubles,
    seeded_file_context: FileDataContext,
):
    """
    Ensure that all Datasources that require data_connectors have their data_connectors
    created when loaded from config.
    """
    context = seeded_file_context
    dc_datasources: dict[str, list[str]] = defaultdict(list)

    assert context.fluent_datasources
    for datasource in context.fluent_datasources.values():
        if datasource.data_connector_type:
            print(f"class: {datasource.__class__.__name__}")
            print(f"type: {datasource.type}")
            print(f"data_connector: {datasource.data_connector_type.__name__}")
            print(f"name: {datasource.name}", end="\n\n")

            dc_datasources[datasource.type].append(datasource.name)

            for asset in datasource.assets:
                assert isinstance(asset._data_connector, datasource.data_connector_type)
            print()

    print(f"Datasources with DataConnectors\n{pf(dict(dc_datasources))}")
    assert dc_datasources


if __name__ == "__main__":
    pytest.main([__file__, "-vv"])
