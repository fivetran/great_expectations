# Contributing to Great Expectations

Thank you for your interest in contributing to Great Expectations (GX)! This guide walks through the
contribution journey end to end: proposing a change, claiming an issue, submitting a pull request, and what
happens during review.

For everything related to setting up your local development environment — installing dependencies,
configuring test backends, running the test suite, linting, and IDE setup — see
[DEVELOPMENT.md](./DEVELOPMENT.md). Complete that setup before starting the steps below.

Discuss a code change before you implement it on GitHub — ideally as a comment on the applicable issue if
one exists, or by starting a new thread in
[GitHub Discussions](https://github.com/fivetran/great_expectations/discussions) if it doesn't.
To request a documentation-only change, or a change that doesn't require local testing, see the
[README](https://github.com/fivetran/great_expectations/tree/develop/docs) in the `docs`
directory instead of following this guide.

## 1. Propose a change or claim an issue

1. If you want to fix a bug or make a small, well-scoped change, look for an existing issue on the
   [GX Issues board](https://github.com/orgs/great-expectations/projects/2/views/11?visibleFields=%5B%22Title%22%2C%22Assignees%22%2C%22Linked+pull+requests%22%2C%22Labels%22%5D&sliceBy%5BcolumnId%5D=Labels&sortedBy%5Bdirection%5D=asc&sortedBy%5BcolumnId%5D=Labels). Issues
   labeled `help wanted` or `good first issue` are good entry points if you're not sure where to start.

2. Before you start work, claim the issue so maintainers and other contributors know you're picking it
   up. Issues open for claiming carry the `ready-for-work` label. To claim one, comment `/assign-me` on
   the issue; once the claim succeeds, the bot applies a `claimed` label and assigns you. If an issue
   doesn't carry `ready-for-work`, it isn't open for claiming yet — look for a different issue instead.
   A claim goes stale after about a week without activity on the issue (not a week from when you claimed
   it — commenting or otherwise engaging with the issue keeps your claim active) and becomes reclaimable
   by someone else at that point, except for issues carrying a maintainer-applied `pinned` label, which
   are exempt from this staleness handling.

3. If no existing issue covers your change, open a new issue first and add a comment introducing yourself
   and describing what you plan to do. For a significant feature, open the issue before writing code so the
   approach can be discussed and aligned with the project's direction — this ensures your time and effort
   are well spent.

## 2. Set up your environment and make your change

1. Follow DEVELOPMENT.md's "Fork and clone the repository" and "Set up your development environment"
   sections to get a working checkout, then its "Configure backends for testing" section if your change
   needs a specific backend (for example, PostgreSQL, MySQL, or Spark).

2. Make your change on a branch in your fork.

3. Test your change. See DEVELOPMENT.md's test-code-changes and test-performance sections for how to run the
   unit test suite, test against specific backends, and (if relevant) run performance benchmarks.

## 3. Submit a pull request

1. Push your changes to the remote fork of your repository.

2. Create a pull request (PR) from your fork. See
   [Creating a pull request from a fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork).

3. Add a meaningful title and description. Provide a detailed explanation of what you changed and why. To
   help identify the change, prefix the PR title with `[CONTRIB]`.

4. In the PR description, include a description of any prior discussion or coordination on the feature —
   for example, "Closes #123", a link to a relevant [Discourse](https://discourse.greatexpectations.io/)
   thread or Slack conversation, or a note that no discussion is relevant because the change is small.

5. If this is your first Great Expectations contribution, you'll be prompted to complete the Contributor
   License Agreement (CLA). See [Contributor License Agreement (CLA)](#contributor-license-agreement-cla)
   below for what the CLA requires and how to complete it, then add `@cla-bot check` as a comment on the PR
   once you have.

6. Continuous Integration (CI) doesn't start automatically on your PR — a maintainer needs to review and
   trigger the run first. This usually happens within the next business day, though that isn't guaranteed.
   Once CI runs, wait for the checks to complete and correct any syntax or formatting issues they surface.

## 4. What happens during review

A maintainer reviews your PR, requests changes if needed, and approves and merges it once it's ready.
Depending on your GitHub notification settings, you'll be notified when there are comments on your PR or
when it's successfully merged.

## Requesting comment on larger changes

Some changes benefit from broader discussion before any code is written. An RFC (Request For Comment) is
how that discussion happens in the open.

**An RFC is required for:**

- Breaking changes to a public API
- Adding support for a new data source or execution engine
- Changes to a canonical JSON schema's version
- Cross-cutting architectural decisions that affect multiple subsystems

**An RFC is not required for:**

- Bug fixes
- Additive, non-breaking API changes
- New Expectations that conform to the existing Expectation interface
- Documentation changes
- Performance changes that don't alter behavior

RFCs are posted in the **Request For Comment** category of
[GitHub Discussions](https://github.com/fivetran/great_expectations/discussions). If your idea is
still half-baked or exploratory, start in the **Ideas** category instead — move it to Request For Comment
once you're ready to propose a concrete change.

Maintainers have final authority to approve or deny an RFC. If an RFC is denied, the maintainer who denies
it provides written rationale for the decision.

An RFC's status is tracked with a label: `rfc:proposed`, `rfc:final-comment`, `rfc:accepted`,
`rfc:declined`, or `rfc:withdrawn`. See [.github/LABELS.md](./.github/LABELS.md) for what each label means.

Once posted, an RFC stays open for public comment for a minimum of two weeks. A maintainer may extend the
comment window at their discretion. After the comment window closes, maintainers aim to reach a decision
within 14 days.

## Contributor License Agreement (CLA)

Before your first contribution can be merged, you'll need to sign our Contributor License Agreement. See
[CLA.md](./CLA.md) for what the CLA covers and how to complete it.
