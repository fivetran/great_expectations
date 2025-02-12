from typing import ClassVar, Final

from typing_extensions import dataclass_transform

from great_expectations.compatibility.pydantic import BaseModel, ModelMetaclass, root_validator
from great_expectations.metrics.domain import AbstractClassInstantiationError, Domain
from great_expectations.metrics.registry import DOMAIN_NAMES, METRIC_REGISTRY
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


class UnregisteredMetricTypeError(TypeError):
    def __init__(self, class_name: str, domain_class: type[Domain]) -> None:
        super().__init__(
            f"Metric `{class_name.lower()}` was not mapped to "
            f"domain `{domain_class}`, in the metric registry."
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
        # ensure metric is registered
        for base_type in bases:
            if issubclass(base_type, Domain):
                try:
                    registered_metrics_for_domain = METRIC_REGISTRY[DOMAIN_NAMES[base_type]]
                except KeyError:
                    raise UnregisteredMetricTypeError(name, base_type)
                if name.lower() not in registered_metrics_for_domain:
                    raise UnregisteredMetricTypeError(name, base_type)
        return super().__new__(cls, name, bases, attrs)


class Metric(BaseModel, metaclass=MetaMetric):
    """The abstract base class for defining all metrics.

    A Metric represents a measurable property that can be computed over a specific domain
    of data (e.g., a column, table, or column pair). All concrete metric implementations
    must inherit from this class and specify their domain type as a mixin.

    Examples:
        A metric for column nullity values computed on each row:

        >>> class Null(Metric, ColumnMap):
        ...     ...

        A metric for a single table row count value:

        >>> class RowCount(Metric, Table):
        ...     ...

    Notes:
        - The Metric class cannot be instantiated directly - it must be subclassed.
        - Subclasses must specify a Domain type as a mixin.
        - The subclass name and specified Domain type must be registered in the METRIC_REGISTRY.
        - The MetaMetric metaclass enforces these constraints at class creation time.

    See Also:
        Domain: The base class for all domain types
        MetricConfiguration: Configuration class for metric computation
    """

    name: ClassVar[str]
    config: MetricConfiguration

    class Config:
        arbitrary_types_allowed = True
        frozen = True

    def __new__(cls, *args, **kwargs):
        if cls is Metric:
            raise AbstractClassInstantiationError(cls.__name__)
        return super().__new__(cls)

    @root_validator(pre=True)
    @classmethod
    def _set_computed_fields(cls, values) -> dict:
        if "name" not in values or not values["name"]:
            values["name"] = cls._get_metric_name()
        if "config" not in values or values["config"] is None:
            values["config"] = cls._to_config(values)
        return values

    @property
    def id(self) -> MetricConfigurationID:
        return self.config.id

    @classmethod
    def _get_metric_name(cls) -> str:
        """The name of the metric as it exists in the registry."""
        for base_type in cls.__bases__:
            if issubclass(base_type, Domain):
                metric_class_name = str(cls.__name__)
                try:
                    domain_name = DOMAIN_NAMES[base_type]
                except KeyError:
                    # this should never be reached
                    # that the metric is registered should have been confirmed in MetaMetric.__new__
                    raise UnregisteredMetricTypeError(metric_class_name, base_type)
                return ".".join([domain_name, metric_class_name.lower()])

        # this should never be reached
        # that a Domain exists in __bases__ should have been confirmed in MetaMetric.__new__
        raise MixinTypeError(cls.__name__, "Domain")

    @classmethod
    def _to_config(cls, model_values: dict) -> MetricConfiguration:
        """Returns a MetricConfiguration instance for this Metric."""
        metric_domain_kwargs = {}
        metric_value_kwargs = {}
        for base_type in cls.__bases__:
            if issubclass(base_type, Domain):
                domain_fields = base_type.__fields__
                metric_fields = Metric.__fields__
                value_fields = {
                    field_name: field_info
                    for field_name, field_info in cls.__fields__.items()
                    if field_name not in domain_fields and field_name not in metric_fields
                }
                for field_name, field_info in domain_fields.items():
                    metric_domain_kwargs[field_name] = model_values.get(
                        field_name, field_info.default
                    )
                for field_name, field_info in value_fields.items():
                    metric_value_kwargs[field_name] = model_values.get(
                        field_name, field_info.default
                    )

        return MetricConfiguration(
            metric_name=model_values["name"],
            metric_domain_kwargs=metric_domain_kwargs,
            metric_value_kwargs=metric_value_kwargs,
        )
