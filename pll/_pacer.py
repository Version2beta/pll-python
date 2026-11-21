"""Implement the exact owned controller. No clocks or external effects."""
from math import gcd

from ._errors import InvalidArgumentError, InvalidRateError, PllOverflowError
from ._rate import _checked_int, _U
from ._span import ceil_slot_time, floor_slot_time
from ._values import Rate, Span, _Segment

_IMAX = 2**63 - 1


def _checked_due_inputs(now_ns: int, count: int) -> tuple[int, int]:
    """Check both types, both envelopes, then the shared time semantics."""
    now_ns = _checked_int(now_ns)
    count = _checked_int(count)
    if not -2**63 <= now_ns <= _IMAX:
        raise OverflowError("pacer time outside signed 64-bit range")
    if not 0 <= count <= _U:
        raise OverflowError("pacer count outside 0..2**64-1")
    if now_ns < 0:
        raise InvalidArgumentError()
    return now_ns, count


class Pacer:
    def __init__(self, rate: Rate):
        """Validate Rate; start at slot zero with zero trim."""
        if not isinstance(rate, Rate):
            raise TypeError("Pacer requires a Rate")
        if rate.num == 0 or rate.den == 0:
            raise InvalidRateError()
        # Period is den * 10**9 / num ns per slot: numerator den*10**9, denominator num.
        self._segment = _Segment(0, 0, rate.den * 10**9, rate.num, 0)
        self._cursor = 0

    def due(self, now_ns: int, max_count: int) -> Span:
        """Issue oldest exact-due slots, capped; preserve state on failure."""
        now_ns, max_count = _checked_due_inputs(now_ns, max_count)
        if max_count == 0:
            raise InvalidArgumentError()
        count = min(self._due_count(now_ns), max_count)
        span = Span._make(self._cursor, count, self._segment)
        self._cursor += count
        return span

    def claim(self, n: int) -> Span:
        """Issue n slots if extent and last floor fit; atomic on failure."""
        n = _checked_int(n)
        if not 0 <= n <= _U:
            raise OverflowError("claim count outside 0..2**64-1")
        if n == 0:
            raise InvalidArgumentError()
        first = self._cursor
        if n > _U - first:
            raise PllOverflowError()
        if floor_slot_time(self._segment, first + n - 1) > _IMAX:
            raise PllOverflowError()
        self._cursor = first + n
        return Span._make(first, n, self._segment)

    def skip(self, now_ns: int, keep: int) -> int:
        """Skip all but newest keep due slots, excluding slot U."""
        now_ns, keep = _checked_due_inputs(now_ns, keep)
        count = self._due_count(now_ns)
        skipped = count - min(count, keep)
        self._cursor += skipped
        return skipped

    def _due_count(self, now_ns: int) -> int:
        """Invert exact segment timing without enumerating slots or rounding times."""
        segment = self._segment
        if now_ns < segment.anchor:
            return 0
        # T(s) <= now iff (s-S)*period_numerator <= (now-A)*period_denominator.
        last = segment.start + (
            (now_ns - segment.anchor) * segment.denominator
            // segment.numerator
        )
        last = min(last, _U)
        if last < self._cursor:
            return 0
        if self._cursor == _U:
            raise PllOverflowError()
        return min(last, _U - 1) - self._cursor + 1

    def next_due(self) -> tuple[int, int]:
        """Return cursor and ceiling; reject cursor U or non-fitting ceiling."""
        if self._cursor == _U:
            raise PllOverflowError()
        due = ceil_slot_time(self._segment, self._cursor)
        if due > _IMAX:
            raise PllOverflowError()
        return (self._cursor, due)

    def set_trim(self, ppt: int) -> None:
        """Validate; equal trim is a no-op; otherwise anchor at old cursor floor."""
        ppt = _checked_int(ppt)
        if not -2**63 <= ppt <= _IMAX:
            raise OverflowError("trim outside signed 64-bit range")
        if not -10**12 < ppt < 10**12:
            raise InvalidArgumentError()
        segment = self._segment
        if ppt == segment.trim:
            return
        anchor = floor_slot_time(segment, self._cursor)
        if anchor > _IMAX:
            raise PllOverflowError()
        # Undo the old trim and apply the new one to the exact stored period.
        numerator = segment.numerator * (10**12 + segment.trim)
        denominator = segment.denominator * (10**12 + ppt)
        divisor = gcd(numerator, denominator)
        # Replace the immutable segment only after validation; issued spans keep it.
        self._segment = _Segment(
            self._cursor, anchor, numerator // divisor, denominator // divisor, ppt
        )

    def trim(self) -> int:
        """Return current trim in parts per trillion."""
        return self._segment.trim
