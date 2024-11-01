from __future__ import annotations

import random
import string
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, Dict, Generic, Mapping, Optional, Type, TypeVar, Union

import great_expectations as gx
from great_expectations.compatibility.sqlalchemy import TypeEngine
from great_expectations.data_context.data_context.abstract_data_context import AbstractDataContext
from great_expectations.datasource.fluent.interfaces import Batch

if TYPE_CHECKING:
    import pandas as pd
    import pytest
    from pytest import FixtureRequest

_ColumnTypes = TypeVar("_ColumnTypes")


@dataclass(frozen=True)
class DataSourceTestConfig(ABC, Generic[_ColumnTypes]):
    name: Optional[str] = None
    column_types: Optional[Mapping[str, _ColumnTypes]] = None
    extra_assets: Optional[Mapping[str, Mapping[str, _ColumnTypes]]] = None

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
    ) -> BatchTestSetup:
        """Create a batch setup object for this data source."""

    @property
    def test_id(self) -> str:
        parts: list[Optional[str]] = [self.label, self.name]
        non_null_parts = [p for p in parts if p is not None]

        return "-".join(non_null_parts)


_ConfigT = TypeVar("_ConfigT", bound=DataSourceTestConfig)


class BatchTestSetup(ABC, Generic[_ConfigT]):
    """ABC for classes that set up and tear down batches."""

    def __init__(self, config: _ConfigT, data: pd.DataFrame) -> None:
        self.config = config
        self.data = data

    @abstractmethod
    def make_batch(self) -> Batch: ...

    @abstractmethod
    def setup(self) -> None: ...

    @abstractmethod
    def teardown(self) -> None: ...

    @staticmethod
    def _random_resource_name() -> str:
        return "".join(random.choices(string.ascii_lowercase, k=10))

    @cached_property
    def _context(self) -> AbstractDataContext:
        return gx.get_context(mode="ephemeral")


class SQLBatchTestSetup(BatchTestSetup, ABC, Generic[_ConfigT]):
    @property
    @abstractmethod
    def connection_string(self) -> str:
        """Connection string used to connect to SQL backend."""

    @property
    @abstractmethod
    def schema(self) -> Union[str, None]:
        """Schema -- if any -- to use when connecting to SQL backend."""

    @property
    @abstractmethod
    def inferrable_types_lookup(self) -> Dict[Type, TypeEngine]:
        """Dict of Python type keys mapped to SQL dialect-specific SqlAlchemy types."""
