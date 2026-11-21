"""Implement complete follower per README; no external effects."""
import math

from ._errors import ConfigError, NotAnchoredError, OrderError, PllOverflowError
from ._follower_values import FollowerConfig, Observation, State, Status
from ._values import Rate


def default_follower_config(nominal: Rate) -> FollowerConfig:
    """Return defaults without validating nominal."""
    return FollowerConfig(
        nominal, 0.1, math.sqrt(2) / 2, 500.0,
        0, 5_000_000, 3, 100_000, 8, 5_000_000_000,
    )


_LO, _HI = -(2**63), 2**63 - 1


def _inputs(*values):
    # Public arguments use phased validation, unlike config fields.
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("expected int, not bool")
    values = tuple(int.__index__(value) for value in values)
    for value in values:
        if not _LO <= value <= _HI:
            raise OverflowError("outside signed64 domain")
    return values


def _between(a, b):
    difference = a - b
    return float(difference) if _LO <= difference <= _HI else float(a) - float(b)


def _round_away(value):
    # Adding 0.5 first can change already-integral binary64 values.
    fraction, whole = math.modf(value)
    result = int(whole)
    if fraction >= 0.5:
        result += 1
    elif fraction <= -0.5:
        result -= 1
    return result


def _checked_result(value):
    if not _LO <= value <= _HI:
        raise PllOverflowError()
    return value


def _saturated(value):
    return max(_LO, min(_HI, _round_away(value)))


