"""Follower values and byte enums. Complete; do not change."""
from dataclasses import dataclass
from enum import IntEnum, EnumType
from ._values import Rate


class _ByteEnumType(EnumType):
    def __call__(cls, value):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("enum value must be int, not bool")
        if not 0 <= value <= 255:
            raise ValueError("enum value outside byte domain")
        return super().__call__(int.__index__(value))


class _ByteEnum(IntEnum, metaclass=_ByteEnumType):
    @classmethod
    def _missing_(cls, value):
        result = int.__new__(cls, value)
        result._name_ = None
        result._value_ = value
        return result

    def __str__(self):
        return self.name.lower() if self.name else f"{type(self).__name__}({int(self)})"


class Status(_ByteEnum):
    ANCHORED = 1
    ACCEPTED = 2
    PENDING = 3
    REJECTED = 4
    STEPPED = 5


class State(_ByteEnum):
    ACQUIRING = 0
    LOCKED = 1
    HOLDOVER = 2


@dataclass(frozen=True, slots=True)
class FollowerConfig:
    nominal: Rate
    bandwidth_hz: float
    damping: float
    max_offset_ppm: float
    window_ns: int
    outlier_threshold_ns: int
    step_after: int
    lock_threshold_ns: int
    lock_count: int
    holdover_after_ns: int


@dataclass(frozen=True, slots=True)
class Observation:
    status: Status
    error_ns: int
