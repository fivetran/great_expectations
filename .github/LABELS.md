# Labels 

We use GitHub labels to organize issues, surface available work for contributors, and track RFC status.
If you're deciding which label to apply, or wondering why an issue carries the labels it does, this is 
the page to check.

Labels are organized into axes. An issue carries exactly one type label. Status labels track lifecycle
position; most issues carry one, but some compose deliberately — for example, `pinned` sits alongside
`claimed` to exempt an actively claimed issue from staleness handling. The invitation axis adds zero or
more labels on top, subject to the composability rule below. The RFC-status axis applies to GitHub
Discussions, not issues.

## Type axis

Exactly one type label per issue, applied at triage.

| Label | Represents | 
|---|---|
| `bug` | Actual behavior diverges from documented/intended behavior | 
| `feature-request` | New capability or additive API |
| `documentation` | Docs defects and gaps |
| `maintenance` | Internal chores: refactors, CI, dependency hygiene, test infra | 

## Status axis

Tracks an issue's lifecycle position. Most issues carry a single status label, but some combinations are
expected — most notably `pinned` alongside `claimed` (see "Claim staleness" below).

| Label | Represents | Applied by |
|---|---|---|
| `triage` | Awaiting maintainer triage | Automatically, by the issue forms' `labels:` key on submission; removed by a maintainer at triage |
| `needs-info` | Blocked on the reporter (repro, versions, clarification) | Maintainer |
| `ready-for-work` | Triaged, accepted, and defined well enough to start today — the claiming gate | Maintainer |
| `claimed` | Contributor assigned and actively working | The claim-bot workflow (applied on a successful claim, removed on unassignment, including deadline lapse) |
| `pinned` | Exempt from the claim staleness deadline (legitimately long-running work) | Maintainer |
| `blocked` | Blocked on something other than the reporter: an RFC decision, an upstream fix, or an architectural dependency | Maintainer |

### Claim staleness

A claim goes stale after about a week of inactivity. Commenting or otherwise engaging with the issue 
resets that inactivity clock.  If a maintainer applies the `pinned` label, it exempts an issue from this 
staleness handling entirely.

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
