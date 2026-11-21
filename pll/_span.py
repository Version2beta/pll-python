"""Implement timing and lazy iteration for the protected immutable Span value."""
from collections.abc import Iterator
from ._rate import _checked_int
from ._values import Span


def _scaled_offset(segment, slot: int) -> tuple[int, int]:
    """Exact ns offset of slot from the segment anchor as (numerator, denominator)."""
    offset = slot - segment.start
    numerator = offset * segment.numerator
    denominator = segment.denominator
    return numerator, denominator


def floor_slot_time(segment, slot: int) -> int:
    """Floored exact time of slot; the trim denominator is always positive."""
    numerator, denominator = _scaled_offset(segment, slot)
    return segment.anchor + numerator // denominator


def ceil_slot_time(segment, slot: int) -> int:
    """Ceiling exact time of slot for the nonnegative offsets issued here."""
    numerator, denominator = _scaled_offset(segment, slot)
    return segment.anchor - (-numerator // denominator)


def span_time(span: Span, i: int) -> int:
    """Implement Span.time: exact floor and Python index validation."""
    i = _checked_int(i)
    if not 0 <= i < span.count:
        raise IndexError("span index outside 0..count-1")
    return floor_slot_time(span._segment, span.first + i)


def span_all(span: Span) -> Iterator[tuple[int, int]]:
    """Implement Span.all: a fresh iterator; no eager timing computations."""
    for i in range(span.count):
        yield span.first + i, span.time(i)
