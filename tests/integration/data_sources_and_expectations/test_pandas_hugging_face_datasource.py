from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

import great_expectations as gx
import great_expectations.expectations as gxe


class FakeDataset:
    def to_pandas(self) -> pd.DataFrame:
        return pd.DataFrame({"id": [1, 2, 3], "text": ["a", "b", "c"]})


@pytest.mark.integration
def test_hugging_face_batch_runs_existing_expectation(monkeypatch: pytest.MonkeyPatch):
    package = SimpleNamespace(config=SimpleNamespace(HF_ENDPOINT="https://huggingface.co"))
    monkeypatch.setattr(
        "great_expectations.datasource.fluent.pandas_hugging_face_datasource.datasets.get_datasets_module",
        lambda: package,
    )
    monkeypatch.setattr(
        "great_expectations.datasource.fluent.pandas_hugging_face_datasource.datasets.load_dataset",
        lambda *args, **kwargs: FakeDataset(),
    )

    context = gx.get_context(mode="ephemeral")
    datasource = context.data_sources.add_pandas_hugging_face(
        name="hf",
        repository="org/data",
    )
    asset = datasource.add_dataset_asset("asset", columns=["id", "text"])
    definition = asset.add_batch_definition_split("train", config=None, split="train")
    batch = definition.get_batch()

    result = batch.validate(gxe.ExpectTableRowCountToEqual(value=3))
    assert result.success
