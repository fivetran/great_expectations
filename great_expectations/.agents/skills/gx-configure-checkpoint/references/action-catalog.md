# The post-run action catalog

A checkpoint's `actions` list is what fires after `run()` completes: a
notification, a Data Docs rebuild, a webhook. This document covers every
attachable action, its fields, and the mechanics of enabling Data Docs so an
update action has a site to write to.

## Counting the catalog: eight actions, not the base class

`ValidationAction` is the abstract base every action subclasses. Do not
attach it — it has no `run()` implementation of its own and exists only to be
subclassed. `DataDocsAction` is an intermediate base below it — it has
**two** subclasses, not one: `SlackNotificationAction` and
`UpdateDataDocsAction` (verified: `DataDocsAction.__subclasses__()` returns
exactly those two). `DataDocsAction` contributes helper methods for building
and linking a Data Docs site and defines no field of its own (verified:
`DataDocsAction.__fields__` holds only the two inherited from
`ValidationAction`, `type` and `name`). That is why `notify_with` — the
field for linking Data Docs sites in a notification — is declared directly
on `SlackNotificationAction` itself, **and independently again** on
`EmailAction`, a class that does not descend from `DataDocsAction` at all
(its base is `ValidationAction`). Both actions carry it; neither inherits it
from the other or from a shared base. `DataDocsAction` is not attachable
either, for the same reason as `ValidationAction`. Selecting on which classes
carry their own non-`None` `type` literal is what separates the two bases
from the eight things a user can actually attach — verified directly against
the running registry, not assumed from a doc count:

```python
from great_expectations.checkpoint import actions

def closure(cls):
    found = set(cls.__subclasses__())
    for c in list(found):
        found |= closure(c)
    return found

attachable = sorted(
    (c for c in closure(actions.ValidationAction) if c.__fields__["type"].default is not None),
    key=lambda c: c.__name__,
)
print([c.__name__ for c in attachable])  # the eight actions below, and only them
```

Every action instance also needs its own `name` — a string identifying that
action within the checkpoint, separate from its `type`. `type` is fixed per
class; `name` is yours to choose (`name="notify_on_call"`, for example).

## Stability split

Four actions are `@public_api`: stable, documented, safe to build guidance
around without qualification. Four exist, are registered, and deserialize
from a stored checkpoint's config exactly like the public ones — but carry no
public-API stability contract, and were adopted into this skill's guidance
under a recorded case-by-case escalation rather than by default. State that
caveat plainly wherever one of the four appears in your own guidance to a
user: *"this action works today but isn't part of Great Expectations'
public-API stability guarantee, so its interface is more likely to change
between releases than the others."*

| Action | `type` | Stability |
| --- | --- | --- |
| `SlackNotificationAction` | `slack` | `@public_api` |
| `MicrosoftTeamsNotificationAction` | `microsoft` | `@public_api` |
| `EmailAction` | `email` | `@public_api` |
| `UpdateDataDocsAction` | `update_data_docs` | `@public_api` |
| `PagerdutyAlertAction` | `pagerduty` | not public API — caveat above |
| `OpsgenieAlertAction` | `opsgenie` | not public API — caveat above |
| `SNSNotificationAction` | `sns` | not public API — caveat above |
| `APINotificationAction` | `api` | not public API — caveat above |

## Fields, per action

**This split matters, and it does not follow the public/caveat line.** The
three notification actions that take a webhook or address — Slack, Teams,
Email — accept their credential-bearing fields as `Union[ConfigStr, str]`.
Pass a `${ENV_VAR}` template exactly as in `gx-configure-data-source`'s
connection strings and it resolves at use time, the same as everywhere else
in this skill family: environment variables always, plus the project's
uncommitted config-variables file in a file-backed project.

**`PagerdutyAlertAction.api_key`/`routing_key`, `OpsgenieAlertAction.api_key`,
`SNSNotificationAction.sns_topic_arn`, and `APINotificationAction.url` are
plain `str` fields — verified directly against the live models, not
`ConfigStr`.** Great Expectations performs no substitution on them. A
`${ENV_VAR}` template placed in one of these fields is not resolved; it is
stored and used **literally**, character for character, as if it were the
real credential. Verified end to end through an actual save/reload: a Slack
action built with `slack_webhook="${SLACK_WEBHOOK_URL}"` reloads as a
`ConfigStr` that resolves correctly, while a Pagerduty action built with
`api_key="${PD_KEY}"` reloads holding the bare string `'${PD_KEY}'` — the
literal template text, not the secret it names. Two consequences follow, and
both matter more here than anywhere else in this skill family:

