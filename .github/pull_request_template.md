

<!--
Describe your change above.

Some changes need an RFC (Request For Comment) agreed before implementation, so that the
design discussion happens before anyone invests in code. An RFC is required for:

  - breaking changes to a public API
  - adding support for a new data source or execution engine
  - changes to a canonical JSON schema's version
  - cross-cutting architectural decisions that affect multiple subsystems

An RFC is not required for bug fixes, additive non-breaking API changes, new Expectations that
conform to the existing Expectation interface, documentation changes, or performance changes
that don't alter behavior.

If your change needs an RFC, open one in the Request For Comment discussion category first, then
add a line to the description above linking it. Full criteria and process:
https://github.com/fivetran/great_expectations/blob/develop/CONTRIBUTING.md#requesting-comment-on-larger-changes

For changes that add a new data source or execution engine, an automated check looks for one of
these two lines in the description above, written exactly in this form:

  RFC: <link to the accepted discussion>
  No RFC needed: <reason this isn't new backend support>

Either answer satisfies the check — it only asks that the question was answered. Linking the RFC
in prose won't be recognized, so use the line form.
-->

- [ ] Description of PR changes above includes a link to [an existing GitHub issue](https://github.com/fivetran/great_expectations/issues)
- [ ] PR title is prefixed with one of: [BUGFIX], [FEATURE], [DOCS], [MAINTENANCE], [CONTRIB], [MINORBUMP]
- [ ] This change is below the [RFC threshold](https://github.com/fivetran/great_expectations/blob/develop/CONTRIBUTING.md#requesting-comment-on-larger-changes), or the description above carries an `RFC: <link>` line pointing at an accepted RFC
- [ ] Code is linted - run `invoke lint` (uses `ruff format` + `ruff check`)
- [ ] Appropriate tests and docs have been updated
- [ ] For any behavioral change to a data source, validation mechanic, or Expectation, at least one integration test exists in `tests/integration/data_sources_and_expectations` (see [AGENTS.md](https://github.com/fivetran/great_expectations/blob/develop/AGENTS.md#integration-test-requirement))
- [ ] If this PR proposes adopting or recommending a particular third-party library or service, any affiliation with it (employment, financial interest, maintainership) is disclosed above for the reviewer's context

For more information about contributing, visit our [community resources](https://docs.greatexpectations.io/docs/core/introduction/community_resources#contribute-code-or-documentation).

After you submit your PR, keep the page open and **monitor the statuses of the various checks made by our continuous integration process at the bottom of the page. Please fix any issues that come up** and [reach out on Slack](https://greatexpectations.io/slack) if you need help. Thanks for contributing!
