# Prompt 007 — API coverage measurement

The brief requires meeting “all API coverage criteria” without defining them. Use: endpoint coverage, HTTP method coverage, status-code coverage for every documented code, request-field coverage, valid and invalid input class coverage, and response-schema coverage. Add a pytest plugin or fixture that logs every request and response, and write tools/api_coverage.py that compares that log against openapi/openapi.yaml and prints a coverage table. Show real numbers, list the gaps, and add tests to close them. Save the output to docs/api/coverage-report.md.