- **The template lands verbatim in the persisted checkpoint config**, since
  nothing ever substitutes it. Writing `${ENV_VAR}` into one of these five
  fields does not protect the secret the way it does for a connection string
  or a Slack webhook — it just writes a string that looks like a template and
  behaves like nothing.
- **The action then authenticates with that literal text**, which is never a
  valid credential, so it fails silently at run time rather than at setup —
  the checkpoint runs, the action's `run()` fires, and only the destination
  service's own rejection (an auth failure the checkpoint result does not
  surface) reveals that nothing was actually sent.

**Neither of this skill's usual answers applies to these five fields, and
this skill does not write a credential into any of them.** A
`${ENV_VAR}` template doesn't work — GX never resolves it there, so the
action just fails to authenticate. The only way to make the field
functional is to place the real credential in it, and that credential then
lands in `checkpoints/<name>.json`, a file the project's scaffolded
`.gitignore` does **not** exclude — verified directly: a fresh file-backed
project's `.gitignore` holds exactly one line, `uncommitted/`, and
`checkpoints/` is a tracked sibling directory alongside it, committed by
default like any other project file. That is the opposite of what this
skill's standard secret handling exists to guarantee, so there is no gated
or opt-in version of writing it: **this skill will not place a credential
in one of these five fields, under any circumstance.**

Tell the user plainly: the action they've asked for needs a field Great
Expectations offers no template mechanism for, so this skill can't wire it
without putting the credential in tracked project config — something it
won't do. If they still want the action, they can add it themselves, outside
this skill, and accept that trade-off knowingly. Then build the checkpoint
without it.

Every action below with a `notify_on` field accepts the same six values —
`"all"`, `"success"`, `"failure"`, `"info"`, `"warning"`, `"critical"` —
verified directly against the live models, not just the two or three each
individual docstring happens to mention. Treat the per-action lists below as
covering the default and the common cases, not the full set.

**`SlackNotificationAction`** — `slack`

- Required: **either** `slack_webhook`, **or** both `slack_token` and
  `slack_channel`. A checkpoint config carrying `slack_webhook` alongside
  `slack_token`/`slack_channel` raises at construction time — pick one route
  and use it exclusively.
- Optional: `notify_on` (default `"all"`; full set above), `notify_with`
  (list of Data Docs site names to link in the message; default is all
  sites), `show_failed_expectations` (default `False`).

```python
SlackNotificationAction(
    name="notify_slack",
    slack_webhook="${SLACK_WEBHOOK_URL}",
    notify_on="failure",
)
```

**`MicrosoftTeamsNotificationAction`** — `microsoft`

- Required: `teams_webhook`.
- Optional: `notify_on` (default `"all"`).

**`EmailAction`** — `email`

- Required: `smtp_address`, `smtp_port`, `receiver_emails`.
- Optional: `sender_login`, `sender_password` — both warn-only if absent
  (GX logs that the server must accept unauthenticated mail; it does not
  refuse to construct the action), `sender_alias` (defaults to
  `sender_login`), `use_tls`, `use_ssl`, `notify_on` (default `"all"`),
  `notify_with`.

**`UpdateDataDocsAction`** — `update_data_docs`

- Required: nothing beyond `name`.
- Optional: `site_names` — a list of site names to build. **An empty list
  (the default) means every configured site**, not "no sites" — there is no
  way to request zero sites from this field; omit the action entirely if
  that's the goal.
- See "Enabling Data Docs" below before attaching this to a project that has
  no site yet.

**`PagerdutyAlertAction`** — `pagerduty` (stability caveat above)

- Required: `api_key`, `routing_key` — **plain `str`, not templatable; see
  "Fields, per action" above before asking for either one.**
- Optional: `notify_on` (default `"failure"`), `severity` (`"critical"` /
  `"error"` / `"warning"` / `"info"`, default `"critical"`).

**`OpsgenieAlertAction`** — `opsgenie` (stability caveat above)

- Required: `api_key` — **plain `str`, not templatable; see "Fields, per
  action" above.**
- Optional: `region` (set to `"EU"` for the European region, otherwise leave
  unset), `priority` (`"P1"`–`"P5"`, default `"P3"`), `notify_on` (default
  `"failure"`), `tags`.

**`SNSNotificationAction`** — `sns` (stability caveat above)

- Required: `sns_topic_arn` — **plain `str`, not templatable; see "Fields,
  per action" above.**
