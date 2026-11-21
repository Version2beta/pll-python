"""Implement exact reduced rate factories; see README and SPEC."""
from math import gcd

from ._errors import InvalidRateError
from ._values import Rate

_U = 2**64 - 1


def _checked_int(value) -> int:
    """Reject non-int and bool; return a plain int copy of an int subclass."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("rate arguments must be int")
    # int.__index__ copies an int subclass without calling its overrides.
    return int.__index__(value)


def _reduced_rate(first, second) -> Rate:
    """Validate in README order: all types, all envelopes, then zero terms."""
    first = _checked_int(first)
    second = _checked_int(second)
    for value in (first, second):
        if not 0 <= value <= _U:
            raise OverflowError("rate term outside 0..2**64-1")
    if first == 0 or second == 0:
        raise InvalidRateError()
    divisor = gcd(first, second)
    return Rate._make(first // divisor, second // divisor)


def units_per_second(num: int, den: int) -> Rate:
    """Types, envelopes, then nonzero terms; reduce by gcd."""
    return _reduced_rate(num, den)


def bits_per_second(bits: int, bits_per_unit: int) -> Rate:
    """Same exact fraction as units_per_second, with the same validation."""
    return _reduced_rate(bits, bits_per_unit)
