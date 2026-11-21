"""Implement complete follower per README; no external effects."""
from ._follower_values import FollowerConfig, Observation, State
from ._values import Rate


def default_follower_config(nominal: Rate) -> FollowerConfig:
    """Return defaults without validating nominal."""
    raise NotImplementedError


class Follower:
    def __init__(self, config: FollowerConfig):
        """Validate field-by-field, snapshot configuration; start unanchored."""
        raise NotImplementedError

    def observe(self, local_ns: int, remote: int) -> Observation:
        """Feed ordered input, including windows/outliers/steps; atomic on failure."""
        raise NotImplementedError

    def local(self, remote: int) -> int:
        """Round displacement then add integer anchor; check final signed64 result."""
        raise NotImplementedError

    def remote(self, local_ns: int) -> int:
        """Inverse mapping with ties away and exact integer-base addition."""
        raise NotImplementedError

    def offset(self) -> float:
        """Estimated fractional rate offset."""
        raise NotImplementedError

    def trim(self) -> int:
        """Rounded, pacer-safe parts-per-trillion offset."""
        raise NotImplementedError

    def jitter(self) -> int:
        """Saturated rounded RMS, zero until two accepted inliers."""
        raise NotImplementedError

    def state(self, now_ns: int) -> State:
        """Pure exact elapsed holdover/lock query."""
        raise NotImplementedError

    def reset(self) -> None:
        """Clear all learned state and retain validated configuration."""
        raise NotImplementedError
