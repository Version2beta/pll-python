"""Explicit real-time CLI adapter; importing this module starts no work."""
import argparse
from contextlib import contextmanager
from dataclasses import dataclass, field
import math
import re
import socket
import sys
import threading
import time

from . import Pacer, PllError, bits_per_second

SEARCH_LIMIT = 1_000_000_000_000
IMAX = 2**63 - 1
U = 2**64 - 1


def duration(text):
    """Parse Go-style signed composite durations, truncating to integer ns."""
    original = text
    sign = -1 if text.startswith('-') else 1
    text = text[1:] if text[:1] in ('+', '-') else text
    if text == '0':
        return 0
    total = 0
    scales = {'ns': 1, 'us': 1000, 'µs': 1000, 'μs': 1000,
              'ms': 10**6, 's': 10**9, 'm': 60*10**9, 'h': 3600*10**9}
    while text:
        match = re.match(r'(\d+(?:\.\d*)?|\.\d+)(ns|us|µs|μs|ms|s|m|h)', text)
        if not match:
            raise argparse.ArgumentTypeError(f'invalid duration: {original}')
        whole, _, fraction = match[1].partition('.')
        total += (int(whole or '0') * scales[match[2]]
                  + int(fraction or '0') * scales[match[2]] // 10**len(fraction))
        text = text[match.end():]
    n = int(total) * sign
    if not -2**63 <= n <= IMAX or not original or original in ('+', '-'):
        raise argparse.ArgumentTypeError('duration outside signed 64-bit ns')
    return n


def ticker_period(bps, size):
    if not 0 < bps <= U or not 0 < size <= U // 8:
        raise ValueError('invalid ticker rate or unit size')
    period = size * 8 * 10**9 // bps
    if not 1 <= period <= IMAX:
        raise ValueError('ticker period must be between 1 ns and the largest time.Duration')
    return period


@dataclass
class Options:
    bps: int = 100_000_000
    unit_bytes: int = 1000
    seconds: float = 10
    mode: str = 'pacer'
    udp: str = ''
    per_datagram: int = 1
    find_max: bool = False
    slack: int = 5_000_000

    def validate(self):
        ns = self.seconds * 10**9
        if not 0 < self.bps <= U:
            raise ValueError('-bps must be positive and fit uint64')
        if not 0 < self.unit_bytes <= min(U // 8, sys.maxsize):
            raise ValueError('-unit-bytes must fit in int and convert to bits without overflow')
        if not math.isfinite(ns) or not 1 <= ns < float(IMAX):
            raise ValueError('-seconds must be finite, positive and representable as a time.Duration')
        if self.mode not in ('pacer', 'ticker'):
            raise ValueError('-mode must be pacer or ticker')
        if not 1 <= self.per_datagram <= sys.maxsize // self.unit_bytes:
            raise ValueError('-per-datagram must be positive and its byte size must fit in int')
        if self.udp and self.per_datagram * self.unit_bytes > 65507:
            raise ValueError('UDP payload must not exceed 65507 bytes')
        if self.find_max and self.mode != 'pacer':
            raise ValueError('-find-max requires -mode pacer')
        if self.find_max and self.bps > SEARCH_LIMIT:
            raise ValueError(f'-bps must not exceed {SEARCH_LIMIT} with -find-max')
        if not 0 <= self.slack <= IMAX:
            raise ValueError('-slack must not be negative or exceed signed 64-bit ns')
        if self.mode == 'ticker':
            ticker_period(self.bps, self.unit_bytes)
        return int(ns)


class Sink:
    def __init__(self, write, per, size):
        self.write, self.per, self.size = write, per, size
        self.buf = bytearray()
        self.written = 0

    def unit(self, payload):
        self.buf.extend(payload)
        if len(self.buf) >= self.per * self.size:
            self.flush()

    def flush(self):
        if not self.buf:
            return
        data = self.buf
        self.buf = bytearray()  # Never retry/carry a failed datagram into another trial.
        try:
            n = self.write(data)
        except OSError as error:
            self.written += getattr(error, 'characters_written', 0)
            raise
        if not isinstance(n, int) or not 0 <= n <= len(data):
            raise OSError('invalid writer byte count')
        self.written += n
        if n != len(data):
            raise OSError('short write')


def quantile(values, fraction):
    return values[int(fraction * (len(values) - 1))] if values else 0


@dataclass
class Result:
    offered: int = 0
    written: int = 0
    wakeups: int = 0
    max_batch: int = 0
    elapsed: int = 0
    behind: int = 0
    worst: list[int] = field(default_factory=list)

    def mbps(self):
        return self.written * 8000 / self.elapsed if self.elapsed > 0 else 0

    def sustained(self, slack):
        return self.offered > 0 and self.behind <= slack and quantile(self.worst, .99) <= slack


def run_trial(o, bps, dur, out, progress=False, *, clock=None, sleep=None):
    clock = clock or time.monotonic_ns
    sleep = sleep or time.sleep
    p = Pacer(bits_per_second(bps, o.unit_bytes * 8)) if o.mode == 'pacer' else None
    period = ticker_period(bps, o.unit_bytes) if p is None else 0
    payload = bytes(o.unit_bytes)
    r = Result()
    start, initial = clock(), out.written
    next_tick, next_report = period, 10**9
    succeeded = False
    try:
        while True:
            now = clock() - start
            if now >= dur:
                break
            if p is None:
                if now < next_tick:
                    sleep(min(next_tick - now, dur - now) / 10**9)
                    continue
                count = 1
                # One event per wake-up; missed periods are dropped, not caught up.
                next_tick = (now // period + 1) * period
            else:
                span = p.due(now, 4096)
                count = span.count
                if count:
                    r.worst.append(now - span.time(0))
            r.wakeups += 1
            for _ in range(count):
                r.offered += 1
                out.unit(payload)
            r.max_batch = max(r.max_batch, count)
            r.elapsed, r.written = clock() - start, out.written - initial
            if progress and now >= next_report:
                print(f'{now / 1e9:6.1f}s  {r.offered:10d} offered units  {r.mbps():9.3f} writer Mbps')
                next_report += 10**9
            at = p.next_due()[1] if p is not None else next_tick
            remaining = min(at, dur) - (clock() - start)
            if remaining > 0:
                sleep(remaining / 10**9)
        out.flush()
        succeeded = True
    finally:
        out.buf.clear()
        r.written = out.written - initial
        r.elapsed = clock() - start
        r.worst.sort()
    if succeeded:
        at = p.next_due()[1] if p is not None else (r.offered + 1) * o.unit_bytes * 8 * 10**9 // bps
        r.behind = max(0, r.elapsed - at)
    return r


def bisect_rate(lo, hi, trial):
    while hi - lo > 1 and hi / lo > 1.05:
        mid = lo + (hi - lo) // 2
        if trial(mid):
            lo = mid
        else:
            hi = mid
    return lo, hi


def search_rates(start, trial):
    lo, hi, rate = 0, 0, start
    while rate <= SEARCH_LIMIT:
        if not trial(rate):
            hi = rate
            break
        lo = rate
        rate *= 2
    return bisect_rate(lo, hi, trial) if lo and hi else (lo, hi)


@contextmanager
def output(o):
    """Own all sockets and the loopback worker, including cancellation paths."""
    receiver = sender = worker = None
    stop = threading.Event()
    errors = []
    try:
        if not o.udp:
            yield Sink(len, 1, o.unit_bytes), 'discarded'
            return
        address = o.udp
        if address == 'loopback':
            receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            receiver.bind(('127.0.0.1', 0))
            receiver.settimeout(.05)
            def receive():
                try:
                    while not stop.is_set():
                        try:
                            receiver.recv(65536)
                        except socket.timeout:
                            pass
                except OSError as error:
                    errors.append(error)
            worker = threading.Thread(target=receive, name='pllpace-loopback')
            worker.start()
            host, port = receiver.getsockname()
            address = f'{host}:{port}'
        else:
            host, port = address.rsplit(':', 1)
            host = host.strip('[]')
            port = int(port)
        for family, kind, proto, _, target in socket.getaddrinfo(host, port, type=socket.SOCK_DGRAM):
            try:
                sender = socket.socket(family, kind, proto)
                sender.connect(target)
                break
            except OSError:
                if sender is not None:
                    sender.close()
                sender = None
        if sender is None:
            raise OSError('cannot connect UDP destination')
        def write(data):
            if errors:
                raise errors[0]
            return sender.send(data)
        yield Sink(write, o.per_datagram, o.unit_bytes), f'UDP writes to {address}, up to {o.per_datagram} units per datagram; receipt not measured'
        if errors:
            raise errors[0]
    finally:
        stop.set()
        if sender is not None:
            sender.close()
        if worker is not None and worker.ident is not None:
            worker.join()
        if receiver is not None:
            receiver.close()
    if errors:
        raise errors[0]


def parser():
    p = argparse.ArgumentParser(description='Real-time pll pacing; writer acceptance is not UDP receipt.', allow_abbrev=False)
    for name, default, kind, help_text in (
        ('bps', 100_000_000, int, 'target bits/s; starting rate with -find-max'),
        ('unit-bytes', 1000, int, 'bytes per unit'),
        ('seconds', 10, float, 'seconds per trial'),
        ('mode', 'pacer', str, 'pacer or ticker (one event per wake-up, missed periods dropped)'),
        ('udp', '', str, 'host:port or loopback; default discard'),
        ('per-datagram', 1, int, 'units per UDP datagram'),
        ('slack', 5_000_000, duration, 'search timing allowance, e.g. 5ms or 1s250us')):
        p.add_argument('-' + name, '--' + name, default=default, type=kind, help=help_text)
    p.add_argument('-find-max', '--find-max', action='store_true', help='bounded exponential/binary sustained-rate search')
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    o = Options(**vars(args))
    try:
        dur = o.validate()
        with output(o) as (out, where):
            if o.find_max:
                print(f'searching for the highest sustained rate: {o.unit_bytes}-byte units, {dur / 1e9:g}s per trial, pass within {o.slack / 1e6:g}ms ({where})')
                print('target Mbps  units/s  writer Mbps  behind (ms)  late p99 (ms)  verdict')
                def trial(bps):
                    r = run_trial(o, bps, dur, out)
                    ok = r.sustained(o.slack)
                    print(f'{bps / 1e6:.3f}  {bps / (o.unit_bytes * 8):.0f}  {r.mbps():.3f}  {r.behind / 1e6:.3f}  {quantile(r.worst, .99) / 1e6:.3f}  {"pass" if ok else "FAIL"}')
                    return ok
                lo, hi = search_rates(o.bps, trial)
                if not lo:
                    print(f'the starting rate, {o.bps / 1e6:.3f} Mbps, did not pass')
                elif not hi:
                    print(f'every rate up to {lo / 1e6:g} Mbps passed')
                else:
                    print(f'highest rate sustained: {lo / 1e6:.1f} Mbps ({lo / (o.unit_bytes * 8):.0f} units/s); {hi / 1e6:.1f} Mbps failed')
                    if hi / lo > 1.05:
                        print(f'search stopped at integer bit-rate resolution: {lo} bps passed, {hi} bps failed (range still wider than 5%)')
                return 0
            ups = o.bps / (o.unit_bytes * 8)
            print(f'target  {o.bps / 1e6:.3f} Mbps = {ups:.2f} units/s of {o.unit_bytes} bytes, one every {1e6 / ups:.2f} µs ({o.mode}, {where})')
            r = run_trial(o, o.bps, dur, out, True)
            print(f'result  {r.offered} offered units, {r.written} writer-accepted bytes in {r.elapsed / 1e9:.3f}s = {r.mbps():.3f} writer Mbps (target {o.bps / 1e6:.3f}), {r.behind / 1e6:.3f}ms behind schedule at the end')
            print(f'        {r.wakeups} wake-ups, {r.offered / max(r.wakeups, 1):.1f} units per wake-up on average, {r.max_batch} at most')
            if r.worst:
                print(f'        oldest unit at each wake-up, lateness: median {quantile(r.worst, .5) / 1e6:.3f}ms, 99th {quantile(r.worst, .99) / 1e6:.3f}ms, max {quantile(r.worst, 1) / 1e6:.3f}ms')
        return 0
    except KeyboardInterrupt:
        print('pllpace: interrupted', file=sys.stderr)
        return 130
    except (ValueError, OSError, OverflowError, MemoryError, RuntimeError, PllError) as error:
        print(f'pllpace: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
