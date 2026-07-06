# Contributing to Great Expectations

Thank you for your interest in contributing to Great Expectations (GX)! This guide walks through the
contribution journey end to end: proposing a change, claiming an issue, submitting a pull request, and what
happens during review.

For everything related to setting up your local development environment — installing dependencies,
configuring test backends, running the test suite, linting, and IDE setup — see
[DEVELOPMENT.md](./DEVELOPMENT.md). Complete that setup before starting the steps below.

Discuss a code change before you implement it on GitHub — ideally as a comment on the applicable issue if
one exists, or by starting a new thread in
[GitHub Discussions](https://github.com/great-expectations/great_expectations/discussions) if it doesn't.
To request a documentation-only change, or a change that doesn't require local testing, see the
[README](https://github.com/great-expectations/great_expectations/tree/develop/docs) in the `docs`
directory instead of following this guide.

## 1. Propose a change or claim an issue

1. If you want to fix a bug or make a small, well-scoped change, look for an existing issue on the
   [GX Issues board](https://github.com/orgs/great-expectations/projects/2/views/1?pane=info). Issues
   labeled `help wanted` or `good first issue` are good entry points if you're not sure where to start —
   check an issue's labels and existing comments to see whether it's still open for someone to pick up.

2. Before you start work, comment on the issue to let maintainers and other contributors know you're
   picking it up. If someone else has already commented that they're working on it, look for a different
   issue instead of duplicating effort. If you're unsure whether an issue is still available, ask in the
   comment thread rather than assuming.

3. If no existing issue covers your change, open a new issue first and add a comment introducing yourself
   and describing what you plan to do. For a significant feature, open the issue before writing code so the
   approach can be discussed and aligned with the project's direction — this ensures your time and effort
   are well spent.

4. If you can't find an issue that interests you, or you're not sure where to start, ask in the
   [#contributing Slack channel](https://greatexpectationstalk.slack.com/archives/CV828B2UX).

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

## Contributor License Agreement (CLA)

> This section is expected to move to its own dedicated document as GX's contribution governance materials
> expand. Until then, it lives here in full so nothing is lost in the meantime.

*When you contribute code, you affirm that the contribution is your original work and that you license the
work to the project under the project's open source license. Whether or not you state this explicitly, by
submitting any copyrighted material via pull request, email, or other means you agree to license the
material under the project's open source license and warrant that you have the legal authority to do so.*

Please make sure you have signed our Contributor License Agreement (either
[Individual Contributor License Agreement](https://docs.google.com/forms/d/e/1FAIpQLSdA-aWKQ15yBzp8wKcFPpuxIyGwohGU1Hx-6Pa4hfaEbbb3fg/viewform?usp=sf_link)
or
[Software Grant and Corporate Contributor License Agreement](https://docs.google.com/forms/d/e/1FAIpQLSf3RZ_ZRWOdymT8OnTxRh5FeIadfANLWUrhaSHadg_E20zBAQ/viewform?usp=sf_link)).

We are not asking you to assign copyright to us, but to give us the right to distribute your code without
restriction. We ask this of all contributors in order to assure our users of the origin and continuing
existence of the code. You only need to sign the CLA once.
