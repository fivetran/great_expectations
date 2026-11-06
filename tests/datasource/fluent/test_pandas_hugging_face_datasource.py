from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

import great_expectations as gx
from great_expectations.datasource.fluent.pandas_hugging_face_datasource import (
    HuggingFaceDatasourceError,
    PandasHuggingFaceDatasource,
)


class FakeDataset:
    def __init__(self, dataframe: pd.DataFrame):
        self.dataframe = dataframe

    def to_pandas(self) -> pd.DataFrame:
        return self.dataframe


@pytest.fixture
def source() -> PandasHuggingFaceDatasource:
    context = gx.get_context(mode="ephemeral")
    return context.data_sources.add_pandas_hugging_face(
        name="hf", repository="org/data", token="synthetic-token"
    )


@pytest.fixture
def fake_hub(monkeypatch: pytest.MonkeyPatch):
    calls = []
    package = SimpleNamespace(
        config=SimpleNamespace(HF_ENDPOINT="https://huggingface.co"),
        concatenate_datasets=lambda datasets: FakeDataset(
            pd.concat([dataset.dataframe for dataset in datasets], ignore_index=True)
        ),
    )

    def load_dataset(repository: str, **kwargs):
        calls.append((repository, kwargs.copy()))
        if kwargs.get("split") is None:
            return {
                "train": FakeDataset(pd.DataFrame({"id": [1], "text": ["a"]})),
                "test": FakeDataset(pd.DataFrame({"id": [2], "text": ["b"]})),
            }
        return FakeDataset(pd.DataFrame({"id": [1, 2], "text": ["a", "b"]}))

    monkeypatch.setattr(
        "great_expectations.datasource.fluent.pandas_hugging_face_datasource.datasets.get_datasets_module",
        lambda: package,
    )
    monkeypatch.setattr(
        "great_expectations.datasource.fluent.pandas_hugging_face_datasource.datasets.load_dataset",
        load_dataset,
    )
    return calls


@pytest.mark.unit
def test_batch_materializes_selected_columns_and_revision(source, fake_hub):
    asset = source.add_dataset_asset("asset", columns=["text"])
    definition = asset.add_batch_definition_split("train", config="default", split="train")

    batch = definition.get_batch(batch_parameters={"revision": "abc123"})

    assert batch.head().data.equals(pd.DataFrame({"text": ["a", "b"]}))
    assert batch.metadata["revision"] == "abc123"
    assert fake_hub[0][0] == "org/data"
    assert fake_hub[0][1]["revision"] == "abc123"
    assert fake_hub[0][1]["name"] == "default"
    assert fake_hub[0][1]["split"] == "train"


@pytest.mark.unit
def test_missing_column_has_actionable_error(source, fake_hub):
    asset = source.add_dataset_asset("asset", columns=["missing"])
    definition = asset.add_batch_definition_split("train", config=None, split="train")

    with pytest.raises(HuggingFaceDatasourceError, match="Requested Hugging Face column"):
        definition.get_batch()


@pytest.mark.unit
def test_nested_feature_values_are_rejected(source, monkeypatch):
    monkeypatch.setattr(
        "great_expectations.datasource.fluent.pandas_hugging_face_datasource.datasets.get_datasets_module",
        lambda: SimpleNamespace(config=SimpleNamespace(HF_ENDPOINT="https://huggingface.co")),
    )
    monkeypatch.setattr(
        "great_expectations.datasource.fluent.pandas_hugging_face_datasource.datasets.load_dataset",
        lambda *args, **kwargs: FakeDataset(pd.DataFrame({"nested": [[1, 2]]})),
    )
    asset = source.add_dataset_asset("asset")
    definition = asset.add_batch_definition_split("train", config=None, split="train")

    with pytest.raises(HuggingFaceDatasourceError, match="nested or non-scalar"):
        definition.get_batch()


@pytest.mark.unit
def test_whole_configuration_combines_splits(source, fake_hub):
    asset = source.add_dataset_asset("asset")
    definition = asset.add_batch_definition_whole_config("all", config="default")

    definition.get_batch()

    assert fake_hub[0][1]["split"] is None


@pytest.mark.unit
def test_revision_is_the_only_batch_parameter(source):
    asset = source.add_dataset_asset("asset")
    definition = asset.add_batch_definition_split("train", config=None, split="train")

    with pytest.raises(ValueError, match="Only 'revision'"):
        definition.build_batch_request({"split": "test"})


@pytest.mark.unit
def test_missing_optional_dependency_has_install_hint(source, monkeypatch):
    monkeypatch.setattr(
        "great_expectations.datasource.fluent.pandas_hugging_face_datasource.datasets.get_datasets_module",
        lambda: None,
    )
    monkeypatch.setattr(
        "great_expectations.datasource.fluent.pandas_hugging_face_datasource.datasets.load_dataset",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            ModuleNotFoundError(
                "Hugging Face Datasets support requires optional 'datasets' package"
            )
        ),
    )

    with pytest.raises(ModuleNotFoundError, match="optional 'datasets' package"):
        source._load_dataset(config=None, split="train", whole_config=False, revision=None)


@pytest.mark.unit
def test_token_is_passed_to_hub_loader(fake_hub):
    context = gx.get_context(mode="ephemeral")
    source = context.data_sources.add_pandas_hugging_face(
        name="hf", repository="org/data", token="resolved-token"
    )
    asset = source.add_dataset_asset("asset")
    definition = asset.add_batch_definition_split("train", config=None, split="train")

    definition.get_batch()

    assert fake_hub[0][1]["token"] == "resolved-token"


@pytest.mark.unit
def test_hub_failure_does_not_expose_token(monkeypatch: pytest.MonkeyPatch):
    context = gx.get_context(mode="ephemeral")
    source = context.data_sources.add_pandas_hugging_face(
        name="hf", repository="org/data", token="secret-token"
    )
    monkeypatch.setattr(
        "great_expectations.datasource.fluent.pandas_hugging_face_datasource.datasets.get_datasets_module",
        lambda: SimpleNamespace(config=SimpleNamespace(HF_ENDPOINT="https://huggingface.co")),
    )
    monkeypatch.setattr(
        "great_expectations.datasource.fluent.pandas_hugging_face_datasource.datasets.load_dataset",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("secret-token rejected")),
    )
    with pytest.raises(HuggingFaceDatasourceError) as exc_info:
        source._load_dataset(config=None, split="train", whole_config=False, revision=None)

    assert "secret-token" not in str(exc_info.value)
    assert exc_info.value.__cause__ is None


@pytest.mark.unit
def test_datasource_asset_and_batch_definition_round_trip():
    context = gx.get_context(mode="ephemeral")
    source = context.data_sources.add_pandas_hugging_face(
        name="hf", repository="org/data", token="secret-token"
    )
    asset = source.add_dataset_asset("asset", columns=["text"])
    asset.add_batch_definition_split("train", config="default", split="train")

    serialized = source.json(exclude_unset=True)
    restored = PandasHuggingFaceDatasource.parse_raw(serialized)

    assert "secret-token" not in serialized
    assert restored.repository == "org/data"
    assert restored.assets[0].columns == ["text"]
    assert restored.assets[0].batch_definitions[0].config == "default"
