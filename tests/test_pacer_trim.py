"""Floor anchoring, equal-trim no-op, retained spans and rollback."""
import unittest
from fractions import Fraction
from pll import Pacer, units_per_second, InvalidArgumentError, PllOverflowError
from tests.test_rate import IntSubclass, U
from tests.test_pacer_claim import I


class TrimTests(unittest.TestCase):
    def test_floor_anchor_and_retained_spans(self):
        rate = units_per_second(375000000, 1)
        p = Pacer(rate)

        def assert_period(span, trim):
            # SPEC's protected issuance seam stores the exact trimmed ns period.
            segment = span._segment
            self.assertGreater(segment.numerator, 0)
            self.assertGreater(segment.denominator, 0)
            self.assertEqual(segment.numerator * rate.num * (10**12 + trim),
                             segment.denominator * rate.den * 10**21)

        old = p.claim(1)
        assert_period(old, 0)
        self.assertIsNone(p.set_trim(-500000000000))  # floor(8/3)=2
        self.assertEqual(p.trim(), -500000000000)
        self.assertEqual(p.next_due(), (1, 2))
        s = p.claim(3)
        assert_period(s, -500000000000)
        self.assertEqual(list(s.all()), [(1, 2), (2, 7), (3, 12)])
        p.set_trim(500000000000)
        assert_period(old, 0)
        assert_period(s, -500000000000)
        self.assertEqual(list(s.all()), [(1, 2), (2, 7), (3, 12)])
        self.assertEqual(list(old.all()), [(0, 0)])
        new = p.claim(1)
        assert_period(new, 500000000000)
        self.assertEqual(new.time(0), 18)

    def test_equal_trim_does_not_reanchor(self):
        p = Pacer(units_per_second(375000000, 1))
        p.claim(1)
        p.set_trim(0)
        self.assertEqual(p.next_due(), (1, 3))  # not floor 2
        self.assertEqual(p.claim(2).time(1), 5)
        p = Pacer(units_per_second(1, U))
        p.claim(1)
        self.assertIsNone(p.set_trim(0))  # cursor floor does not fit
        with self.assertRaises(PllOverflowError):
            p.set_trim(1)
        self.assertEqual(p.trim(), 0)
        with self.assertRaises(PllOverflowError):
            p.next_due()
        p = Pacer(units_per_second(2000000000, U))
        p.claim(1)
        with self.assertRaises(PllOverflowError):
            p.next_due()
        p.set_trim(1)  # floor I fits even though the old ceiling does not
        self.assertEqual(p.next_due(), (1, I))
        self.assertEqual(p.claim(1).time(0), I)

    def test_extreme_trims_and_large_terms(self):
        for n, d in [(U, U-1), (U, 1), (4294967295, 4294967291), (1, U)]:
            for q in (-10**12+1, 10**12-1):
                p = Pacer(units_per_second(n, d))
                p.set_trim(IntSubclass(q))
                self.assertEqual(p.trim(), q)
                period = Fraction(d*10**21, n*(10**12+q))
                p.claim(1)
                ceiling = -(-period.numerator // period.denominator)
                if ceiling <= I:
                    self.assertEqual(p.next_due(), (1, ceiling))
                else:
                    with self.assertRaises(PllOverflowError):
                        p.next_due()

    def test_validation_and_failed_change_atomic(self):
        p = Pacer(units_per_second(1000, 1))
        old = p.claim(3)
        old_times = list(old.all())
        p.set_trim(123)
        for q, error in [(True, TypeError), (1.0, TypeError), (None, TypeError),
                         (-2**63-1, OverflowError), (I+1, OverflowError),
                         (-10**12, InvalidArgumentError), (10**12, InvalidArgumentError),
                         (-2**63, InvalidArgumentError), (I, InvalidArgumentError)]:
            before = (p.next_due(), p.trim())
            with self.assertRaises(error):
                p.set_trim(q)
            self.assertEqual((p.next_due(), p.trim()), before)
            self.assertEqual(list(old.all()), old_times)
        self.assertIsNone(p.set_trim(ppt=124))

    def test_cursor_u_trim_allowed_if_floor_fits(self):
        p = Pacer(units_per_second(U, 1))
        old = p.claim(U)
        p.set_trim(1)
        self.assertEqual(p.trim(), 1)
        self.assertEqual(old.time(U-1), 999999999)
        self.assertEqual(p.due(0, 1).count, 0)
        with self.assertRaises(PllOverflowError):
            p.due(1000000000, 1)
