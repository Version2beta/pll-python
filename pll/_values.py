"""Immutable values and issuance seam. Complete; do not change.

Private _make methods are for validated library results, not public construction.
Segment terms describe an exact period in ns; no live controller is retained.
"""
from collections.abc import Iterator
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True, init=False)
class Rate:
    num: int = 0
    den: int = 0

    def __init__(self):
        object.__setattr__(self, "num", 0)
        object.__setattr__(self, "den", 0)

    @classmethod
    def _make(cls, num: int, den: int):
        value = cls()
        object.__setattr__(value, "num", num)
        object.__setattr__(value, "den", den)
        return value

    def __str__(self):
        if not self.den:
            return "invalid rate"
        terms = str(self.num) if self.den == 1 else f"{self.num}/{self.den}"
        return f"{terms} units/s"


@dataclass(frozen=True, slots=True)
class _Segment:
    start: int
    anchor: int
    numerator: int
    denominator: int
    trim: int


@dataclass(frozen=True, slots=True, init=False)
class Span:
    first: int = 0
    count: int = 0
    _segment: _Segment | None = field(default=None, repr=False)

    def __init__(self):
        object.__setattr__(self, "first", 0)
        object.__setattr__(self, "count", 0)
        object.__setattr__(self, "_segment", None)

    @classmethod
    def _make(cls, first: int, count: int, segment: _Segment):
        value = cls()
        object.__setattr__(value, "first", first)
        object.__setattr__(value, "count", count)
        object.__setattr__(value, "_segment", segment)
        return value

    def time(self, i: int) -> int:
        """Floor the exact time; reject bool/non-int and any out-of-range index."""
        from ._span import span_time
        return span_time(self, i)

    def all(self) -> Iterator[tuple[int, int]]:
        """Fresh lazy iterator: compute only items requested by the caller."""
        from ._span import span_all
        return span_all(self)
