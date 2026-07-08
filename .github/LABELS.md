# Labels

We use GitHub labels to organize issues, surface available work for contributors, and track RFC status.
If you're deciding which label to apply, or wondering why an issue carries the labels it does, this is
the page to check.

Labels fall into a few groups, and each group answers one question about an issue:

- **Type** — what kind of work is it? Every issue carries exactly one type label.
- **Status** — where is it in its lifecycle? Most issues carry one status label, though a few combine
  deliberately (for example, `pinned` alongside `claimed`).
- **Invitation** — is it open for community contribution, and how welcoming? These sit on top of a status
  and never appear on their own.
- **RFC status** — for design proposals, which live in GitHub Discussions rather than as issues.

If you're here to contribute, start with the next section: it covers the labels that tell you which
issues are open and how claiming works. Everything after it is reference.

## Finding and claiming work

Most contributions start from an issue labeled `ready-for-work`: it has been triaged, accepted, and
scoped well enough to begin today. `ready-for-work` is the gate for claiming — an issue without it isn't
open yet. The two invitation labels point you toward especially good starting points, and once you claim
an issue the claim bot tracks it with `claimed`. For how to claim an issue, see
[`CONTRIBUTING.md`](../CONTRIBUTING.md).

| Label | Represents | Applied by |
|---|---|---|
| `ready-for-work` | Triaged, accepted, and defined well enough to start today — the claiming gate | Maintainer |
| `good first issue` | Ready for work and scoped for a first-time contributor: a clear reproduction and description, a pointer to the relevant module, no architectural judgment required | Maintainer |
| `help wanted` | Ready for work and the maintainer is explicitly not planning to do it themselves — community contribution is the expected path | Maintainer |
| `claimed` | Contributor assigned and actively working | The claim bot (on a successful claim; removed on unassignment, including deadline lapse) |
| `pinned` | Exempt from the claim staleness deadline (legitimately long-running work) | Maintainer |

`good first issue` and `help wanted` are the invitation group: they only ever appear on an issue that
already carries `ready-for-work`, never on their own.

### Claim staleness

A claim goes stale after about a week of inactivity. Commenting or otherwise engaging with the issue
resets that inactivity clock. If a maintainer applies the `pinned` label, it exempts an issue from this
staleness handling entirely.

## Issue types

Exactly one type label per issue, applied by a maintainer at triage.

| Label | Represents |
|---|---|
| `bug` | Actual behavior diverges from documented/intended behavior |
| `feature-request` | New capability or additive API |
| `documentation` | Docs defects and gaps |
| `maintenance` | Internal chores: refactors, CI, dependency hygiene, test infra |

## RFC labels

RFCs (design proposals) live in GitHub Discussions, not issues, and carry their own status labels:

| Label | Represents |
|---|---|
| `rfc:proposed` | Open, within the comment window |
| `rfc:final-comment` | Comment window closed; the maintainer decision-SLA clock is running |
| `rfc:accepted` | Approved |
| `rfc:declined` | Denied, with written rationale |
| `rfc:withdrawn` | Withdrawn by its author |

## Other issue statuses

These statuses track where an issue sits before or outside the claiming flow. You generally won't apply
them yourself, but they explain why an issue may not be available to pick up.

| Label | Represents | Applied by |
|---|---|---|
| `triage` | Awaiting maintainer triage | Automatically, by the issue forms' `labels:` key on submission; removed by a maintainer at triage |
| `needs-info` | Blocked on the reporter (repro, versions, clarification) | Maintainer |
| `blocked` | Blocked on something other than the reporter: an RFC decision, an upstream fix, or an architectural dependency | Maintainer |

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
