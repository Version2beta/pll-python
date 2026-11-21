"""Complete shared-domain schema and canonical artifact guard; do not change."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INT = re.compile(r'(0|-?[1-9][0-9]*)\Z')
HEX = re.compile(r'[0-9a-f]{16}\Z')
SHA256 = re.compile(r'[0-9a-f]{64}\Z')
ARITY = dict(claim=1, due=2, skip=2, next_due=0, set_trim=1, pacer_trim=0,
             time=2, all=2, observe=2, local=1, remote=1, offset=0, trim=0,
             jitter=0, state=1, reset=0)
PACER = {'claim', 'due', 'skip', 'next_due', 'set_trim', 'pacer_trim', 'time', 'all'}
FLOATS = {'Bandwidth', 'Damping', 'MaxOffsetPPM'}
REASONS = dict(Nominal='must be a valid Rate', Bandwidth='must be finite and > 0',
               Damping='must be finite and > 0', MaxOffsetPPM='must be finite, > 0 and < 1000000',
               Window='must be >= 0', OutlierThreshold='must be > 0', StepAfter='must be >= 1',
               LockThreshold='must be >= 0', LockCount='must be >= 1', HoldoverAfter='must be > 0')
FIELDS = set(REASONS)
HARNESS = {'main.go', 'cases.py', 'generate.py'}
U, LO, HI = 2**64-1, -2**63, 2**63-1
# Fingerprint of the complete tracked Go-source manifest at the approved revision.
SOURCE_MANIFEST_SHA256 = '4b87acc008b57137bb77dc3f9c6838c96f423395739c651340293aa58d381227'


def canonical(obj):
    return (json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True)+'\n').encode()


def require(ok):
    if not ok:
        raise ValueError('invalid pll-public-api-v1 corpus')


def integer(value, low, high):
    return (isinstance(value, str) and INT.fullmatch(value) is not None
            and low <= int(value) <= high)


def encoded(value, pattern):
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def provenance(data):
    require(isinstance(data, dict))
    require(set(data) == {'schema', 'source', 'source_hashes', 'harness_hashes', 'go',
                          'seed', 'algorithm', 'command', 'cases', 'results'})
    require(data['schema'] == 'pll-public-api-v1')
    require(data['source'] == '971282632129110794c9d6edd22026e9de2359be')
    require(data['seed'] == '21274')
    require(data['algorithm'] == 'LCG32: (1664525*x+1013904223) mod 2**32')
    require(data['command'] == 'PYTHONDONTWRITEBYTECODE=1 python3 -B tools/go-corpus/generate.py ../pll')
    require(encoded(data['go'], re.compile(r'go version go[0-9]+\.[0-9]+(?:\.[0-9]+)? [a-z0-9]+/[a-z0-9]+\Z')))
    hashes = data['source_hashes']
    require(isinstance(hashes, dict) and bool(hashes))
    require(all(isinstance(n, str) and encoded(h, SHA256) for n, h in hashes.items()))
    require(hashlib.sha256(canonical(hashes)).hexdigest() == SOURCE_MANIFEST_SHA256)
    hashes = data['harness_hashes']
    require(isinstance(hashes, dict) and set(hashes) == HARNESS)
    require(all(encoded(h, SHA256) for h in hashes.values()))


def error_row(row, codes):
    require(len(row) >= 2 and row[0] == 'error' and row[1] in codes)
    if row[1] == 'config':
        require(len(row) == 4 and row[2] in REASONS and row[3] == REASONS[row[2]])
    else:
        require(len(row) == 2)


def operation(op, kind):
    require(isinstance(op, dict) and set(op) == {'name', 'args'})
    name, args = op['name'], op['args']
    require(isinstance(name, str) and name in ARITY)
    require(kind in ('pacer', 'follower') and (name in PACER) == (kind == 'pacer'))
    require(isinstance(args, list) and len(args) == ARITY[name])
    bounds = {
        'claim': [(0, U)], 'due': [(LO, HI), (0, U)], 'skip': [(LO, HI), (0, U)],
        'set_trim': [(LO, HI)], 'time': [(0, HI), (0, U)], 'all': [(0, HI), (1, HI)],
        'observe': [(LO, HI), (LO, HI)], 'local': [(LO, HI)],
        'remote': [(LO, HI)], 'state': [(LO, HI)]
    }
    require(all(integer(a, low, high) for a, (low, high) in zip(args, bounds.get(name, []))))


def operation_result(op, row, spans):
    name, args = op['name'], op['args']
    if name in ('time', 'all'):
        index = int(args[0])
        require(index < len(spans))
        if name == 'time':
            require(int(args[1]) < spans[index][1])
    errors = {'claim': {'invalid_argument', 'overflow'}, 'due': {'invalid_argument', 'overflow'},
              'skip': {'invalid_argument', 'overflow'}, 'next_due': {'overflow'},
              'set_trim': {'invalid_argument', 'overflow'}, 'observe': {'order', 'overflow'},
              'local': {'not_anchored', 'overflow'}, 'remote': {'not_anchored', 'overflow'}}
    if row[0] == 'error':
        error_row(row, errors.get(name, set()))
        return
    tag = {'claim': 'span', 'due': 'span', 'next_due': 'next', 'all': 'all',
           'set_trim': 'ok', 'reset': 'ok', 'observe': 'observation',
           'state': 'state', 'offset': 'float'}.get(name, 'int')
    require(row[0] == tag)
    if tag == 'span':
        require(len(row) in (3, 5) and integer(row[1], 0, U) and integer(row[2], 0, U))
        first, count = map(int, row[1:3])
        require(first+count <= U and len(row) == (5 if count else 3))
        require(all(integer(v, 0, HI) for v in row[3:]))
        spans.append((first, count))
    elif tag == 'all':
        require(len(row) % 2 == 1)
        first, count = spans[int(args[0])]
        require((len(row)-1)//2 == min(count, int(args[1])))
        for j in range(1, len(row), 2):
            require(integer(row[j], 0, U) and int(row[j]) == first+(j-1)//2)
            require(integer(row[j+1], 0, HI))
    elif tag == 'next':
        require(len(row) == 3 and integer(row[1], 0, U-1) and integer(row[2], 0, HI))
    elif tag == 'observation':
        require(len(row) == 3 and row[1] in ('1', '2', '3', '4', '5') and integer(row[2], LO, HI))
        require(row[1] not in ('1', '3') or row[2] == '0')
    elif tag == 'state':
        require(len(row) == 2 and row[1] in ('0', '1', '2'))
    elif tag == 'float':
        require(len(row) == 2 and encoded(row[1], HEX))
        require(int(row[1], 16) & 0x7ff0000000000000 != 0x7ff0000000000000)
    elif tag == 'ok':
        require(len(row) == 1)
    else:
        low, high = (0, U) if name == 'skip' else (LO, HI)
        require(len(row) == 2 and integer(row[1], low, high))


def load(path):
    """Return validated v1 shared-domain data; malformed schemas raise ValueError."""
    raw = Path(path).read_bytes()
    data = json.loads(raw)
    require(raw == canonical(data))
    provenance(data)
    require(isinstance(data['cases'], list) and bool(data['cases']))
    require(isinstance(data['results'], list) and len(data['cases']) == len(data['results']))
    ids = set()
    for c, rows in zip(data['cases'], data['results']):
        require(isinstance(c, dict) and set(c) == {'id', 'kind', 'rate', 'config', 'ops', 'tolerance', 'rationale'})
        require(isinstance(c['id'], str) and bool(c['id']) and c['id'] not in ids)
        ids.add(c['id'])
        require(isinstance(c['kind'], str) and c['kind'] in ('rate', 'bits', 'pacer', 'follower'))
        require(isinstance(c['rate'], list) and len(c['rate']) == 2 and all(integer(x, 0, U) for x in c['rate']))
        require(isinstance(c['tolerance'], str) and c['tolerance'] in ('exact', 'moderate', 'extreme'))
        require(c['kind'] == 'follower' or c['tolerance'] == 'exact')
        require(isinstance(c['rationale'], str) and bool(c['rationale']))
        require(isinstance(c['config'], dict) and set(c['config']) <= FIELDS)
        require(c['kind'] == 'follower' or not c['config'])
        for k, v in c['config'].items():
            require(encoded(v, HEX) if k in FLOATS else integer(v, LO, HI))
            # The harness supports only the zero-rate sentinel override.
            require(k != 'Nominal' or v == '0')
        require(isinstance(c['ops'], list))
        for op in c['ops']:
            operation(op, c['kind'])
        require(isinstance(rows, list) and bool(rows))
        require(all(isinstance(r, list) and bool(r) and all(isinstance(v, str) for v in r) for r in rows))
        if rows[0][0] == 'error':
            error_row(rows[0], {'invalid_rate'})
            require(len(rows) == 1)
            continue
        require(len(rows[0]) == 4 and rows[0][0] == 'rate')
        require(all(integer(v, 1, U) for v in rows[0][1:3]) and bool(rows[0][3]))
        if len(rows) == 2 and rows[1][:2] == ['error', 'config']:
            require(c['kind'] == 'follower')
            error_row(rows[1], {'config'})
            continue
        require(len(rows) == len(c['ops'])+1)
        spans = []
        for op, row in zip(c['ops'], rows[1:]):
            operation_result(op, row, spans)
    return data


def verify_artifacts(data):
    provenance(data)
    for name, sha in data['harness_hashes'].items():
        if hashlib.sha256((ROOT/'tools/go-corpus'/name).read_bytes()).hexdigest() != sha:
            raise ValueError('harness hash mismatch')
    path = ROOT/'fixtures/go-public-api.json'
    if hashlib.sha256(path.read_bytes()).hexdigest() != (ROOT/'fixtures/go-public-api.sha256').read_text().strip():
        raise ValueError('corpus hash mismatch')
