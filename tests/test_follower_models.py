"""Independent moderate absolute-coordinate model and Decimal extreme-gain fixtures."""
import math
import random
import sys
import unittest
from decimal import Decimal, localcontext
from tests.test_follower import make
from pll import Status


def nearest(v):
    return int(Decimal.from_float(v).to_integral_value(rounding='ROUND_HALF_UP'))


class ModelTests(unittest.TestCase):
    def test_moderate_independent_model(self):
        # Fixture-local tolerances: error/local/remote <=1 unit, offset <=1e-12,
        # jitter <=2ns. Status comparisons remain exact. Absolute coordinates
        # deliberately differ from production's integer+fraction representation.
        rng = random.Random(9712826)
        f = make(1000, outlier_threshold_ns=1000000, lock_threshold_ns=1000000)
        f.observe(0, 0)
        anchor, tick, ref, y, m = 0., 0, 0, 0., None
        for k in range(1, 501):
            r = k*10
            l = k*10000000 + k*37 + rng.randrange(-30, 31)
            pred = anchor + (r-tick)*1000000/(1+y)
            error = l-pred
            dt = (l-ref)*1e-9
            a = min(.5, 2*math.pi*.1*dt)
            phase_gain = min(1., math.sqrt(2)*a)
            y = min(.0005, max(-.0005, y-a*a*error/dt*1e-9))
            anchor = pred+phase_gain*error
            tick, ref = r, l
            m = error*error if m is None else (15*m+error*error)/16
            obs = f.observe(l, r)
            self.assertEqual(obs.status, Status.ACCEPTED)
            self.assertLessEqual(abs(obs.error_ns-nearest(error)), 1)
            self.assertLessEqual(abs(f.local(r+3)-nearest(anchor+3000000/(1+y))), 1)
            self.assertLessEqual(abs(f.remote(l)-nearest(tick+(l-anchor)*(1+y)/1000000)), 1)
            self.assertLessEqual(abs(f.offset()-y), 1e-12)
            if k > 1:
                self.assertLessEqual(abs(f.jitter()-nearest(math.sqrt(m))), 2)

    def test_decimal_extreme_finite_gains(self):
        # Source follower_test.go TestFollowerExtremeFiniteGains matrix ONLY:
        # local <=1ns, absolute offset <=1e-20. Decimal >=256-bit precision.
        with localcontext() as ctx:
            ctx.prec = 110
            D = Decimal.from_float
            for bandwidth in (math.ulp(0.), 1e-300, .1, sys.float_info.max):
                for damping in (math.ulp(0.), math.sqrt(2)/2, sys.float_info.max):
                    for phase in (0, 100, -100):
                        with self.subTest(bandwidth=bandwidth, damping=damping, phase=phase):
                            f = make(1000, bandwidth_hz=bandwidth, damping=damping)
                            f.observe(0, 0)
                            l = 1000000000+phase
                            obs = f.observe(l, 1000)
                            self.assertEqual((obs.status, obs.error_ns), (Status.ACCEPTED, phase))
                            dt = D(l/1e9)
                            x = min(Decimal('.5'), D(2*math.pi)*D(bandwidth)*dt)
                            kp = min(Decimal(1), 2*D(damping)*x)
                            wanted = 1000000000+nearest(float(kp)*phase)
                            self.assertLessEqual(abs(f.local(1000)-wanted), 1)
                            wanted_y = float(x*x/dt)*(-phase/1e9)
                            self.assertLessEqual(abs(f.offset()-wanted_y), 1e-20)
                            self.assertTrue(math.isfinite(f.offset()))

    def test_offset_and_jitter_saturation(self):
        from tests.test_follower import HI
        for sign in (-1, 1):
            f = make(1000, bandwidth_hz=1e9, damping=1., max_offset_ppm=999999.9999999999,
                     outlier_threshold_ns=HI)
            f.observe(0, 0)
            # Force opposite rate clamps while preserving ordered local/remote.
            if sign < 0:
                for k in range(1, 7):
                    f.observe(k*10**12, k)
            else:
                f.observe(1, 10**9)
            self.assertEqual(f.trim(), sign*999999999999)
        f = make(bandwidth_hz=5e-324, outlier_threshold_ns=HI)
        f.observe(0, -2**63)
        for r in (0, 1):
            self.assertEqual(f.observe(0, r).status, Status.ACCEPTED)
        self.assertEqual(f.jitter(), HI)
