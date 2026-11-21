"""Immutable self-contained spans, indexing, floor and observable laziness."""
import gc
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from pll import Pacer, Span, units_per_second
from tests.test_rate import IntSubclass, U


class SpanTests(unittest.TestCase):
    def test_hand_fixtures(self):
        data = json.loads(Path("fixtures/pacing.json").read_text())
        self.assertEqual(data["source_revision"], "971282632129110794c9d6edd22026e9de2359be")
        for case in data["cases"]:
            p = Pacer(units_per_second(int(case["num"]), int(case["den"])))
            s = p.claim(int(case["count"]))
            self.assertEqual([s.time(i) for i in range(s.count)], list(map(int, case["times"])))
            self.assertEqual(list(s.all()), list(enumerate(map(int, case["times"]))))

    def test_empty_and_index_rules(self):
        for s in (Span(), Pacer(units_per_second(1, 1)).claim(2)):
            for bad in (-U-1, -1, s.count, U+1):
                with self.assertRaises(IndexError):
                    s.time(bad)
            for bad in (True, False, 0.0, None, "0"):
                with self.assertRaises(TypeError):
                    s.time(bad)
        self.assertEqual((Span().first, Span().count, list(Span().all())), (0, 0, []))
        s = Pacer(units_per_second(1, 1)).claim(2)
        self.assertEqual(s.time(IntSubclass(1)), 1000000000)
        with self.assertRaises(TypeError):
            Span(0, 2)

    def test_immutable_and_outlives_controller(self):
        p = Pacer(units_per_second(3, 1))
        s = p.claim(4)
        for name in ("first", "count"):
            with self.assertRaises(AttributeError):
                setattr(s, name, 9)
            with self.assertRaises(AttributeError):
                delattr(s, name)
        del p
        gc.collect()
        self.assertEqual(list(s.all()), [(0, 0), (1, 333333333), (2, 666666666), (3, 1000000000)])

    def test_lazy_fresh_iterators(self):
        s = Pacer(units_per_second(U, 1)).claim(U)
        observed = []
        original = Span.time

        def counted(value, index):
            observed.append(index)
            if len(observed) > 4:
                raise AssertionError("iterator computed unrequested items")
            return original(value, index)

        with patch.object(Span, "time", counted):
            a, b = s.all(), s.all()
            self.assertIs(iter(a), a)
            self.assertIs(iter(b), b)
            self.assertEqual(observed, [])
            self.assertEqual(next(a), (0, 0))
            self.assertEqual(observed, [0])
            self.assertEqual(next(a), (1, 0))
            self.assertEqual(observed, [0, 1])
            self.assertEqual(next(b), (0, 0))
            self.assertEqual(observed, [0, 1, 0])
        self.assertEqual(s.time(U-1), 999999999)
