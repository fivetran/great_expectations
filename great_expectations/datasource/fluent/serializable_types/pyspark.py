from __future__ import annotations

from great_expectations.compatibility.pyspark import pyspark


class SerializableStructType(dict):
    """Custom type implementing pydantic validation."""

    struct_type: pyspark.sql.types.StructType

    def __init__(
        self,
        fields_or_struct_type: pyspark.sql.types.StructType
        | list[pyspark.sql.types.StructField]
        | None,
    ):
        # Store a copy of the instantiated type as an instance variable
        if isinstance(fields_or_struct_type, pyspark.sql.types.StructType):
            self.struct_type = fields_or_struct_type
        else:
            self.struct_type = pyspark.sql.types.StructType(fields=fields_or_struct_type)

        # Store the serialized version in the keys/values of the instance (parent is dict)
        json_value = self.struct_type.jsonValue()
        super().__init__(**json_value)

    @classmethod
    def validate(
        cls,
        fields_or_struct_type: pyspark.sql.types.StructType
        | list[pyspark.sql.types.StructField]
        | None,
    ):
        """If already StructType then return otherwise try to create a StructType."""
        if isinstance(fields_or_struct_type, pyspark.sql.types.StructType):
            return cls(fields_or_struct_type.fields)
        if isinstance(fields_or_struct_type, dict):
            # dict is the serialized jsonValue() form written to great_expectations.yml;
            # StructType.fromJson is its inverse (already used in sparkdf_execution_engine)
            return cls(pyspark.sql.types.StructType.fromJson(fields_or_struct_type))
        if isinstance(fields_or_struct_type, list):
            if not all(
                isinstance(field, pyspark.sql.types.StructField) for field in fields_or_struct_type
            ):
                raise ValueError(  # noqa: TRY003 # FIXME CoP
                    "a spark_schema list must contain pyspark StructField values, got types "
                    f"{[type(field).__name__ for field in fields_or_struct_type]}"
                )
            return cls(fields_or_struct_type)
        if fields_or_struct_type is None:
            return cls(fields_or_struct_type)
        raise ValueError(  # noqa: TRY003 # FIXME CoP
            "spark_schema must be a pyspark StructType, a list of StructField, or None;"
            f" got {type(fields_or_struct_type).__name__}"
        )

    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate
