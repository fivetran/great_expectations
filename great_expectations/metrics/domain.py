from typing import Annotated, Optional

from great_expectations.compatibility.pydantic import BaseModel, Field, StrictStr
from great_expectations.expectations.model_field_types import ConditionParser

NonEmptyString = Annotated[StrictStr, Field(min_length=1)]


class AbstractClassInstantiationError(TypeError):
    def __init__(self, class_name: str) -> None:
        super().__init__(f"Cannot instantiate abstract class `{class_name}`.")


class Domain(BaseModel):
    """The abstract base class for defining all types of domains over which metrics are computed."""

    batch_id: NonEmptyString

    def __new__(cls, *args, **kwargs):
        if cls is Domain:
            raise AbstractClassInstantiationError(cls.__name__)
        return super().__new__(cls)


class Values(Domain):
    """The abstract base class for metric domain types that compute row-level calculations."""

    row_condition: Optional[StrictStr] = None

    def __new__(cls, *args, **kwargs):
        if cls is Values:
            raise AbstractClassInstantiationError(cls.__name__)
        return super().__new__(cls)


class ColumnValues(Values):
    """A domain type for metrics that compute row-level calculations on a single column.

    The ColumnValues domain type is used to define metrics that evaluate conditions or compute
    values for each row in a single column. This class is intended to be used as a mixin
    with the Metric class when defining a new Metric.

    Attributes:
        batch_id (str): Unique identifier for the batch being processed.
        column (str): Name of the column to compute metrics on.
        row_condition (Optional[str]): A condition that can be used to filter rows.
                                       See: https://docs.greatexpectations.io/docs/core/customize_expectations/expectation_conditions/#create-an-expectation-condition

    Examples:
        A metric with a ColumnValues domain for column nullity values computed on each row:

        >>> class Null(Metric, ColumnValues):
        ...     ...

    See Also:
        Metric: The abstract base class for defining all metrics
    """

    column: NonEmptyString


class Batch(Domain):
    """A domain type for metrics that compute over an entire batch.

    The Batch domain type is used to define metrics that evaluate conditions or compute
    values for an entire table. This class is intended to be used as a mixin
    with the Metric class when defining a new Metric.
    """

    row_condition: Optional[StrictStr] = None
    condition_parser: Optional[ConditionParser] = None
