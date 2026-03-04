from __future__ import annotations

import json
from typing import ClassVar, Type

from great_expectations.data_context.store.store import Store
from great_expectations.data_context.types.resource_identifiers import (
    ValidationMetricIdentifier,
)


class MetricStore(Store):
    """
    A MetricStore stores ValidationMetric information to be used between runs.
    """

    _key_class: ClassVar[Type] = ValidationMetricIdentifier

    def __init__(self, store_backend=None, store_name=None) -> None:
        super().__init__(store_backend=store_backend, store_name=store_name)

    def serialize(self, value):  # type: ignore[explicit-override] # FIXME
        return json.dumps({"value": value})

    def deserialize(self, value):  # type: ignore[explicit-override] # FIXME
        if value:
            return json.loads(value)["value"]
