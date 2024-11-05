# Expectation JSON Schemas

## Specification
Expectation JSON schemas should conform to the [JsonSchema7 interface](https://jsonforms.io/api/core/interfaces/jsonschema7). We ensure this by validating each schema using the python [jsonschema](https://python-jsonschema.readthedocs.io/en/stable/) library (e.g. using `Draft7Validator.check_schema()`).

## Metadata Property
Properties on the Expectation schemas represent class instance variable definitions except for one special property: `metadata`

The `metadata` property is itself an `object` containing many `properties`. The `metadata` `properties` are all defined by a `const` which does not change from one Expectation instance to another.
