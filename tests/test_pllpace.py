"""Source-named CLI checks with deterministic clock and writer boundaries."""
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import replace
import io
import threading
import unittest
from unittest.mock import patch
from pll import pllpace as cli


class Clock:
    def __init__(self):
        self.now = 0

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.now += round(seconds * 10**9)


class PllpaceTests(unittest.TestCase):
    def run_trial(self, o=None, write=len, per=1, dur=2_000_000):
        o = o or cli.Options(bps=8000, unit_bytes=1)
        c = Clock()
        s = cli.Sink(write, per, o.unit_bytes)
        return cli.run_trial(o, o.bps, dur, s, clock=c.clock, sleep=c.sleep), s

    def test_options_validation(self):
        good = cli.Options()
        for change in ({'bps': 0}, {'bps': 2**64}, {'unit_bytes': 0},
                       {'unit_bytes': 2**61}, {'seconds': 0}, {'seconds': -1},
                       {'seconds': float('nan')}, {'seconds': float('inf')},
                       {'seconds': .5e-9}, {'seconds': float(cli.IMAX) / 1e9},
                       {'mode': 'bad'}, {'per_datagram': 0}, {'per_datagram': -1},
                       {'per_datagram': cli.IMAX}, {'udp': 'loopback', 'per_datagram': 66},
                       {'mode': 'ticker', 'bps': 8_000_000_001, 'unit_bytes': 1},
                       {'mode': 'ticker', 'bps': 1, 'unit_bytes': 2_000_000_000},
                       {'mode': 'ticker', 'find_max': True},
                       {'find_max': True, 'bps': cli.SEARCH_LIMIT + 1}, {'slack': -1}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                replace(good, **change).validate()
        for change in ({}, {'mode': 'ticker'}, {'udp': 'loopback', 'unit_bytes': 65507},
                       {'find_max': True, 'bps': cli.SEARCH_LIMIT},
                       {'mode': 'ticker', 'bps': 8_000_000_000, 'unit_bytes': 1, 'seconds': 1e-9}):
            self.assertGreater(replace(good, **change).validate(), 0)

    def test_duration_and_flags(self):
        self.assertEqual(cli.duration('1s250us'), 1_000_250_000)
        self.assertEqual(cli.duration('-1.5ms'), -1_500_000)
        self.assertEqual(cli.duration('0'), 0)
        for text in ('', 's', '1', '1d', '--1s', '9223372036854775808ns'):
            with self.assertRaises(cli.argparse.ArgumentTypeError):
                cli.duration(text)
        self.assertEqual(cli.parser().parse_args(['-bps=8', '--seconds', '.01']).bps, 8)
        for b, s, want in ((8_000_000_000, 1, 1), (3, 1, 2_666_666_666), (8, 1, 10**9)):
            self.assertEqual(cli.ticker_period(b, s), want)

    def test_sink_groups_partial_and_errors(self):
        writes = []
        def write(data):
            writes.append(bytes(data))
            return len(data)
        s = cli.Sink(write, 2, 2)
        for payload in (b'ab', b'cd', b'ef'):
            s.unit(payload)
        s.flush()
        s.flush()
        self.assertEqual(writes, [b'abcd', b'ef'])
        self.assertEqual(s.written, 6)
        s.write = lambda data: len(data) - 1
        s.unit(b'gh')
        with self.assertRaisesRegex(OSError, 'short write'):
            s.flush()
        self.assertEqual(s.written, 7)
        self.assertFalse(s.buf)
        def failure(data):
            raise BlockingIOError(11, 'failed', 1)
        s.write = failure
        s.unit(b'ij')
        with self.assertRaises(BlockingIOError):
            s.flush()
        self.assertEqual(s.written, 8)
        self.assertFalse(s.buf)

    def test_trials_flush_and_failure_no_carry(self):
        for mode in ('pacer', 'ticker'):
            o = cli.Options(bps=16000, unit_bytes=2, mode=mode)
            writes = []
            def write(data):
                writes.append(bytes(data))
                return len(data)
            for _ in range(2):
                r, s = self.run_trial(o, write, 1000, 10_000_000)
                self.assertEqual(r.written, r.offered * 2)
                self.assertGreater(r.offered, 0)
                self.assertFalse(s.buf)
                self.assertEqual(r.elapsed, 10_000_000)
            self.assertEqual(len(writes), 2)
            for per in (1, 1000):
                s = cli.Sink(lambda data: 1, per, 2)
                c = Clock()
                with self.assertRaisesRegex(OSError, 'short write'):
                    cli.run_trial(o, o.bps, 10_000_000, s, clock=c.clock, sleep=c.sleep)
                self.assertFalse(s.buf)
                self.assertEqual(s.written, 1)
            c = Clock()
            s = cli.Sink(len, 1000, 2)
            def interrupt(seconds):
                raise KeyboardInterrupt
            with self.assertRaises(KeyboardInterrupt):
                cli.run_trial(o, o.bps, 10_000_000, s, clock=c.clock, sleep=interrupt)
            self.assertFalse(s.buf)
            self.assertEqual(s.written, 0)

    def test_final_flush_time_backlog(self):
        c = Clock()
        def write(data):
            c.now += 20_000_000
            return len(data)
        o = cli.Options(bps=8000, unit_bytes=1)
        s = cli.Sink(write, 1000, 1)
        r = cli.run_trial(o, o.bps, 2_000_000, s, clock=c.clock, sleep=c.sleep)
        self.assertEqual((r.offered, r.written, r.elapsed, r.behind), (2, 2, 22_000_000, 20_000_000))

    def test_low_rate_deadline_and_ticker_drop(self):
        for mode, count in (('pacer', 1), ('ticker', 0)):
            r, _ = self.run_trial(cli.Options(bps=1, unit_bytes=1, mode=mode))
            self.assertEqual((r.offered, r.elapsed), (count, 2_000_000))
        c = Clock()
        def slow(data):
            c.now += 3_000_000
            return len(data)
        o = cli.Options(bps=8000, unit_bytes=1, mode='ticker')
        r = cli.run_trial(o, o.bps, 10_000_000, cli.Sink(slow, 1, 1), clock=c.clock, sleep=c.sleep)
        self.assertEqual((r.offered, r.max_batch, r.behind), (3, 1, 6_000_000))
        self.assertFalse(r.worst)

    def test_pacer_batch_cap_progress_and_quantile(self):
        c = Clock()
        def slow(data):
            if c.now == 0:
                c.now = 1_000_000_000
            return len(data)
        o = cli.Options(bps=80000, unit_bytes=1)
        with redirect_stdout(io.StringIO()) as stdout:
            r = cli.run_trial(o, o.bps, 1_000_000_001, cli.Sink(slow, 1, 1), True, clock=c.clock, sleep=c.sleep)
        self.assertEqual(r.max_batch, 4096)
        self.assertIn('offered units', stdout.getvalue())
        self.assertEqual(cli.quantile(list(range(100)), .99), 98)
        self.assertEqual(cli.quantile([], .99), 0)
        self.assertFalse(cli.Result().sustained(1))
        self.assertTrue(cli.Result(offered=1, behind=1, worst=[1]).sustained(1))
        self.assertFalse(cli.Result(offered=1, worst=[2]).sustained(1))

    def test_rate_search_boundaries(self):
        for lo, hi, limit, want, trials in (
            (1, 2, 1, (1, 2), []), (20, 21, 20, (20, 21), []),
            (1, 8, 2, (2, 3), [4, 2, 3]),
            (1_000_000, 2_000_000, 1_500_000, (1_500_000, 1_562_500), [1_500_000, 1_750_000, 1_625_000, 1_562_500])):
            seen = []
            def trial(rate):
                seen.append(rate)
                self.assertLessEqual(len(seen), len(trials))
                return rate <= limit
            self.assertEqual(cli.bisect_rate(lo, hi, trial), want)
            self.assertEqual(seen, trials)
        self.assertEqual(cli.search_rates(1, lambda b: False), (0, 1))
        seen = []
        self.assertEqual(cli.search_rates(cli.SEARCH_LIMIT, lambda b: seen.append(b) or True), (cli.SEARCH_LIMIT, 0))
        self.assertEqual(seen, [cli.SEARCH_LIMIT])
        self.assertEqual(cli.search_rates(1, lambda b: b <= 2), (2, 3))

    def test_main_validation_errors_and_interrupt(self):
        import importlib
        import sys
        # Warm stdlib imports are permitted; importing the adapter starts no work.
        module = sys.modules.pop('pll.pllpace')
        try:
            with patch.object(cli.time, 'monotonic_ns', side_effect=AssertionError('clock')), patch.object(
                    cli.time, 'sleep', side_effect=AssertionError('sleep')), patch.object(
                    cli.socket, 'socket', side_effect=AssertionError('socket')), patch.object(
                    cli.threading.Thread, 'start', side_effect=AssertionError('thread')), redirect_stdout(io.StringIO()) as stdout:
                importlib.import_module('pll.pllpace')
                self.assertEqual(stdout.getvalue(), '')
        finally:
            sys.modules['pll.pllpace'] = module
            import pll
            pll.pllpace = module
        with patch.object(cli, 'output') as output, redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(['-bps', '0', '-udp', 'loopback']), 1)
            output.assert_not_called()
        with patch.object(cli, 'run_trial', side_effect=KeyboardInterrupt), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(cli.main(['-seconds', '.001']), 130)
        with patch.object(cli, 'run_trial', side_effect=OSError('writer failed')), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as stderr:
            self.assertEqual(cli.main([]), 1)
            self.assertIn('writer failed', stderr.getvalue())

    def test_loopback_cleanup_and_smoke(self):
        before = set(threading.enumerate())
        o = cli.Options(udp='loopback', unit_bytes=1)
        with cli.output(o) as (out, where):
            out.unit(b'x')
            self.assertEqual(out.written, 1)
            self.assertIn('receipt not measured', where)
        self.assertEqual(set(threading.enumerate()), before)
        with self.assertRaises(KeyboardInterrupt):
            with cli.output(o):
                raise KeyboardInterrupt
        self.assertEqual(set(threading.enumerate()), before)
        with redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(cli.main(['-seconds', '.002', '-bps', '8', '-unit-bytes', '1']), 0)
        self.assertIn('1 offered units, 1 writer-accepted bytes', stdout.getvalue())
        # Setup failure closes the receiver even before a worker exists.
        receiver = unittest.mock.Mock()
        receiver.bind.side_effect = OSError('bind failed')
        with patch.object(cli.socket, 'socket', return_value=receiver):
            with self.assertRaisesRegex(OSError, 'bind failed'):
                with cli.output(o):
                    self.fail('setup must fail')
        receiver.close.assert_called_once()
        receiver = unittest.mock.Mock()
        with patch.object(cli.socket, 'socket', return_value=receiver), patch.object(
                cli.threading.Thread, 'start', side_effect=RuntimeError('thread failed')):
            with self.assertRaisesRegex(RuntimeError, 'thread failed'):
                with cli.output(o):
                    self.fail('setup must fail')
        receiver.close.assert_called_once()
        # Receiver failures are surfaced and the thread is joined, not swallowed.
        receiver = unittest.mock.Mock()
        receiver.getsockname.return_value = ('127.0.0.1', 12345)
        receiver.recv.side_effect = OSError('receive failed')
        sender = unittest.mock.Mock()
        with patch.object(cli.socket, 'socket', side_effect=[receiver, sender]), patch.object(
                cli.socket, 'getaddrinfo', return_value=[(2, 2, 17, '', ('127.0.0.1', 12345))]):
            with self.assertRaisesRegex(OSError, 'receive failed'):
                with cli.output(o):
                    pass
        receiver.close.assert_called_once()
        sender.close.assert_called_once()
        self.assertEqual(set(threading.enumerate()), before)
        sender = unittest.mock.Mock()
        sender.connect.side_effect = OSError('connect failed')
        with patch.object(cli.socket, 'socket', return_value=sender), patch.object(
                cli.socket, 'getaddrinfo', return_value=[(2, 2, 17, '', ('127.0.0.1', 12345))]):
            with self.assertRaisesRegex(OSError, 'cannot connect'):
                with cli.output(replace(o, udp='127.0.0.1:12345')):
                    self.fail('connect must fail')
        sender.close.assert_called_once()
