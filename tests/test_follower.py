"""Exact README boundary/classification tests; no numerical classification tolerance."""
import unittest
from dataclasses import replace
from pll import (Follower, Status, State, Observation, OrderError, NotAnchoredError,
                 PllOverflowError, default_follower_config, units_per_second)

LO, HI = -2**63, 2**63-1


def make(rate=10**9, **kw):
    return Follower(replace(default_follower_config(units_per_second(rate, 1)), **kw))


def view(f):
    return (f.offset(), f.trim(), f.jitter(), tuple(f.state(t) for t in (LO, 0, HI)),
            tuple(f.local(r) for r in (-1, 0, 1)))


class MappingTests(unittest.TestCase):
    def test_anchor_ties_large_origins_and_wide_cancellation(self):
        f = make(2*10**9)
        for fn in (f.local, f.remote):
            with self.assertRaises(NotAnchoredError):
                fn(0)
        self.assertEqual((f.offset(), f.trim(), f.jitter(), f.state(0)), (0., 0, 0, State.ACQUIRING))
        for origin in (1, -1, 2**53+1, -(2**53+1)):
            f.reset()
            self.assertEqual(f.observe(origin, 0), Observation(Status.ANCHORED, 0))
            self.assertEqual((f.local(-1), f.local(0), f.local(1)), (origin-1, origin, origin+1))
            self.assertEqual(f.remote(origin), 0)
        f = make()
        f.observe(LO, LO)
        self.assertEqual(f.local(0), 0)
        self.assertEqual(f.remote(0), 0)
        f = make()
        f.observe(HI, HI)
        self.assertEqual(f.local(-1025), -2049)  # negative wide displacement cancellation
        f = make()
        f.observe(HI, 0)
        with self.assertRaises(PllOverflowError):
            f.local(1)
        self.assertEqual(f.local(0), HI)
        f = make(500000000)
        f.observe(0, 1)
        self.assertEqual((f.remote(-1), f.remote(1)), (0, 2))

    def test_validation_order_and_failure_retry(self):
        f = make()
        f.observe(0, 0)
        before = view(f)
        for args, exc in [((-1, 'bad'), TypeError), ((HI+1, False), TypeError),
                          ((-1, HI+1), OverflowError), ((-1, 1), OrderError),
                          ((0, 0), OrderError), ((True, 1), TypeError)]:
            with self.assertRaises(exc):
                f.observe(*args)
            self.assertEqual(view(f), before)
        for fn in (f.local, f.remote, f.state):
            for bad, exc in [(True, TypeError), (1., TypeError), (HI+1, OverflowError)]:
                with self.assertRaises(exc):
                    fn(bad)
        self.assertEqual(f.observe(0, 1).status, Status.ACCEPTED)  # dt=0, no mapping update
        self.assertEqual(f.local(1), 1)


