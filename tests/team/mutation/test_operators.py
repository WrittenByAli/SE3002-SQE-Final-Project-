"""Unit tests for the custom operator targeting and replacement rules."""

import parso
import pytest

from sqe_indico_mutation.operators import (BookingLimitBoundaryOperator,
                                           CancellationGraceGuardOperator)


def _leaves(node):
    if hasattr(node, "children"):
        for child in node.children:
            yield from _leaves(child)
    else:
        yield node


@pytest.mark.parametrize(
    ("operator", "function", "before", "after"),
    [
        (BookingLimitBoundaryOperator, "_validate_room_booking_limit",
         "selected_period_days <= booking_limit_days", "selected_period_days < booking_limit_days"),
        (CancellationGraceGuardOperator, "can_cancel",
         "not self.is_pending and not self.occurrences.filter(grace_check).has_rows()",
         "not self.is_pending or not self.occurrences.filter(grace_check).has_rows()"),
    ],
)
def test_custom_operator_mutates_only_its_named_business_rule(operator, function, before, after):
    source = f"def {function}(self):\n    if {before}:\n        return False\n"
    module = parso.parse(source)
    tokens = [leaf for leaf in _leaves(module) if getattr(leaf, "value", None) in ("<=", "and")]
    assert len(tokens) == 1

    mutation = operator()
    token = tokens[0]
    assert list(mutation.mutation_positions(token)) == [(token.start_pos, token.end_pos)]
    assert mutation.mutate(token, 0).value == ("<" if "<=" in before else "or")
    example_before, example_after, index = mutation.examples()[0]
    assert index == 0
    expected_example = example_before.replace("<=", "<").replace(" and ", " or ")
    assert expected_example == example_after


@pytest.mark.parametrize(
    ("operator", "function", "token"),
    [
        (BookingLimitBoundaryOperator, "other_function", "<="),
        (CancellationGraceGuardOperator, "can_edit", "and"),
    ],
)
def test_custom_operator_ignores_other_functions(operator, function, token):
    module = parso.parse(f"def {function}(self):\n    if left {token} right:\n        return False\n")
    leaf = next(leaf for leaf in _leaves(module) if getattr(leaf, "value", None) == token)

    assert list(operator().mutation_positions(leaf)) == []
