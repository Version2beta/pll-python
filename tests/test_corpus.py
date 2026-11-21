"""Complete Stage 3 source-named schema/replay/artifact/oracle checks."""
import copy
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from corpus_schema import load, canonical, verify_artifacts
from replay_corpus import replay_file
PATH = ROOT/'fixtures/go-public-api.json'


class CorpusTests(unittest.TestCase):
    def test_schema_and_coverage(self):
        d=load(PATH)
        self.assertEqual(len(d['cases']),84)
        self.assertEqual(sum(len(x) for x in d['results']),2299)
        names={o['name'] for c in d['cases'] for o in c['ops']}
        from corpus_schema import ARITY
        self.assertEqual(names,set(ARITY))
        table={c['id']:r for c,r in zip(d['cases'],d['results'])}
        failed=table['active-run-True']
        self.assertEqual(failed[3],['error','overflow'])
        self.assertEqual(failed[:3]+failed[4:],table['active-run-False'])
        statuses={r[1] for rows in d['results'] for r in rows if r[0]=='observation'}
        self.assertEqual(statuses,set('12345'))
        self.assertEqual({r[1] for rows in d['results'] for r in rows if r[0]=='error'},
                         {'config','invalid_rate','invalid_argument','overflow','order','not_anchored'})

    def test_reject_malformed_schema(self):
        d=load(PATH)
        bad=[]
        for key,value in [('schema','unknown'),('seed','0'),('source','wrong')]:
            x=copy.deepcopy(d);x[key]=value;bad.append(x)
        x=copy.deepcopy(d);x['cases'][0]['rate'][0]='00';bad.append(x)
        x=copy.deepcopy(d);x['cases'][0]['config']={'Bandwidth':'nan'};bad.append(x)
        x=copy.deepcopy(d);x['cases'][10]['ops'][0]['args'][0]=True;bad.append(x)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'bad.json'
            for x in bad:
                p.write_bytes(canonical(x))
                with self.assertRaises((ValueError,TypeError)):
                    load(p)

    def test_artifact_identity_and_case_regeneration(self):
        d=load(PATH);verify_artifacts(d)
        spec=importlib.util.spec_from_file_location('cases',ROOT/'tools/go-corpus/cases.py')
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        self.assertEqual(d['cases'],m.cases())
        self.assertEqual(d['cases'],m.cases())
        self.assertEqual(len(d['harness_hashes']),3)

    def test_public_api_replay(self):
        self.assertEqual(replay_file(PATH),2299)
        d=load(PATH)
        # A plausible but wrong expected integer must not be accepted.
        d['results'][10][1][-1]='200'
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'wrong.json';p.write_bytes(canonical(d))
            with self.assertRaises(AssertionError):
                replay_file(p)

    def test_fraction_pacing_crosscheck(self):
        d=load(PATH)
        # Independent initial-segment boundary checks, no production helpers.
        checked=0
        for c,rows in zip(d['cases'],d['results']):
            if c['kind']!='pacer':continue
            num,den=map(int,c['rate'])
            if c['ops'][0]['name']=='claim' and rows[1][0]=='span':
                first,count,t0,t1=map(int,rows[1][1:])
                self.assertEqual(t0,int(Fraction(first*den*10**9,num)))
                self.assertEqual(t1,int(Fraction((first+count-1)*den*10**9,num)))
                checked+=1
        self.assertGreaterEqual(checked,5)

    def test_decimal_gain_source_matrix(self):
        def fl(s):return struct.unpack('>d',bytes.fromhex(s))[0]
        checked=0
        d=load(PATH)
        for c,rows in zip(d['cases'],d['results']):
            if c['tolerance']!='extreme':continue
            local,remote=map(int,c['ops'][1]['args'])
            phase=local-remote
            with localcontext() as ctx:
                ctx.prec=110
                # Decimal pi, not the implementation's float gain helpers.
                pi=Decimal('3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679')
                dt=Decimal(local)/10**9
                x=min(Decimal('.5'),2*pi*Decimal.from_float(fl(c['config']['Bandwidth']))*dt)
                kp=min(Decimal(1),2*Decimal.from_float(fl(c['config']['Damping']))*x)
                y=-(x*x/dt)*Decimal(phase)/10**9
                actual_y=Decimal.from_float(fl(rows[-1][1]))
                self.assertLessEqual(abs(actual_y-y),Decimal('1e-20'))
                prediction=Decimal(remote)+kp*phase
                self.assertLessEqual(abs(Decimal(rows[-2][1])-prediction),1)
            checked+=1
        self.assertEqual(checked,36)

    def test_moderate_independent_corpus_model(self):
        import math
        from tests.test_follower_models import nearest
        d=load(PATH)
        index=next(i for i,c in enumerate(d['cases']) if c['id']=='follower-lcg')
        c,rows=d['cases'][index],d['results'][index]
        anchor,tick,ref,y,m,accepted=0.,0,0,0.,None,0
        for o,row in zip(c['ops'],rows[1:]):
            name=o['name']
            if name=='reset':break
            if name=='observe':
                l,r=map(int,o['args'])
                if r==0:
                    self.assertEqual(row,['observation','1','0']);continue
                pred=anchor+(r-tick)*1000000/(1+y)
                error=l-pred
                dt=(l-ref)*1e-9
                x=min(.5,2*math.pi*.1*dt)
                kp=min(1.,math.sqrt(2)*x)
                y=min(.0005,max(-.0005,y-x*x*error/dt*1e-9))
                anchor=pred+kp*error
                tick,ref=r,l
                m=error*error if m is None else (15*m+error*error)/16
                accepted+=1
                self.assertEqual(row[:2],['observation','2'])
                self.assertLessEqual(abs(int(row[2])-nearest(error)),1)
            elif name=='local' and accepted:
                r=int(o['args'][0]);self.assertLessEqual(abs(int(row[1])-nearest(anchor+(r-tick)*1000000/(1+y))),1)
            elif name=='remote' and accepted:
                l=int(o['args'][0]);self.assertLessEqual(abs(int(row[1])-nearest(tick+(l-anchor)*(1+y)/1000000)),1)
            elif name=='offset' and accepted:
                actual=struct.unpack('>d',bytes.fromhex(row[1]))[0]
                self.assertLessEqual(abs(actual-y),1e-12)
            elif name=='jitter' and accepted>1:
                self.assertLessEqual(abs(int(row[1])-nearest(math.sqrt(m))),2)
        self.assertEqual(accepted,200)
