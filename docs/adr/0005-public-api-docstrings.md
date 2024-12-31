# 5. Docstrings for public API functions/classes 

Date: 2024-12-19

## Status

Accepted

## Context

By marking an object as part of the public API, it automatically renders in our docs site. In order to provide a clear and informative experience for our end users, we should make sure we always include docstrings for public functions/classes. These docstrings should adhere to a consistent format such that they can be rendered in the same manner by our public API infrastructure. 

## Decision

All objects decorated with `@public_api` will have docstrings. In order to be considered public, they must meet this criteria.

## Consequences

Marginal increase in developer burden but worthwhile due to a higher level of thought and care around what actually gets marked and rendered as part of our public API.
