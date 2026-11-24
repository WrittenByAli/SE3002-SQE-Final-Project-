"""Cosmic Ray entry-point provider for the two custom rule operators."""

from .operators import BookingLimitBoundaryOperator, CancellationGraceGuardOperator


class Provider:
    _operators = {
        "BR1BookingLimitBoundary": BookingLimitBoundaryOperator,
        "BR3CancellationGraceGuard": CancellationGraceGuardOperator,
    }

    def __iter__(self):
        return iter(self._operators)

    def __getitem__(self, name):
        return self._operators[name]
