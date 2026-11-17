import pathlib

import pytest

import great_expectations as gx
import great_expectations.expectations as gxe


@pytest.mark.filesystem
@pytest.mark.parametrize(
    "file_name",
    [
        pytest.param("sales (2024).csv", id="parentheses"),
        pytest.param("a+b.csv", id="plus"),
        pytest.param("data[1].csv", id="brackets"),
    ],
)
def test_add_batch_definition_path_with_regex_metacharacters(
    tmp_path: pathlib.Path, file_name: str
) -> None:
    (tmp_path / file_name).write_text("value\n1\n2\n")
    context = gx.get_context(mode="ephemeral")
    asset = context.data_sources.add_pandas_filesystem(
        name="ds", base_directory=tmp_path
    ).add_csv_asset(name="asset")

    batch = asset.add_batch_definition_path(name="bd", path=file_name).get_batch()

    assert pathlib.Path(batch.batch_spec["path"]).name == file_name
    assert batch.validate(gxe.ExpectTableRowCountToEqual(value=2)).success


@pytest.mark.filesystem
def test_add_batch_definition_path_does_not_match_other_files_via_wildcard(
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "data.csv").write_text("value\n1\n2\n")
    (tmp_path / "data_csv").write_text("value\n1\n")
    context = gx.get_context(mode="ephemeral")
    asset = context.data_sources.add_pandas_filesystem(
        name="ds", base_directory=tmp_path
    ).add_csv_asset(name="asset")

    batch = asset.add_batch_definition_path(name="bd", path="data.csv").get_batch()

    assert pathlib.Path(batch.batch_spec["path"]).name == "data.csv"
    assert batch.validate(gxe.ExpectTableRowCountToEqual(value=2)).success
