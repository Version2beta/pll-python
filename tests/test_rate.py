"""README Public API; Types, bounds and exceptions: rate factories."""
import inspect
import unittest
from dataclasses import FrozenInstanceError
import pll
from pll import (Rate, Pacer, units_per_second, bits_per_second, PllError,
                 InvalidRateError, InvalidArgumentError, PllOverflowError)

U = 2**64 - 1


class IntSubclass(int):
    pass


class RateTests(unittest.TestCase):
    def test_reduction_and_strings(self):
        for factory in (units_per_second, bits_per_second):
            for n, d, terms, text in [(60000, 2002, (30000, 1001), "30000/1001 units/s"),
                                      (48000, 1, (48000, 1), "48000 units/s"),
                                      (U, U, (1, 1), "1 units/s"),
                                      (U, U-1, (U, U-1), f"{U}/{U-1} units/s")]:
                with self.subTest(factory=factory.__name__, n=n, d=d):
                    r = factory(n, d)
                    self.assertIsInstance(r, Rate)
                    self.assertEqual((r.num, r.den), terms)
                    self.assertEqual(str(r), text)

    def test_type_then_envelope_then_semantics(self):
        for factory in (units_per_second, bits_per_second):
            for args in [(0, "x"), (-1, "x"), (U+1, False), (True, 1), (1, 1.0), (None, 0)]:
                with self.subTest(args=args):
                    with self.assertRaises(TypeError):
                        factory(*args)
            for args in [(0, U+1), (-1, 0), (1, -1), (U+1, 1)]:
                with self.assertRaises(OverflowError):
                    factory(*args)
            for args in [(0, 1), (1, 0), (0, 0)]:
                with self.assertRaises(InvalidRateError):
                    factory(*args)

    def test_integer_subclasses(self):
        r = units_per_second(IntSubclass(60000), IntSubclass(2002))
        self.assertEqual((r.num, r.den), (30000, 1001))

    def test_sentinel_and_immutable_rates(self):
        self.assertEqual((Rate().num, Rate().den, str(Rate())), (0, 0, "invalid rate"))
        for r in (Rate(), units_per_second(3, 2)):
            for name in ("num", "den"):
                with self.assertRaises((FrozenInstanceError, AttributeError)):
                    setattr(r, name, 7)
            with self.assertRaises((FrozenInstanceError, AttributeError)):
                del r.num
        with self.assertRaises(TypeError):
            Rate(3, 2)

    def test_errors(self):
        for cls, code, message in [
            (InvalidRateError, "invalid_rate", "pll: invalid rate"),
            (InvalidArgumentError, "invalid_argument", "pll: invalid argument"),
            (PllOverflowError, "overflow", "pll: overflow")]:
            self.assertIsInstance(cls(), PllError)
            self.assertEqual((cls().code, str(cls())), (code, message))
            self.assertFalse(issubclass(cls, OverflowError))

    def test_surface_and_signatures(self):
        self.assertEqual(set(pll.__all__), {"Rate", "Span", "Pacer", "units_per_second",
                         "bits_per_second", "PllError", "InvalidRateError",
                         "InvalidArgumentError", "PllOverflowError", "Follower",
                         "FollowerConfig", "Observation", "Status", "State",
                         "default_follower_config", "OrderError", "ConfigError", "NotAnchoredError"})
        for fn, params in [(units_per_second, ["num", "den"]),
                           (bits_per_second, ["bits", "bits_per_unit"]),
                           (Pacer, ["rate"]), (Rate, []), (pll.Span, [])]:
            self.assertEqual(list(inspect.signature(fn).parameters), params)
