from functools import cache
from typing import ClassVar, Final, Generic, TypeVar

from typing_extensions import dataclass_transform, get_args

from great_expectations.compatibility.pydantic import BaseModel, ModelMetaclass, StrictStr
from great_expectations.metrics.domain import AbstractClassInstantiationError, Domain
from great_expectations.metrics.metric_results import MetricResult
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


class MissingAttributeError(AttributeError):
    def __init__(self, class_name: str, attribute_name: str) -> None:
        super().__init__(f"`{class_name}` must define `{attribute_name}` attribute.")


class UnregisteredMetricError(ValueError):
    def __init__(self, metric_name: str) -> None:
        super().__init__(f"Metric `{metric_name}` was not found in the registry.")


@dataclass_transform()
class MetaMetric(ModelMetaclass):
    """Metaclass for Metric classes that maintains a registry of all concrete Metric types."""

    _registry: dict[str, type["Metric"]] = {}

    def __new__(cls, name, bases, attrs):
        register_cls = super().__new__(cls, name, bases, attrs)
        # Don't register the base Metric class
        if name != "Metric":
            # ensure a single Domain mixin is defined
            if len(bases) != ALLOWABLE_METRIC_MIXINS + 1 or not any(
                issubclass(base_type, Domain) for base_type in bases
            ):
                raise MixinTypeError(name, "Domain")
            try:
                metric_name = attrs["name"]
            except KeyError:
                raise MissingAttributeError(name, "name")
            MetaMetric._registry[metric_name] = register_cls
        return register_cls

    @classmethod
    def get_registered_metric_class_from_metric_name(cls, metric_name: str) -> type["Metric"]:
        """Returns the registered Metric class for a given metric name."""
        try:
            return cls._registry[metric_name]
        except KeyError:
            raise UnregisteredMetricError(metric_name)


_MetricResult = TypeVar("_MetricResult", bound=MetricResult)


class Metric(Generic[_MetricResult], BaseModel, metaclass=MetaMetric):
    """The abstract base class for defining all metrics.

    A Metric represents a measurable property that can be computed over a specific domain
    of data (e.g., a column, table, or column pair). All concrete metric implementations
    must inherit from this class and specify their domain type as a mixin.

    Examples:
        A metric for a single column max value:

        >>> class ColumnMaxResult(MetricResult[int]): ...
        >>>
        >>> class ColumnMax(Metric[ColumnMaxResult], Column):
        ...     ...

        A metric for a single batch row count value:

        >>> class BatchRowCountResult(MetricResult[int]): ...
        >>>
        >>> class BatchRowCount(Metric[BatchRowCountResult], Batch):
        ...     ...

    Notes:
        - The Metric class cannot be instantiated directly - it must be subclassed.
        - Subclasses must specify a single Domain type as a mixin.
        - Once Metrics are instantiated, they are immutable.

    See Also:
        Domain: The base class for all domain types
        MetricConfiguration: Configuration class for metric computation
    """

    # we wouldn't mind removing this `name` attribute
    # it's currently our only hook into the legacy metrics system
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

    @classmethod
    def get_metric_result_type(cls) -> type[_MetricResult]:
        """Returns the MetricResult type for this Metric."""
        return get_args(getattr(cls, "__orig_bases__", [])[0])[0]

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
