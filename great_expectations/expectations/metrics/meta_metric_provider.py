from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class MetaMetricProvider(type):
    """MetaMetricProvider registers metrics as they are defined."""

    def __new__(cls, clsname, bases, attrs):
        newclass = super().__new__(cls, clsname, bases, attrs)
        # noinspection PyUnresolvedReferences
        newclass._register_metric_functions()
        return newclass
