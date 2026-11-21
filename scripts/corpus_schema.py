"""Complete shared-domain schema and canonical artifact guard; do not change."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
INT = re.compile(r'(0|-?[1-9][0-9]*)\Z')
HEX = re.compile(r'[0-9a-f]{16}\Z')
ARITY = dict(claim=1, due=2, skip=2, next_due=0, set_trim=1, pacer_trim=0,
             time=2, all=2, observe=2, local=1, remote=1, offset=0, trim=0,
             jitter=0, state=1, reset=0)
FLOATS = {'Bandwidth', 'Damping', 'MaxOffsetPPM'}
FIELDS = FLOATS | {'Nominal', 'Window', 'OutlierThreshold', 'StepAfter', 'LockThreshold', 'LockCount', 'HoldoverAfter'}


def canonical(obj):
    return (json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=True)+'\n').encode()


def _load(path):
    """Load canonical v1 data; reject malformed or unsupported shared-domain records."""
    raw = Path(path).read_bytes()
    data = json.loads(raw)
    def require(ok):
        if not ok:
            raise ValueError('invalid pll-public-api-v1 corpus')
    def integer(x):
        return isinstance(x, str) and INT.fullmatch(x) is not None
    require(raw == canonical(data))
    require(set(data) == {'schema','source','source_hashes','harness_hashes','go','seed','algorithm','command','cases','results'})
    require(data['schema'] == 'pll-public-api-v1')
    require(data['source'] == '971282632129110794c9d6edd22026e9de2359be')
    require(data['seed'] == '21274')
    require(isinstance(data['cases'], list) and len(data['cases']) > 0)
    require(len(data['cases']) == len(data['results']))
    ids = set()
    for c, rows in zip(data['cases'], data['results']):
        require(set(c) == {'id','kind','rate','config','ops','tolerance','rationale'})
        require(isinstance(c['id'], str) and c['id'] not in ids)
        ids.add(c['id'])
        require(c['kind'] in ('rate','bits','pacer','follower'))
        require(len(c['rate']) == 2 and all(integer(x) and 0 <= int(x) < 2**64 for x in c['rate']))
        require(c['tolerance'] in ('exact','moderate','extreme') and bool(c['rationale']))
        require(set(c['config']) <= FIELDS)
        for k,v in c['config'].items():
            require(isinstance(v,str) and (HEX.fullmatch(v) if k in FLOATS else integer(v) and -2**63 <= int(v) < 2**63))
        for o in c['ops']:
            require(set(o) == {'name','args'} and o['name'] in ARITY)
            require(len(o['args']) == ARITY[o['name']] and all(integer(x) for x in o['args']))
        require(isinstance(rows,list) and bool(rows))
        for r in rows:
            require(isinstance(r,list) and all(isinstance(x,str) for x in r) and bool(r))
            tag = r[0]
            require(tag in ('rate','span','all','int','next','observation','state','float','ok','error'))
            if tag == 'float':
                require(len(r)==2 and HEX.fullmatch(r[1]) is not None)
            elif tag == 'ok':
                require(len(r)==1)
            elif tag == 'error':
                require(len(r) in (2,4) and r[1] in ('invalid_rate','invalid_argument','overflow','order','not_anchored','config'))
            elif tag == 'rate':
                require(len(r)==4 and all(integer(x) for x in r[1:3]))
            else:
                require(all(integer(x) for x in r[1:]))
                sizes={'int':(2,), 'next':(3,), 'state':(2,), 'observation':(3,), 'span':(3,5)}
                require(tag not in sizes or len(r) in sizes[tag])
                require(tag!='all' or len(r)%2==1)
        if rows[0][0]=='error':
            require(rows==[['error','invalid_rate']])
        elif len(rows)==2 and rows[-1][:2]==['error','config']:
            require(c['kind']=='follower')
        else:
            require(len(rows)==len(c['ops'])+1)
    return data


def load(path):
    """Return validated v1 data; malformed schemas always raise ValueError."""
    try:
        return _load(path)
    except (TypeError, KeyError, IndexError, AttributeError) as exc:
        raise ValueError('invalid pll-public-api-v1 corpus') from exc


def verify_artifacts(data):
    for name, sha in data['harness_hashes'].items():
        if name not in ('main.go','cases.py','generate.py'):
            raise ValueError('unknown harness source')
        if hashlib.sha256((ROOT/'tools/go-corpus'/name).read_bytes()).hexdigest() != sha:
            raise ValueError('harness hash mismatch')
    path = ROOT/'fixtures/go-public-api.json'
    if hashlib.sha256(path.read_bytes()).hexdigest() != (ROOT/'fixtures/go-public-api.sha256').read_text().strip():
        raise ValueError('corpus hash mismatch')