class Follower:
    def __init__(self, config: FollowerConfig):
        """Validate field-by-field, snapshot configuration; start unanchored."""
        if not isinstance(config, FollowerConfig):
            raise TypeError("config must be FollowerConfig")
        nominal = config.nominal
        if not isinstance(nominal, Rate):
            raise TypeError("nominal must be Rate")
        if nominal.num <= 0 or nominal.den <= 0:
            raise ConfigError("nominal", "must be a valid Rate")

        values = {"nominal": nominal}
        for name in ("bandwidth_hz", "damping", "max_offset_ppm"):
            value = getattr(config, name)
            if not isinstance(value, float):
                raise TypeError(f"{name} must be float")
            value = float.__float__(value)
            reason = "must be finite and > 0"
            invalid = not math.isfinite(value) or value <= 0
            if name == "max_offset_ppm":
                reason = "must be finite, > 0 and < 1000000"
                invalid = invalid or value >= 1_000_000
            if invalid:
                raise ConfigError(name, reason)
            values[name] = value

        # Config deliberately completes each field before inspecting the next.
        for name, minimum, reason in (
            ("window_ns", 0, "must be >= 0"),
            ("outlier_threshold_ns", 1, "must be > 0"),
            ("step_after", 1, "must be >= 1"),
            ("lock_threshold_ns", 0, "must be >= 0"),
            ("lock_count", 1, "must be >= 1"),
            ("holdover_after_ns", 1, "must be > 0"),
        ):
            value = getattr(config, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be int, not bool")
            value = int.__index__(value)
            if not -(2**63) <= value <= 2**63 - 1:
                raise OverflowError(f"{name} outside signed64 domain")
            if value < minimum:
                raise ConfigError(name, reason)
            values[name] = value

        self._config = FollowerConfig(**values)
        self._period = (float(nominal.den) * 1e9) / float(nominal.num)
        self.reset()

    def observe(self, local_ns: int, remote: int) -> Observation:
        """Feed ordered input, including windows/outliers/steps; atomic on failure."""
        local_ns, remote = _inputs(local_ns, remote)
        if self._anchored and (local_ns < self._previous[0] or remote <= self._previous[1]):
            raise OrderError()
        # All mutable history is scalar or an immutable tuple. Stage the whole
        # transition, including a window flush, before publishing any changes.
        staged = object.__new__(Follower)
        staged.__dict__ = self.__dict__.copy()
        result = staged._observe(local_ns, remote)
        staged._previous = (local_ns, remote)
        self.__dict__.update(staged.__dict__)
        return result

    def _displacement(self, remote):
        return ((_between(remote, self._remote_anchor) * self._period) / (1 + self._y)) + self._fraction

    def _error(self, local_ns, remote):
        return _between(local_ns, self._anchor) - self._displacement(remote)

    def _reanchor(self, local_ns, remote):
        self._anchor = local_ns
        self._remote_anchor = remote
        self._fraction = 0.0
        self._reference = local_ns
        self._last_accepted = local_ns
        self._lock = 0
        self._mean_square = 0.0
        self._jitter_samples = 0
        self._outlier_first = 0.0
        self._outlier_count = 0

    def _observe(self, local_ns, remote):
        if not self._anchored:
            self._reanchor(local_ns, remote)
            self._anchored = True
            return Observation(Status.ANCHORED, 0)
        window = self._config.window_ns
        if window == 0:
            return self._feed(local_ns, remote, self._error(local_ns, remote))
        if self._window_start is None:
            self._window_start = local_ns
            self._candidate = (local_ns, remote, self._error(local_ns, remote))
            return Observation(Status.PENDING, 0)
        if local_ns - self._window_start >= window:
            result = self._feed(*self._candidate)
            self._window_start = local_ns
            # The triggering input belongs to the new, post-update mapping.
            self._candidate = (local_ns, remote, self._error(local_ns, remote))
            return result
        error = self._error(local_ns, remote)
        if error < self._candidate[2]:
            self._candidate = (local_ns, remote, error)
        return Observation(Status.PENDING, 0)

    def _feed(self, local_ns, remote, error):
        config = self._config
        reported = _saturated(error)
        # Match the pinned binary64 comparisons: Python's mixed float/int
        # comparison would instead preserve threshold bits lost in Go's cast
        # (notably Imax, which converts to 2**63).
        threshold = float(config.outlier_threshold_ns)
        if abs(error) > threshold:
            if self._outlier_count and abs(error - self._outlier_first) <= threshold:
                self._outlier_count += 1
            else:
                self._outlier_first = error
                self._outlier_count = 1
            if self._outlier_count >= config.step_after:
                self._reanchor(local_ns, remote)
                return Observation(Status.STEPPED, reported)
            return Observation(Status.REJECTED, reported)

        dt = _between(local_ns, self._reference) / 1e9
        if dt > 0:
            wn = (2 * math.pi) * config.bandwidth_hz
            x = min(0.5, wn * dt)
            kp = min(1.0, 2 * (config.damping * x))
            limit = config.max_offset_ppm * 1e-6
            y = self._y - (x * x / dt) * error / 1e9
            y = max(-limit, min(limit, y))
            displacement = self._displacement(remote) + kp * error
            whole = _round_away(displacement)
            anchor = _checked_result(self._anchor + whole)
            self._anchor = anchor
            self._fraction = displacement - whole
            self._remote_anchor = remote
            self._reference = local_ns
            self._y = y

        self._outlier_count = 0
        self._outlier_first = 0.0
        if abs(error) <= float(config.lock_threshold_ns):
            self._lock = min(config.lock_count, self._lock + 1)
        else:
            self._lock = 0
        square = error * error
        if self._jitter_samples == 0:
            self._mean_square = square
        else:
            self._mean_square += (square - self._mean_square) / 16
        self._jitter_samples = min(2, self._jitter_samples + 1)
        self._last_accepted = local_ns
        return Observation(Status.ACCEPTED, reported)

    def local(self, remote: int) -> int:
        """Round displacement then add integer anchor; check final signed64 result."""
        remote, = _inputs(remote)
        if not self._anchored:
            raise NotAnchoredError()
        return _checked_result(self._anchor + _round_away(self._displacement(remote)))

    def remote(self, local_ns: int) -> int:
        """Inverse mapping with ties away and exact integer-base addition."""
        local_ns, = _inputs(local_ns)
        if not self._anchored:
            raise NotAnchoredError()
        displacement = ((_between(local_ns, self._anchor) - self._fraction) * (1 + self._y)) / self._period
        return _checked_result(self._remote_anchor + _round_away(displacement))

    def offset(self) -> float:
        """Estimated fractional rate offset."""
        return self._y

    def trim(self) -> int:
        """Rounded, pacer-safe parts-per-trillion offset."""
        return max(-999_999_999_999, min(999_999_999_999, _round_away(self._y * 10**12)))

    def jitter(self) -> int:
        """Saturated rounded RMS, zero until two accepted inliers."""
        return 0 if self._jitter_samples < 2 else _saturated(math.sqrt(self._mean_square))

    def state(self, now_ns: int) -> State:
        """Pure exact elapsed holdover/lock query."""
        now_ns, = _inputs(now_ns)
        if self._anchored and now_ns - self._last_accepted > self._config.holdover_after_ns:
            return State.HOLDOVER
        return State.LOCKED if self._lock >= self._config.lock_count else State.ACQUIRING

    def reset(self) -> None:
        """Clear all learned state and retain validated configuration."""
        self._anchored = False
        self._y = 0.0
        self._reanchor(0, 0)
        self._previous = None
        self._window_start = None
        self._candidate = None
