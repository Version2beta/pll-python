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
