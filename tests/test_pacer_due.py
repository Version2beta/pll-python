"""Exact due comparison, backlog caps, earlier now and newest-keep skipping."""
import unittest
from pll import Pacer, units_per_second, InvalidArgumentError, PllOverflowError
from tests.test_rate import IntSubclass, U
from tests.test_pacer_claim import I


class DueTests(unittest.TestCase):
    def test_exact_neighbors_and_empty_first(self):
        p = Pacer(units_per_second(375000000, 1))
        self.assertEqual(list(p.due(0, 1).all()), [(0, 0)])
        s = p.due(2, 5)
        self.assertEqual((s.first, s.count, list(s.all())), (1, 0, []))
        self.assertEqual(list(p.due(3, 5).all()), [(1, 2)])
        self.assertEqual(list(p.due(8, 5).all()), [(2, 5), (3, 8)])
        self.assertEqual(p.next_due(), (4, 11))

    def test_backlog_earlier_now_and_alias(self):
        p = Pacer(units_per_second(1000, 1))
        alias = p
        self.assertEqual((p.due(10000000, 2).first, p.next_due()), (0, (2, 2000000)))
        self.assertEqual(list(alias.due(5000000, 3).all()), [(2, 2000000), (3, 3000000), (4, 4000000)])
        self.assertEqual(list(p.due(5000000, 8).all()), [(5, 5000000)])
        self.assertEqual(p.due(0, 1).first, 6)

    def test_skip_keep_and_zero(self):
        p = Pacer(units_per_second(1000, 1))
        self.assertEqual(p.skip(10000000, 3), 8)
        self.assertEqual(list(p.due(10000000, 3).all()), [(8, 8000000), (9, 9000000), (10, 10000000)])
        self.assertEqual(p.skip(0, 0), 0)
        self.assertEqual(p.skip(12000000, U), 0)
        self.assertEqual(p.skip(IntSubclass(12000000), IntSubclass(0)), 2)
        self.assertEqual(p.next_due(), (13, 13000000))

    def test_multiphase_validation_atomic(self):
        p = Pacer(units_per_second(1000, 1))
        p.claim(2)
        for method in (p.due, p.skip):
            for args, error in [((-1, "x"), TypeError), ((I+1, False), TypeError),
                                ((True, 1), TypeError), ((0.0, 1), TypeError),
                                ((0, None), TypeError), ((-1, U+1), OverflowError),
                                ((I+1, 0), OverflowError), ((-2**63-1, 1), OverflowError),
                                ((0, -1), OverflowError), ((-1, 1), InvalidArgumentError)]:
                before = (p.next_due(), p.trim())
                with self.subTest(method=method.__name__, args=args), self.assertRaises(error):
                    method(*args)
                self.assertEqual((p.next_due(), p.trim()), before)
        with self.assertRaises(InvalidArgumentError):
            p.due(0, 0)
        self.assertEqual(p.due(now_ns=IntSubclass(2000000), max_count=IntSubclass(1)).count, 1)

    def test_cursor_u_and_floor_fit_boundaries(self):
        p = Pacer(units_per_second(2000000000, U))
        p.claim(1)
        s = p.due(I, 1)
        self.assertEqual((s.first, s.count), (1, 0))
        self.assertEqual(p.skip(I, 0), 0)
        self.assertEqual(p.claim(1).time(0), I)
        p = Pacer(units_per_second(U, 1))
        self.assertEqual(p.skip(1000000000, 0), U)
        self.assertEqual((p.due(0, 1).first, p.due(0, 1).count), (U, 0))
        self.assertEqual(p.skip(0, 0), 0)
        for fn in (lambda: p.due(1000000000, 1), lambda: p.skip(1000000000, U)):
            with self.assertRaises(PllOverflowError):
                fn()
        self.assertEqual(p.due(0, 1).first, U)
        p = Pacer(units_per_second(U, 1))
        huge = p.due(1000000000, U)
        self.assertEqual((huge.first, huge.count), (0, U))
        self.assertEqual(huge.time(U-1), 999999999)
        self.assertEqual(p.due(0, 1).first, U)
