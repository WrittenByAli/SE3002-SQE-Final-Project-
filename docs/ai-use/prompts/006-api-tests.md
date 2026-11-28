Write the API tests in tests/team/api/, driven by the generated cases:
1. EP and 3-point BVA on every input of both workflows.
2. Decision-table tests for every business rule with two or more conditions.
3. State-transition tests: every allowed transition, plus at least one disallowed transition from each state, asserting rejection and unchanged state.
4. Rule rejections: after every rejected request, read the shared record back and assert it did not change.
5. After every successful request, read the shared record back and assert the new value.
6. Repeated requests: send the same request twice and also in rapid succession; assert no duplicate records.
7. Cross-workflow: workflow A changes the shared record, and workflow B must see the new value.
8. Role checks: the lower-privileged role is denied where it should be.
Run the suite and show me the real output. For any failure caused by app behaviour, do not change the assertion; log it in docs/api/suspected-defects.md with request, response, expected behaviour and the rule it breaks.
