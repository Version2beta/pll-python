"""Stage 1 domain errors. Complete; do not change."""


class PllError(Exception):
    """Base class for library domain failures."""


class InvalidRateError(PllError):
    code = "invalid_rate"

    def __str__(self):
        return "pll: invalid rate"


class InvalidArgumentError(PllError):
    code = "invalid_argument"

    def __str__(self):
        return "pll: invalid argument"


class PllOverflowError(PllError):
    code = "overflow"

    def __str__(self):
        return "pll: overflow"


class OrderError(PllError):
    code = "order"

    def __str__(self):
        return "pll: reading out of order"


class NotAnchoredError(PllError):
    code = "not_anchored"

    def __str__(self):
        return "pll: follower has no reading yet"


class ConfigError(PllError):
    code = "config"

    def __init__(self, field: str, reason: str):
        super().__init__(field, reason)
        self._field, self._reason = field, reason

    @property
    def field(self) -> str:
        return self._field

    @property
    def reason(self) -> str:
        return self._reason

    def __str__(self):
        return f"pll: FollowerConfig.{self.field} {self.reason}"
