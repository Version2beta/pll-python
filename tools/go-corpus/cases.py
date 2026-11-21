"""Complete deterministic shared-domain cases; do not change."""
import struct


def bits(x):
    return struct.pack('>d', x).hex()


def cases():
    result = []

    def add(id, kind, rate, ops=(), config=None, tolerance='exact', rationale='Integer/classification or hand-derived boundary; exact.'):
        result.append(dict(id=id, kind=kind, rate=list(map(str, rate)),
                           config=config or {}, ops=[dict(name=n, args=list(map(str, a))) for n, *a in ops],
                           tolerance=tolerance, rationale=rationale))

    U, HI, LO = 2**64-1, 2**63-1, -2**63
    for kind in ('rate', 'bits'):
        for n, d in ((0, 1), (1, 0), (60000, 2002), (U, U-1), (50000000, 8)):
            add(f'{kind}-{n}-{d}', kind, (n, d))
    add('pacer-neighbors-retention', 'pacer', (375000000, 1), [
        ('claim', 2), ('next_due',), ('due', 5, 10), ('due', 6, 10), ('set_trim', -500000000000),
        ('claim', 3), ('time', 0, 1), ('all', 0, 2), ('set_trim', 10**12), ('claim', 0),
        ('due', -1, 1), ('due', 20, 0), ('skip', 100, 2), ('due', 100, 2), ('pacer_trim',), ('time',0,1), ('all',0,2)])
    for rate in ((2000000000, U), (U, 1), (1, U), (U, U-1)):
        add('pacer-extreme-'+str(rate[0])+str(rate[1]), 'pacer', rate, [
            ('claim', 1), ('next_due',), ('due', HI, 1), ('claim', U-1), ('next_due',),
            ('due', 0, 1), ('due', HI, 1), ('skip', HI, 0), ('set_trim', 0),
            ('set_trim', 999999999999), ('set_trim', -999999999999), ('claim', 1), ('pacer_trim',)])
    seed = 0x531A
    def rand():
        nonlocal seed
        seed = (1664525*seed+1013904223) & 0xffffffff
        return seed
    ops=[]
    for k in range(120):
        choice=rand()%5
        ops += [(('claim', 1+rand()%7) if choice==0 else
                 ('due', rand()%100000000, 1+rand()%10) if choice==1 else
                 ('skip', rand()%100000000, rand()%5) if choice==2 else
                 ('set_trim', (rand()%1000000000)-500000000) if choice==3 else ('next_due',))]
    add('pacer-lcg', 'pacer', (48000, 1), ops)
    def workflow(obs):
        ops=[('local',0),('remote',0),('offset',),('trim',),('jitter',),('state',0)]
        for l,r in obs:
            ops += [('observe',l,r),('local',r),('remote',l),('offset',),('trim',),('jitter',),('state',l)]
        return ops+[('state',HI),('reset',),('local',0),('observe',-5,-5),('offset',),('jitter',)]
    add('lock-holdover', 'follower', (1000,1), workflow([(0,0)]+[(k*10000000,k*10) for k in range(1,9)])+ [('state',5080000000),('state',5080000001)])
    add('outlier-first-step-order', 'follower',(10**9,1),workflow([(0,0)]+[(0,r) for r in (10,20,30,40,41,42,42,43)]), {'Bandwidth':bits(5e-324),'OutlierThreshold':'10'})
    for window in (0,4,HI):
        add('window-'+str(window),'follower',(10**9,1),workflow([(0,0),(1,1),(2,3),(3,4),(4,5),(5,6),(6,6),(6,7),(10,11)]),{'Window':str(window),'Bandwidth':bits(5e-324),'HoldoverAfter':'10'})
    for origin in (1,-1,2**53+1,-2**53-1):
        add('half-tie-'+str(origin),'follower',(2*10**9,1), [('observe',origin,0),('local',-1),('local',1),('remote',origin)])
    for origin in (LO, HI):
        add('wide-'+str(origin),'follower',(10**9,1), [('observe',origin,origin),('local',0),('remote',0),('local',-1025),('state',HI)])
    for window in (0,1):
        add('overflow-retry-'+str(window),'follower',(10**9,1), [('observe',HI-1024,0),('observe',HI-1,2048),('observe',HI,2049),('observe',HI,2049),('observe',HI-1,2049),('local',0),('reset',),('observe',0,0),('observe',1,1)],{'Window':str(window),'Bandwidth':bits(5e-324),'OutlierThreshold':str(HI)})
    add('signed-window','follower',(10**9,1),[('observe',LO,0),('observe',LO+1,1),('observe',0,2),('state',HI)],{'Window':str(HI)})
    fields={'Bandwidth':[-0.,float('nan'),float('inf'),-float('inf')], 'Damping':[0.], 'MaxOffsetPPM':[1e6], 'Window':[-1], 'OutlierThreshold':[0], 'StepAfter':[0], 'LockThreshold':[-1], 'LockCount':[0], 'HoldoverAfter':[0]}
    for field, vals in fields.items():
        for j,v in enumerate(vals):
            add(f'config-{field}-{j}','follower',(1000,1),config={field:bits(v) if isinstance(v,float) else str(v)})
    add('config-nominal','follower',(1000,1),config={'Nominal':'0'})
    add('error-saturation-negative','follower',(1,1),[('observe',0,LO),('observe',1,HI),('offset',),('jitter',)])
    add('error-saturation-positive','follower',(1,1),[('observe',LO,0),('observe',HI,1),('offset',),('jitter',)],{'OutlierThreshold':str(HI),'Bandwidth':bits(5e-324)})
    # Identical suffixes after an overflowing observation and a control with
    # that failed call omitted expose hidden order/outlier rollback through
    # subsequent public classifications, not just immediate query snapshots.
    for failed in (False,True):
        base=[('observe',HI-1024,0),('observe',HI-1023,1536)]
        suffix=[('observe',HI-1022,1537),('observe',HI-1021,1538),('local',1538),('offset',),('jitter',),('state',HI)]
        ops=base+([('observe',HI,2048)] if failed else [])+suffix
        add(f'active-run-{failed}','follower',(10**9,1),ops,{'Bandwidth':bits(5e-324),'OutlierThreshold':'1024'})
    for b in (5e-324,1e-300,.1,float.fromhex('0x1.fffffffffffffp1023')):
        for d in (5e-324,2**.5/2,float.fromhex('0x1.fffffffffffffp1023')):
            for phase in (0,-100,100):
                add(f'gain-{bits(b)}-{bits(d)}-{phase}','follower',(10**9,1),[('observe',0,0),('observe',10**9+phase,10**9),('local',10**9),('offset',)],{'Bandwidth':bits(b),'Damping':bits(d)},'extreme','Source gain matrix only; Decimal 110-digit independent check in prior model suite; local 1ns offset 1e-20.')
    obs=[(0,0)]
    for k in range(1,201):
        obs.append((k*10000000+(rand()%2001)-1000,k*10))
    add('follower-lcg','follower',(1000,1),workflow(obs),tolerance='moderate',rationale='Bounded noisy synthetic sequence; error/local 1ns remote 1tick offset 1e-12 jitter 2ns; classifications exact.')
    return result
