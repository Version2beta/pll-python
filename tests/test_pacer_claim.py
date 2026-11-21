"""Exact pacer: constructor, claim extent, next_due ceiling and atomicity."""
import unittest
from pll import (Pacer, Rate, units_per_second, InvalidRateError,
                 InvalidArgumentError, PllOverflowError)
from tests.test_rate import IntSubclass, U

I = 2**63 - 1


class ClaimTests(unittest.TestCase):
    def test_constructor_and_initial_cursor(self):
        p = Pacer(units_per_second(48000, 1))
        self.assertEqual((p.next_due(), p.trim()), ((0, 0), 0))
        with self.assertRaises(InvalidRateError):
            Pacer(Rate())
        for value in (None, 1, True, "rate"):
            with self.assertRaises(TypeError):
                Pacer(value)

    def test_claim_contiguity_and_ceil(self):
        p = Pacer(units_per_second(375000000, 1))  # 8/3 ns
        s = p.claim(n=IntSubclass(2))
        self.assertEqual((s.first, s.count), (0, 2))
        self.assertEqual(p.next_due(), (2, 6))
        t = p.claim(3)
        self.assertEqual((t.first, t.count), (2, 3))
        self.assertEqual(p.next_due(), (5, 14))
        self.assertEqual(p.next_due(), (5, 14))

    def test_claim_validation_atomic(self):
        p = Pacer(units_per_second(1000, 1))
        p.claim(3)
        for value, error in [(False, TypeError), (1.0, TypeError), (None, TypeError),
                             (-1, OverflowError), (U+1, OverflowError),
                             (0, InvalidArgumentError), (U, PllOverflowError)]:
            before = (p.next_due(), p.trim())
            with self.subTest(value=value), self.assertRaises(error):
                p.claim(value)
            self.assertEqual((p.next_due(), p.trim()), before)
        self.assertEqual(p.claim(1).first, 3)

    def test_floor_fit_ceil_overflow(self):
        p = Pacer(units_per_second(2000000000, U))
        p.claim(1)
        with self.assertRaises(PllOverflowError):
            p.next_due()
        s = p.claim(1)  # floor fits even though ceiling does not
        self.assertEqual((s.first, s.count), (1, 1))
        with self.assertRaises(PllOverflowError):
            p.claim(1)
        self.assertEqual(p.trim(), 0)

    def test_huge_claim_no_materialization(self):
        p = Pacer(units_per_second(U, 1))
        s = p.claim(U)
        self.assertEqual((s.first, s.count), (0, U))
        for query in (p.next_due, lambda: p.claim(1)):
            with self.assertRaises(PllOverflowError):
                query()
        self.assertEqual((s.first, s.count), (0, U))
