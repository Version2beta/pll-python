"""Exact pacing stage public surface. Complete; do not change.

Follower and its associated values/errors are deferred, not partial exports.
"""
from ._errors import InvalidArgumentError, InvalidRateError, PllError, PllOverflowError
from ._values import Rate, Span
from ._rate import bits_per_second, units_per_second
from ._pacer import Pacer

__all__ = [
    "Rate", "Span", "Pacer", "units_per_second", "bits_per_second",
    "PllError", "InvalidRateError", "InvalidArgumentError", "PllOverflowError",
]
