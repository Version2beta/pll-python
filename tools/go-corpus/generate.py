"""Complete offline generator; do not change. Run with PINNED_GO_ROOT argument."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
SHA = '971282632129110794c9d6edd22026e9de2359be'


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def canonical(obj):
    return (json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True)+'\n').encode()


def generate(upstream):
    upstream = Path(upstream).resolve()
    def git(*args):
        return subprocess.check_output(['git', '-C', str(upstream), *args]).decode().strip()
    if git('rev-parse', 'HEAD') != SHA or git('status', '--porcelain', '--untracked-files=no'):
        raise SystemExit('pinned clean upstream required')
    names = git('ls-files', '*.go', 'go.mod').splitlines()
    before = {n: digest(upstream/n) for n in names}
    spec = importlib.util.spec_from_file_location('corpus_cases', HERE/'cases.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cases = module.cases()
    env = dict(os.environ, GOPROXY='off', GOSUMDB='off', GOTOOLCHAIN='local')
    version = subprocess.check_output(['go', 'version'], env=env).decode().strip()
    with tempfile.TemporaryDirectory(prefix='pll-go-corpus-') as d:
        d = Path(d)
        shutil.copyfile(HERE/'main.go', d/'main.go')
        (d/'go.mod').write_text('module corpus\n\ngo 1.23\nrequire github.com/version2beta/pll v0.0.0\nreplace github.com/version2beta/pll => '+str(upstream)+'\n')
        subprocess.run(['go', 'build', '-o', str(d/'harness'), '.'], cwd=d, env=env, check=True)
        outputs = []
        for _ in range(2):
            outputs.append(subprocess.check_output([str(d/'harness')], input=canonical(cases), env=env))
        if outputs[0] != outputs[1]:
            raise AssertionError('non-deterministic Go results')
    if before != {n: digest(upstream/n) for n in names} or git('rev-parse', 'HEAD') != SHA:
        raise AssertionError('upstream changed')
    return canonical(dict(schema='pll-public-api-v1', source=SHA, source_hashes=before,
                          harness_hashes={n:digest(HERE/n) for n in ('main.go','cases.py','generate.py')},
                          go=version, seed='21274', algorithm='LCG32: (1664525*x+1013904223) mod 2**32',
                          command='PYTHONDONTWRITEBYTECODE=1 python3 -B tools/go-corpus/generate.py ../pll',
                          cases=cases, results=json.loads(outputs[0])))


if __name__ == '__main__':
    sys.stdout.buffer.write(generate(sys.argv[1]))