- Optional: `sns_message_subject` (defaults to the checkpoint result's name).

**`APINotificationAction`** — `api` (stability caveat above)

- Required: `url` — **plain `str`, not templatable; see "Fields, per action"
  above.** Not a credential itself, but the same no-substitution behavior
  applies to whatever this field holds.
- No optional fields.

## Missing configuration

If the user asks for an action whose required field you don't have a value
for, name the exact field and what it is (a webhook URL, an API key, an SMTP
address), and say how to provide it. For Slack, Teams, and Email, that's the
environment-variable / uncommitted-config-file split used everywhere else in
this skill family. **For the five plain-`str` fields covered above, there is
no way to provide it that this skill will use** — Great Expectations has no
secret-safe mechanism for those fields, per "Fields, per action" above, so
the action is left off the checkpoint rather than wired with a credential
this skill won't write. Do not attach any action with a placeholder value
and do not guess a plausible one; leave it out of the checkpoint's action
list until it can be configured safely.

## Enabling Data Docs

`UpdateDataDocsAction` needs a Data Docs site to write to. Check
`context.config.data_docs_sites` before attaching it — three states follow:

**A site already exists.** File-backed projects scaffold a default
`local_site` automatically; nothing further to do. Attach the action.

**An ephemeral session.** In-memory sessions carry a working `local_site`
too, pointed at a directory that only lives for the process's lifetime —
verified: `context.config.data_docs_sites` on a bare `gx.get_context(mode="ephemeral")`
already holds a `local_site` entry whose `store_backend.base_directory` is a
freshly created temp directory, and a checkpoint carrying the action builds
real HTML there. Attach the action; it works. But announce the output as
throwaway when you report it — say plainly that the site lives in a
temporary directory that disappears with the process, and that if durable
Data Docs matter, write-out (`write-out.md`) is what makes them
survive.

**`data_docs_sites` is explicitly `null` in a file project's
`great_expectations.yml`.** This is a trap, not a normal "no site configured"
state: every one of the four public site-CRUD methods
(`add_data_docs_site`, `list_data_docs_sites`, `update_data_docs_site`,
`delete_data_docs_site`) **silently no-ops** against it — no exception, no
log line, no change to the yml. Verified directly: calling
`add_data_docs_site(...)` against a context loaded with `data_docs_sites:
null` returns normally, and the yml still reads `null` afterward. Checking
only "did the call raise" will tell you it worked when it did nothing.

<!-- consent-gate: config-file -->
The state is recoverable. **This requires editing the user's
`great_expectations.yml`, so ask before doing it — the consent to make that
edit is not implied by the request to attach a Data Docs action.** State
plainly what you found (`data_docs_sites` is set to `null`, which silently
blocks every site-management call) and what fixing it involves, then wait for
a yes before running any of the three steps. If the user declines, state the
same fix as the path forward and continue building the checkpoint without the
Data Docs action.

With consent, the fix is a three-step sequence, each step verified in order —
skipping the reload in the middle leaves you editing an in-memory copy of a
context whose live object still has `null` cached:

```python
import yaml
from pathlib import Path
import great_expectations as gx

# 1. Change `data_docs_sites: null` to `data_docs_sites: {}` in the yml.
#    An empty mapping is a real, different value from null -- it's what lets
#    the public factory add a site into it a moment later.
yml_path = Path(context.root_directory) / "great_expectations.yml"
raw = yaml.safe_load(yml_path.read_text())
raw["data_docs_sites"] = {}
yml_path.write_text(yaml.dump(raw, sort_keys=False))

# 2. Reload through a fresh file-mode context with an explicit, absolute
#    project root -- the in-memory `context` object still has `null` cached
#    and won't pick up the yml edit on its own. This is the same project
#    already opened at preflight, not a new directory to ask the user about --
#    only the yml edit above needed their consent.
context = gx.get_context(mode="file", project_root_dir="<the project root established at preflight>")

# 3. Add the default site through the public factory. Only now does this
#    call actually do something -- the no-op trap above is gone because
#    data_docs_sites is {} rather than null.
context.add_data_docs_site(
    site_name="local_site",
    site_config={
        "class_name": "SiteBuilder",
        "store_backend": {
            "class_name": "TupleFilesystemStoreBackend",
            "base_directory": "uncommitted/data_docs/local_site/",
        },
        "site_index_builder": {"class_name": "DefaultSiteIndexBuilder"},
    },
)
```

Verified end to end: after these three steps, `data_docs_sites` in the yml
holds the new site, and a checkpoint carrying `UpdateDataDocsAction` produces
a real `index.html` under `uncommitted/data_docs/local_site/` on its next
run. There is an in-session shortcut — assigning
`context.config.data_docs_sites = {}` directly before calling the public
factory, skipping the reload — that also works, but it mutates configuration
state that isn't part of the public API. Don't offer it; the three-step
version above uses only public surface.
