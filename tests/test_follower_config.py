"""README config field order, strict byte enums and frozen public seams."""
import math
import unittest
from dataclasses import fields, replace, FrozenInstanceError
import pll
from pll import (Follower, FollowerConfig, Observation, Status, State, Rate,
                 ConfigError, default_follower_config, units_per_second)


class ConfigTests(unittest.TestCase):
    def test_defaults_values_enums_errors(self):
        c = default_follower_config(Rate())
        self.assertEqual(tuple(getattr(c, f.name) for f in fields(c)),
                         (Rate(), .1, math.sqrt(2)/2, 500., 0, 5000000, 3, 100000, 8, 5000000000))
        with self.assertRaises(TypeError):
            FollowerConfig()
        for value in (c, Observation(Status.PENDING, 0)):
            with self.assertRaises((FrozenInstanceError, AttributeError)):
                setattr(value, fields(value)[0].name, None)
        for cls in (Status, State):
            for v in (True, False, 1., '1', None):
                with self.assertRaises(TypeError):
                    cls(v)
            for v in (-1, 256, 2**64):
                with self.assertRaises(ValueError):
                    cls(v)
            for v in range(256):
                self.assertEqual(int(cls(v)), v)
            self.assertEqual(str(cls(9)), f'{cls.__name__}(9)')
        self.assertEqual([str(s) for s in Status], ['anchored', 'accepted', 'pending', 'rejected', 'stepped'])
        self.assertEqual([str(s) for s in State], ['acquiring', 'locked', 'holdover'])
        for name, message in [('OrderError', 'pll: reading out of order'),
                              ('NotAnchoredError', 'pll: follower has no reading yet')]:
            err = getattr(pll, name)()
            self.assertIsInstance(err, pll.PllError)
            self.assertEqual(str(err), message)
        e = ConfigError('damping', 'must be finite and > 0')
        self.assertEqual((e.code, e.field, e.reason, str(e)), ('config', 'damping', 'must be finite and > 0',
                         'pll: FollowerConfig.damping must be finite and > 0'))
        for key in ('field', 'reason'):
            with self.assertRaises(AttributeError):
                setattr(e, key, 'changed')

    def test_field_by_field_validation(self):
        c = default_follower_config(units_per_second(1000, 1))
        cases = [('nominal', Rate(), 'must be a valid Rate'),
                 ('bandwidth_hz', 0., 'must be finite and > 0'),
                 ('damping', float('nan'), 'must be finite and > 0'),
                 ('max_offset_ppm', 1000000., 'must be finite, > 0 and < 1000000'),
                 ('window_ns', -1, 'must be >= 0'), ('outlier_threshold_ns', 0, 'must be > 0'),
                 ('step_after', 0, 'must be >= 1'), ('lock_threshold_ns', -1, 'must be >= 0'),
                 ('lock_count', 0, 'must be >= 1'), ('holdover_after_ns', 0, 'must be > 0')]
        for index, (name, bad, reason) in enumerate(cases):
            changes = {f.name: None for f in fields(c)[index+1:]}
            changes[name] = bad
            with self.subTest(name=name), self.assertRaises(ConfigError) as ctx:
                Follower(replace(c, **changes))
            self.assertEqual((ctx.exception.field, ctx.exception.reason), (name, reason))
        for f in fields(c):
            for bad in (True, None, '1', 1 if f.type is float else 1.0):
                with self.subTest(field=f.name, bad=bad), self.assertRaises(TypeError):
                    Follower(replace(c, **{f.name: bad}))
            if f.type is int:
                for bad in (-2**63-1, 2**63):
                    with self.assertRaises(OverflowError):
                        Follower(replace(c, **{f.name: bad}))
        for name in ('bandwidth_hz', 'damping', 'max_offset_ppm'):
            for bad in (float('inf'), -float('inf'), float('nan'), -1., 0.):
                with self.assertRaises(ConfigError):
                    Follower(replace(c, **{name: bad}))
        class I(int):
            pass
        class F(float):
            pass
        Follower(replace(c, window_ns=I(0), damping=F(1.)))
        with self.assertRaises(TypeError):
            Follower(None)
        with self.assertRaises(ConfigError):
            Follower(replace(c, window_ns=-1, lock_count=2**63))
