from functools import cache
from typing import ClassVar, Final

from typing_extensions import dataclass_transform

from great_expectations.compatibility.pydantic import BaseModel, ModelMetaclass, StrictStr
from great_expectations.metrics.domain import AbstractClassInstantiationError, Domain
from great_expectations.validator.metric_configuration import (
    MetricConfiguration,
    MetricConfigurationID,
)

ALLOWABLE_METRIC_MIXINS: Final[int] = 1


class MixinTypeError(TypeError):
    def __init__(self, class_name: str, mixin_superclass_name: str) -> None:
        super().__init__(
            f"`{class_name}` must use a single `{mixin_superclass_name}` subclass mixin."
        )


@dataclass_transform()
class MetaMetric(ModelMetaclass):
    def __new__(cls, name, bases, attrs):
        # ensure a single Domain mixin is defined
        if name != "Metric" and (
            len(bases) != ALLOWABLE_METRIC_MIXINS + 1
            or not any(issubclass(base_type, Domain) for base_type in bases)
        ):
            raise MixinTypeError(name, "Domain")
        return super().__new__(cls, name, bases, attrs)


class Metric(BaseModel, metaclass=MetaMetric):
    """The abstract base class for defining all metrics.

    A Metric represents a measurable property that can be computed over a specific domain
    of data (e.g., a column, table, or column pair). All concrete metric implementations
    must inherit from this class and specify their domain type as a mixin.

    Examples:
        A metric for column nullity values computed on each row:

        >>> class ColumnValuesNull(Metric, ColumnValues):
        ...     ...

        A metric for a single table row count value:

        >>> class TableRowCount(Metric, Table):
        ...     ...

    Notes:
        - The Metric class cannot be instantiated directly - it must be subclassed.
        - Subclasses must specify a single Domain type as a mixin.
        - Once Metrics are instantiated, they are immutable.

    See Also:
        Domain: The base class for all domain types
        MetricConfiguration: Configuration class for metric computation
    """

    name: ClassVar[StrictStr]

    class Config:
        arbitrary_types_allowed = True
        frozen = True

    def __new__(cls, *args, **kwargs):
        if cls is Metric:
            raise AbstractClassInstantiationError(cls.__name__)
        return super().__new__(cls)

    @property
    def id(self) -> MetricConfigurationID:
        return self.config.id

    @property
    def config(self) -> MetricConfiguration:
        return Metric._to_config(
            instance_class=self.__class__,
            metric_value_set=frozenset(self.dict().items()),
        )

    @staticmethod
    @cache
    def _to_config(
        instance_class: type["Metric"], metric_value_set: frozenset[tuple]
    ) -> MetricConfiguration:
        """Returns a MetricConfiguration instance for this Metric."""
        metric_domain_kwargs = {}
        metric_value_kwargs = {}
        metric_values = dict(metric_value_set)
        for base_type in instance_class.__bases__:
            if issubclass(base_type, Domain):
                domain_fields = base_type.__fields__
                metric_fields = Metric.__fields__
                value_fields = {
                    field_name: field_info
                    for field_name, field_info in instance_class.__fields__.items()
                    if field_name not in domain_fields and field_name not in metric_fields
                }
                for field_name, field_info in domain_fields.items():
                    metric_domain_kwargs[field_name] = metric_values.get(
                        field_name, field_info.default
                    )
                for field_name, field_info in value_fields.items():
                    metric_value_kwargs[field_name] = metric_values.get(
                        field_name, field_info.default
                    )

        return MetricConfiguration(
            metric_name=instance_class.name,
            metric_domain_kwargs=metric_domain_kwargs,
            metric_value_kwargs=metric_value_kwargs,
        )
