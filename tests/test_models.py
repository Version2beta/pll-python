"""Independent Fraction oracle with binary-search due and public-only comparisons."""
import random
import unittest
from fractions import Fraction
from pll import Pacer, units_per_second, PllOverflowError
from tests.test_rate import U
from tests.test_pacer_claim import I


class FractionModel:
    def __init__(self, num, den):
        self.num, self.den = num, den
        self.cursor = self.start = self.anchor = self.q = 0

    def at(self, slot):
        return Fraction(self.anchor) + Fraction((slot-self.start)*self.den*10**21,
                                                self.num*(10**12+self.q))

    def due_count(self, now):
        # Search the slot domain, not production's inverse period calculation.
        lo, hi = self.cursor, U+1
        while lo < hi:
            mid = (lo+hi)//2
            if self.at(mid) <= now:
                lo = mid+1
            else:
                hi = mid
        if self.cursor == U and self.at(U) <= now:
            raise PllOverflowError()
        return max(0, min(lo, U)-self.cursor)

    def apply(self, name, *args):
        if name == "next_due":
            t = self.at(self.cursor)
            value = -(-t.numerator//t.denominator)
            if self.cursor == U or value > I:
                raise PllOverflowError()
            return self.cursor, value
        if name == "set_trim":
            q, = args
            if q != self.q:
                anchor = self.at(self.cursor).__floor__()
                if anchor > I:
                    raise PllOverflowError()
                self.anchor, self.start, self.q = anchor, self.cursor, q
            return None
        if name == "claim":
            n, = args
            if n > U-self.cursor or self.at(self.cursor+n-1).__floor__() > I:
                raise PllOverflowError()
        elif name == "due":
            n = min(self.due_count(args[0]), args[1])
        else:
            count = self.due_count(args[0])
            n = max(0, count-args[1])
        first = self.cursor
        times = [self.at(first+i).__floor__() for i in range(n)] if name != "skip" else None
        self.cursor += n
        return n if name == "skip" else (first, n, times)


def observed(p, name, args):
    try:
        result = getattr(p, name)(*args)
        if name in ("due", "claim"):
            result = result.first, result.count, [result.time(i) for i in range(result.count)]
        return "ok", result
    except PllOverflowError:
        return "overflow", None


class ModelTests(unittest.TestCase):
    def test_seeded_sequences(self):
        randomizer = random.Random(9712826)
        rates = [(48000, 1), (30000, 1001), (375000000, 1), (U, U-1),
                 (U, 1), (1, U), (4294967295, 4294967291), (2000000000, U)]
        for num, den in rates:
            p, model = Pacer(units_per_second(num, den)), FractionModel(num, den)
            retained = []
            for step in range(160):
                name = randomizer.choice(["due", "claim", "skip", "next_due", "set_trim"])
                if name in ("due", "skip"):
                    args = (randomizer.choice([0, 1, 2, 3, 10000000, I, randomizer.randrange(10**12)]),
                            randomizer.randrange(1, 8) if name == "due" else randomizer.randrange(8))
                elif name == "claim":
                    args = (randomizer.randrange(1, 8),)
                elif name == "set_trim":
                    args = (randomizer.choice([-10**12+1, -500000000000, 0, 50000000,
                                               10**12-1, model.q]),)
                else:
                    args = ()
                before = (model.cursor, model.q)
                try:
                    expected = "ok", model.apply(name, *args)
                except PllOverflowError:
                    expected = "overflow", None
                    self.assertEqual((model.cursor, model.q), before)
                actual = observed(p, name, args)
                with self.subTest(rate=(num, den), step=step, name=name, args=args):
                    self.assertEqual(actual, expected)
                    self.assertEqual(p.trim(), model.q)
                    self.assertEqual(observed(p, "next_due", ()), self.model_query(model))
                    empty = p.due(0, 1)
                    # This may issue slot zero before later work; mirror it.
                    expected_empty = model.apply("due", 0, 1)
                    self.assertEqual((empty.first, empty.count,
                                      [empty.time(i) for i in range(empty.count)]), expected_empty)
                if step % 31 == 0 and model.cursor < U:
                    # Retain actual results with independent issuance-time expectations.
                    expected_span = self.try_claim_model(model)
                    try:
                        span = p.claim(1)
                    except PllOverflowError:
                        self.assertIsNone(expected_span)
                    else:
                        self.assertIsNotNone(expected_span)
                        retained.append((span, expected_span))
                for span, expected_span in retained:
                    self.assertEqual((span.first, span.count, [span.time(i) for i in range(span.count)]),
                                     expected_span)

    @staticmethod
    def model_query(model):
        try:
            return "ok", model.apply("next_due")
        except PllOverflowError:
            return "overflow", None

    @staticmethod
    def try_claim_model(model):
        try:
            return model.apply("claim", 1)
        except PllOverflowError:
            return None

    def test_due_neighbors_against_formula(self):
        for n, d in [(375000000, 1), (48000, 1), (U, 1), (U, U-1)]:
            for slot in range(1, 12):
                t = Fraction(slot*d*10**9, n)
                ceiling = -(-t.numerator//t.denominator)
                for now in (ceiling-1, ceiling):
                    p = Pacer(units_per_second(n, d))
                    p.claim(slot)
                    span = p.due(now, 1)
                    self.assertEqual(span.count, int(t <= now))
                    self.assertEqual(span.first, slot)
