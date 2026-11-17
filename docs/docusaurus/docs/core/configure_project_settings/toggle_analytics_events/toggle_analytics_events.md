---
title: Analytics events
description: GX Core does not collect or send analytics events.
hide_feedback_survey: false
hide_title: false
hide_table_of_contents: true
---

GX Core does not collect or send analytics events. Usage analytics were removed from the library in version 1.7.0, and the library no longer installs the `posthog` dependency. Nothing in GX Core reports how, where, or by whom it is used.

## Existing analytics settings

The `analytics_enabled` key in `great_expectations.yml`, the `context.variables.analytics_enabled` Data Context variable, the `context.enable_analytics()` method, the `user_agent_str` argument to `gx.get_context()`, and the `GX_ANALYTICS_ENABLED` environment variable are still accepted so that existing configuration files and code keep working. None of them has any effect, and you can remove them. The Python method, variable, and argument emit a `DeprecationWarning` when used, and will be removed in a future major version of GX.

## Earlier versions

GX Core 1.0 through 1.6 sent analytics events by default. If you use one of those versions, set the environment variable `GX_ANALYTICS_ENABLED=False` or the Data Context variable `analytics_enabled: false` to turn them off, or upgrade to GX Core 1.7.0 or later.
