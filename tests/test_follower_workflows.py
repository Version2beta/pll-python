"""All follower README fences, cross-pacer retained spans and effects traps."""
import re
import subprocess
import sys
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
from pll import Follower, Pacer, default_follower_config, units_per_second


class WorkflowTests(unittest.TestCase):
    def test_readme_and_cross_pacer(self):
        text = Path('README.md').read_text()
        code = re.search(r'```python\n(.*?)\n```', text[text.index('### Cross-module success'):], re.S)
        self.assertIsNotNone(code)
        exec(compile(code.group(1), 'README follower example', 'exec'), {})
        p = Pacer(units_per_second(1000, 1))
        old = p.claim(2)
        f = Follower(default_follower_config(units_per_second(1000, 1)))
        f.observe(0, 0)
        f.observe(1000010000, 1000)
        p.set_trim(f.trim())
        self.assertEqual(list(old.all()), [(0, 0), (1, 1000000)])
        p.claim(2)
        self.assertEqual(old.time(1), 1000000)

    def test_import_and_runtime_effects(self):
        # Fresh import: audit prohibited non-import effects; loader file reads
        # are necessarily permitted. This is representative, not a sandbox.
        code = '''import sys
seen=[]
def audit(event,args):
 if event.startswith(('socket.', 'subprocess.', 'os.system', 'os.fork')):
  raise AssertionError(event)
sys.addaudithook(audit)
import pll
assert len(pll.__all__)==18
print('PASS FRESH IMPORT')
'''
        p = subprocess.run([sys.executable, '-B', '-c', code], text=True, capture_output=True)
        self.assertEqual((p.returncode, p.stdout.strip()), (0, 'PASS FRESH IMPORT'), p.stderr)
        forbidden = ['builtins.open', 'os.open', 'os.getenv', 'os.system', 'os.fork',
                     'socket.socket', 'subprocess.Popen', 'time.time', 'time.time_ns',
                     'time.monotonic', 'time.monotonic_ns', 'time.sleep',
                     'threading.Thread.start', 'os._Environ.__getitem__']
        with ExitStack() as stack:
            for target in forbidden:
                stack.enter_context(patch(target, side_effect=AssertionError(target), create=True))
            f = Follower(default_follower_config(units_per_second(1000, 1)))
            f.observe(0, 0)
            for k in range(1, 10):
                f.observe(k*1000000, k)
            f.local(12), f.remote(12), f.state(12), f.trim(), f.offset(), f.jitter()
            f.reset()
