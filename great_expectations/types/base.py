from __future__ import annotations

import copy
import logging
from typing import Any, List

from ruamel.yaml import YAML, yaml_object

from great_expectations.compatibility.typing_extensions import override

logger = logging.getLogger(__name__)
yaml = YAML()


@yaml_object(yaml)
class DotDict(dict):
    """This class provides dot.notation access to dictionary attributes.

    It is also serializable by the ruamel.yaml library used in Great Expectations for managing
    configuration objects.
    """

    def __getattr__(self, item):
        return self.get(item)

    @override
    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    @override
    def __delattr__(self, name: str) -> None:
        del self[name]

    def __dir__(self):  # type: ignore[explicit-override] # FIXME
        return self.keys()

    # Cargo-cultishly copied from: https://github.com/spindlelabs/pyes/commit/d2076b385c38d6d00cebfe0df7b0d1ba8df934bc
    def __deepcopy__(self, memo):
        # noinspection PyArgumentList
        return DotDict([(copy.deepcopy(k, memo), copy.deepcopy(v, memo)) for k, v in self.items()])

    # The following are required to support yaml serialization, since we do not raise
    # AttributeError from __getattr__ in DotDict. We *do* raise that AttributeError when it is possible to know  # noqa: E501 # FIXME CoP
    # a given attribute is not allowed (because it's not in _allowed_keys)
    _yaml_merge: List = []

    @classmethod
    def yaml_anchor(cls):
        # This is required since our dotdict allows *any* access via dotNotation, blocking the normal  # noqa: E501 # FIXME CoP
        # behavior of raising an AttributeError when trying to access a nonexistent function
        return None

    @classmethod
    def to_yaml(cls, representer, node):
        """Use dict representation for DotDict (and subtypes by default)"""
        return representer.represent_dict(node)


class SerializableDotDict(DotDict):
    """
    Analogously to the way "SerializableDictDot" extends "DictDot" to provide JSON serialization, the present class,
    "SerializableDotDict" extends "DotDict" to provide JSON-serializable version of the "DotDict" class as well.
    Since "DotDict" is already YAML-serializable, "SerializableDotDict" is both YAML-serializable and JSON-serializable.
    """  # noqa: E501 # FIXME CoP

    def to_json_dict(self) -> dict:
        raise NotImplementedError
