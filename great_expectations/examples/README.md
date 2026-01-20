### Pandas Validation Pipeline (CI-Friendly)
This example shows how to use Great Expectations in CI:
- defines expectations
- validates a pandas dataframe
- outputs a JSON validation artifact
- fails (exit code 1) if validation fails

Run:
```bash
python examples/quickstart/pandas_validation_pipeline.py
```
Artifacts saved to:
`outputs/ge_validation/`
```

## 4. Make the Pull Request
Commit and push your changes:
```bash
git add examples/quickstart/pandas_validation_pipeline.py examples/README.md
git commit -m "Add example: pandas validation pipeline with CI integration"
git push origin add-ci-validation-example