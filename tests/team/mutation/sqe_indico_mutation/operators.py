"""Business-rule-specific mutations for Indico Room Booking."""

from cosmic_ray.operators.operator import Operator


def _enclosing_function_name(node):
    """Return the nearest function name for a parso node, if any."""
    parent = getattr(node, "parent", None)
    while parent is not None:
        if getattr(parent, "type", None) == "funcdef":
            return parent.children[1].value
        parent = getattr(parent, "parent", None)
    return None


def _token(node, value):
    """Create a replacement token while retaining its concrete-syntax type."""
    return type(node)(value, node.start_pos)


class BookingLimitBoundaryOperator(Operator):
    """Make the BR1 booking-limit boundary exclusive instead of inclusive."""

    def mutation_positions(self, node):
        if (getattr(node, "value", None) == "<=" and
                _enclosing_function_name(node) == "_validate_room_booking_limit"):
            yield (node.start_pos, node.end_pos)

    def mutate(self, node, index):
        assert index == 0
        return _token(node, "<")

    @classmethod
    def examples(cls):
        return [("selected_period_days <= booking_limit_days",
                 "selected_period_days < booking_limit_days", 0)]


class CancellationGraceGuardOperator(Operator):
    """Change BR3's pending/grace guard from AND to OR."""

    def mutation_positions(self, node):
        parent_code = "".join(getattr(getattr(node, "parent", None), "get_code", lambda: "")().split())
        if (getattr(node, "value", None) == "and" and
                _enclosing_function_name(node) == "can_cancel" and
                "notself.is_pendingandnot" in parent_code):
            yield (node.start_pos, node.end_pos)

    def mutate(self, node, index):
        assert index == 0
        return _token(node, "or")

    @classmethod
    def examples(cls):
        return [("not is_pending and not has_grace_occurrence",
                 "not is_pending or not has_grace_occurrence", 0)]
