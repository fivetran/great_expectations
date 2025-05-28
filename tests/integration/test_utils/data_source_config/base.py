from __future__ import annotations

import random
import string
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING, Generator, Generic, Hashable, Mapping, Optional, TypeVar
from uuid import UUID, uuid4

import pandas as pd

from great_expectations.compatibility.typing_extensions import override
from great_expectations.data_context.data_context.abstract_data_context import AbstractDataContext
from great_expectations.datasource.fluent.interfaces import Batch, DataAsset

if TYPE_CHECKING:
    import pytest
    from pytest import FixtureRequest


_ColumnTypes = TypeVar("_ColumnTypes")


@dataclass(frozen=True)
class DataSourceTestConfig(ABC, Generic[_ColumnTypes]):
    name: Optional[str] = None
    table_name: Optional[str] = None  # Overrides random table name generation
    column_types: Optional[Mapping[str, _ColumnTypes]] = None
    extra_column_types: Mapping[str, Mapping[str, _ColumnTypes]] = field(default_factory=dict)

    @property
    @abstractmethod
    def label(self) -> str:
        """Label that will show up in test name."""
        ...

    @property
    @abstractmethod
    def pytest_mark(self) -> pytest.MarkDecorator:
        """Mark for pytest"""
        ...

    @abstractmethod
    def create_batch_setup(
        self,
        request: FixtureRequest,
        data: pd.DataFrame,
        extra_data: Mapping[str, pd.DataFrame],
        context: AbstractDataContext,
    ) -> BatchTestSetup:
        """Create a batch setup object for this data source."""

    @property
    def test_id(self) -> str:
        parts: list[Optional[str]] = [self.label, self.name]
        non_null_parts = [p for p in parts if p is not None]

        return "-".join(non_null_parts)

    @override
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, DataSourceTestConfig):
            return False
        return all(
            [
                super().__eq__(value),
                self.label == value.label,
                self.pytest_mark == value.pytest_mark,
            ]
        )

    @override
    def __hash__(self) -> int:
        hashable_col_types = dict_to_tuple(self.column_types) if self.column_types else None
        hashable_extra_col_types = dict_to_tuple(
            {k: dict_to_tuple(self.extra_column_types[k]) for k in sorted(self.extra_column_types)}
        )
        return hash(
            (
                self.__class__.name,
                self.test_id,
                hashable_col_types,
                hashable_extra_col_types,
            )
        )


_ConfigT = TypeVar("_ConfigT", bound=DataSourceTestConfig)
_AssetT = TypeVar("_AssetT", bound=DataAsset)


class BatchTestSetup(ABC, Generic[_ConfigT, _AssetT]):
    """ABC for classes that set up and tear down batches."""

    def __init__(self, config: _ConfigT, data: pd.DataFrame, context: AbstractDataContext) -> None:
        self.config = config
        self.data = data
        self.context = context

    @abstractmethod
    def make_asset(self) -> _AssetT: ...

    @abstractmethod
    def make_batch(self) -> Batch: ...

    @abstractmethod
    def setup(self) -> None: ...

    @abstractmethod
    def teardown(self) -> None: ...

    @contextmanager
    def data_context_test_context(self) -> Generator[AbstractDataContext, None, None]:
        """Receive a DataContext and ensure proper setup and teardown regardless of errors."""
        try:
            self.setup()
            yield self.context
        finally:
            self.teardown()

    @contextmanager
    def asset_test_context(self) -> Generator[_AssetT, None, None]:
        """Receive an Asset and ensure proper setup and teardown regardless of errors."""
        try:
            self.setup()
            yield self.make_asset()
        finally:
            self.teardown()

    @contextmanager
    def batch_test_context(self) -> Generator[Batch, None, None]:
        """Receive a Batch and ensure proper setup and teardown regardless of errors."""
        try:
            self.setup()
            yield self.make_batch()
        finally:
            self.teardown()

    @staticmethod
    def _random_resource_name() -> str:
        return "".join(random.choices(string.ascii_lowercase, k=10))

    @cached_property
    def id(self) -> UUID:
        return uuid4()


def dict_to_tuple(d: Mapping[str, Hashable]) -> tuple[tuple[str, Hashable], ...]:
    return tuple((key, d[key]) for key in sorted(d))


def hash_data_frame(df: pd.DataFrame) -> int:
    return hash(tuple(pd.util.hash_pandas_object(df).array))