class LoopTests(unittest.TestCase):
    def test_lock_jitter_holdover_reset(self):
        f = make(1000)
        f.observe(0, 0)
        for k in range(1, 9):
            self.assertEqual(f.observe(k*10000000, k*10), Observation(Status.ACCEPTED, 0))
            self.assertEqual(f.state(k*10000000), State.LOCKED if k == 8 else State.ACQUIRING)
        self.assertEqual((f.offset(), f.trim(), f.jitter()), (0., 0, 0))
        self.assertEqual(f.state(5080000000), State.LOCKED)
        self.assertEqual(f.state(5080000001), State.HOLDOVER)
        f.reset()
        with self.assertRaises(NotAnchoredError):
            f.local(0)
        self.assertEqual(f.observe(-5, -5).status, Status.ANCHORED)
        f = make(bandwidth_hz=5e-324, lock_threshold_ns=2, lock_count=2)
        f.observe(0, 0)
        self.assertEqual(f.observe(0, 2).error_ns, -2)
        self.assertEqual(f.jitter(), 0)
        f.observe(0, 4)
        self.assertEqual(f.jitter(), 2)  # sqrt(4+(16-4)/16)
        self.assertEqual(f.state(0), State.ACQUIRING)
        f = make(holdover_after_ns=HI)
        f.observe(LO, 0)
        self.assertEqual(f.state(-1), State.ACQUIRING)
        self.assertEqual(f.state(0), State.HOLDOVER)

    def test_threshold_outlier_first_reference_step_and_order(self):
        f = make(outlier_threshold_ns=10, step_after=3, bandwidth_hz=5e-324)
        f.observe(0, 0)
        self.assertEqual(f.observe(0, 10).status, Status.ACCEPTED)  # equality is inlier
        self.assertEqual(f.observe(0, 20).status, Status.REJECTED)
        self.assertEqual(f.observe(0, 30).status, Status.REJECTED)  # agreement equality
        self.assertEqual(f.observe(0, 40).status, Status.REJECTED)  # resets: not relative to previous
        self.assertEqual(f.observe(0, 41).status, Status.REJECTED)
        self.assertEqual(f.observe(0, 42).status, Status.STEPPED)
        self.assertEqual((f.local(42), f.offset(), f.jitter(), f.state(0)), (0, 0., 0, State.ACQUIRING))
        with self.assertRaises(OrderError):
            f.observe(0, 42)
        f = make(1000, bandwidth_hz=1., damping=1.)
        f.observe(0, 0)
        f.observe(1001000000, 1000)
        y = f.offset()
        for l, r in [(1011000000, 3010), (1021000000, 3020), (1031000000, 3030)]:
            obs = f.observe(l, r)
        self.assertEqual(obs.status, Status.STEPPED)
        self.assertEqual(f.offset(), y)
        self.assertEqual(f.local(3030), 1031000000)

    def test_saturation_and_atomic_overflow_retry(self):
        f = make(1)
        f.observe(0, LO)
        self.assertEqual(f.observe(1, HI).error_ns, LO)
        f = make(1, outlier_threshold_ns=HI, bandwidth_hz=5e-324)
        f.observe(LO, 0)
        self.assertEqual(f.observe(HI, 1), Observation(Status.REJECTED, HI))
        # Exact elapsed near signed boundary rounds the prediction to 2**63.
        f = make(bandwidth_hz=5e-324, outlier_threshold_ns=HI)
        f.observe(HI-1024, 0)
        with self.assertRaises(PllOverflowError):
            f.observe(HI, 2048)
        self.assertEqual(f.local(0), HI-1024)
        self.assertEqual(f.observe(HI, 512).status, Status.ACCEPTED)
        self.assertEqual(f.local(512), HI-512)


class WindowTests(unittest.TestCase):
    def test_half_open_signed_minimum_tie_and_last_accepted(self):
        f = make(window_ns=4, bandwidth_hz=5e-324, holdover_after_ns=10)
        f.observe(0, 0)
        for l, r in [(1, 1), (2, 3), (3, 4), (4, 4+1)]:
            self.assertEqual(f.observe(l, r), Observation(Status.PENDING, 0))
        self.assertEqual(f.observe(5, 6), Observation(Status.ACCEPTED, -1))
        self.assertEqual(f.state(12), State.ACQUIRING)  # tie retains candidate local=2
        self.assertEqual(f.state(13), State.HOLDOVER)
        with self.assertRaises(OrderError):
            f.observe(5, 6)
        f = make(window_ns=HI)
        f.observe(LO, 0)
        f.observe(LO+1, 1)
        self.assertEqual(f.observe(0, 2).status, Status.ACCEPTED)

    def test_postflush_mapping_and_failed_flush_retry(self):
        f = make(window_ns=10, bandwidth_hz=1e9, damping=1., outlier_threshold_ns=100)
        f.observe(0, 0)
        f.observe(10, 1)
        self.assertEqual(f.observe(20, 2).error_ns, 9)
        # New candidate is evaluated after phase correction, not old mapping.
        first = f.local(2)
        expected = 20-first
        self.assertEqual(f.observe(30, 3).error_ns, expected)
        f = make(window_ns=1, bandwidth_hz=5e-324, outlier_threshold_ns=HI)
        f.observe(HI-1024, 0)
        f.observe(HI-1, 2048)
        for _ in range(2):
            with self.assertRaises(PllOverflowError):
                f.observe(HI, 2049)
            self.assertEqual(f.local(0), HI-1024)
        # A failed boundary call must not consume order coordinates; an earlier
        # valid same-window reading can still replace the pending candidate.
        self.assertEqual(f.observe(HI-1, 2049).status, Status.PENDING)
        f.reset()
        self.assertEqual(f.observe(0, 0).status, Status.ANCHORED)
        self.assertEqual(f.observe(1, 1).status, Status.PENDING)
