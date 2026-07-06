# Label taxonomy

This document is the single source of truth for what each label on this repository means, who applies it,
and when. Other contribution docs (for example, `CONTRIBUTING.md` and the issue forms under
`.github/ISSUE_TEMPLATE/`) link here rather than redefining label meanings themselves. If you're deciding
which label to apply, or wondering why an issue carries the labels it does, this is the page to check.

Labels are organized into axes. An issue carries exactly one type label. Status labels track lifecycle
position; most issues carry one, but some compose deliberately — for example, `pinned` sits alongside
`claimed` to exempt an actively claimed issue from staleness handling. The invitation axis adds zero or
more labels on top, subject to the composability rule below. The RFC-status axis applies to GitHub
Discussions, not issues.

## Type axis

Exactly one type label per issue, applied at triage.

| Label | Represents | Notes |
|---|---|---|
| `bug` | Actual behavior diverges from documented/intended behavior | Existing label, kept |
| `feature-request` | New capability or additive API | Absorbs the older `enhancement`, `feature`, and `expectation-request` labels. A new Expectation that conforms to the existing Expectation interface is a feature request, not an RFC. |
| `documentation` | Docs defects and gaps | Existing label, kept |
| `maintenance` | Internal chores: refactors, CI, dependency hygiene, test infra | Deliberately matches the `[MAINTENANCE]` pull-request title tag |

## Status axis

Tracks an issue's lifecycle position. Most issues carry a single status label, but some combinations are
expected — most notably `pinned` alongside `claimed` (see "Claim staleness" below).

| Label | Represents | Applied by |
|---|---|---|
| `triage` | Awaiting maintainer triage | Automatically, by the issue forms' `labels:` key on submission; removed by a maintainer at triage |
| `needs-info` | Blocked on the reporter (repro, versions, clarification) | Maintainer |
| `ready-for-work` | Triaged, accepted, and defined well enough to start today — the claiming gate | Maintainer |
| `claimed` | Contributor assigned and actively working | The claim-bot workflow (applied on a successful claim, removed on unassignment, including deadline lapse) |
| `pinned` | Exempt from the claim staleness deadline (legitimately long-running work) | Maintainer only |
| `blocked` | Blocked on something other than the reporter: an RFC decision, an upstream fix, or an architectural dependency | Maintainer |

### Claim staleness

A claim goes stale after **~1 week of inactivity on the issue itself** — not one week from the moment of
claiming. Commenting or otherwise engaging with the issue resets that inactivity clock. Because a reminder
comment is posted before the deadline, and that reminder itself counts as activity, the effective
end-to-end window before an unanswered claim lapses is **~10–11 days**, not exactly 7. `pinned` exempts an
issue from this staleness handling entirely.

## Invitation axis

Composable only with `ready-for-work`. These two labels may only appear on an issue that also carries
`ready-for-work`; they are never applied alone.

| Label | Represents |
|---|---|
| `good first issue` | Ready for work and scoped for a first-time contributor: a clear reproduction and description, a pointer to the relevant module, no architectural judgment required |
| `help wanted` | Ready for work and the maintainer is explicitly not planning to do it themselves — community contribution is the expected path |

## RFC-status axis

Applies to GitHub Discussions, not issues.

| Label | Represents |
|---|---|
| `rfc:proposed` | Open, within the comment window |
| `rfc:final-comment` | Comment window closed; the maintainer decision-SLA clock is running |
| `rfc:accepted` | Approved |
| `rfc:declined` | Denied, with written rationale |
| `rfc:withdrawn` | Withdrawn by its author |

## Reserved / bot-owned labels

The following labels are machine-owned. Don't apply them by hand:

- `stale`
- `cla-signed`
- `cla-not-signed`
- `dependencies`
- `python`
- `javascript`
- `github_actions`
- `agent-review-requested`
- `claimed`
- `🔔 reminder-sent` (the claim-bot's reminder marker)

## Retired labels

The following labels were retired (removed from the repository) as part of this taxonomy's introduction
and are no longer valid:

- The team-routing family: `core`, `community`, `devrel`, `dx`, `cloud`, `analytics`
- The `feature:*` family
- The `stack:*` family
- `fluent-datasources`
- `bounty-board`
- `community-supported`
- `not-supported`
- `discussion`
- Vendor one-offs: `azure`, `aws`, `databricks-sql`, `redshift`
- Superseded resolution labels: `wontfix`, `as-designed`, `fix-in-prog`, `pending`, `in-progress`,
  `pr:in_review` (GitHub's native close reasons now cover this)
- `backlog`
- `performance`
