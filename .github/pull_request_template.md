


- [ ] Description of PR changes above includes a link to [an existing GitHub issue](https://github.com/great-expectations/great_expectations/issues)
- [ ] PR title is prefixed with one of: [BUGFIX], [FEATURE], [DOCS], [MAINTENANCE], [CONTRIB], [MINORBUMP]
- [ ] Code is linted - run `invoke lint` (uses `ruff format` + `ruff check`)
- [ ] Appropriate tests and docs have been updated
- [ ] For any behavioral change to a data source, validation mechanic, or Expectation, at least one integration test exists in `tests/integration/data_sources_and_expectations` (see [AGENTS.md#integration-test-requirement](AGENTS.md#integration-test-requirement))
- [ ] CI is green, including linting, mypy type-checking, and tests - this is required for merge
- [ ] If this PR proposes adopting or recommending a particular third-party library or service, any affiliation with it (employment, financial interest, maintainership) is disclosed above for the reviewer's context

For more information about contributing, visit our [community resources](https://docs.greatexpectations.io/docs/core/introduction/community_resources#contribute-code-or-documentation).

After you submit your PR, keep the page open and **monitor the statuses of the various checks made by our continuous integration process at the bottom of the page. Please fix any issues that come up** and [reach out on Slack](https://greatexpectations.io/slack) if you need help. Thanks for contributing!
