"""Representative no-effect and source-tree nonmutation observations, not a proof."""
import builtins
from contextlib import ExitStack
import hashlib
import os
from pathlib import Path
import socket
import subprocess
import threading
import time
import unittest
from unittest.mock import patch
from pll import Pacer, Span, units_per_second, bits_per_second


def snapshot():
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ("pll", "tests", "scripts", "fixtures", "docs")
            for p in Path(folder).rglob("*") if p.is_file()}


class EffectsTests(unittest.TestCase):
    def test_no_runtime_effects_and_source_mutation(self):
        before = snapshot()
        forbidden = ["builtins.open", "os.open", "os.getenv", "os.system", "os.fork",
                     "os._exit", "socket.socket", "subprocess.Popen", "time.time",
                     "time.time_ns", "time.monotonic", "time.monotonic_ns",
                     "time.perf_counter", "time.perf_counter_ns", "time.sleep",
                     "threading.Thread.start", "os._Environ.__getitem__"]
        # Resolve module imports before trapping runtime operations.
        import pll._span
        with ExitStack() as stack:
            for target in forbidden:
                stack.enter_context(patch(target, side_effect=AssertionError(target), create=True))
            r = bits_per_second(50000000, 8)
            p = Pacer(r)
            s = p.claim(1500)
            self.assertEqual(s.time(1499), 239840)
            self.assertEqual(next(s.all()), (0, 0))
            self.assertEqual(p.next_due(), (1500, 240000))
            p.set_trim(5)
            p.due(1000000, 3)
            p.skip(1000000, 1)
            self.assertEqual(p.trim(), 5)
            self.assertEqual(list(Span().all()), [])
            self.assertEqual(str(units_per_second(1, 1)), "1 units/s")
        self.assertEqual(snapshot(), before)
