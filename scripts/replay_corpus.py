"""Replay the validated shared-domain corpus using only public pll APIs."""
from dataclasses import replace
from itertools import islice
import math
import struct

import pll
from corpus_schema import load, verify_artifacts


_FIELDS = {
    'Nominal': 'nominal', 'Bandwidth': 'bandwidth_hz', 'Damping': 'damping',
    'MaxOffsetPPM': 'max_offset_ppm', 'Window': 'window_ns',
    'OutlierThreshold': 'outlier_threshold_ns', 'StepAfter': 'step_after',
    'LockThreshold': 'lock_threshold_ns', 'LockCount': 'lock_count',
    'HoldoverAfter': 'holdover_after_ns',
}
_FLOAT_FIELDS = {'Bandwidth', 'Damping', 'MaxOffsetPPM'}


def _float(bits):
    return struct.unpack('>d', bytes.fromhex(bits))[0]


def _error(exc):
    if isinstance(exc, pll.ConfigError):
        field = next(go for go, py in _FIELDS.items() if py == exc.field)
        return ['error', 'config', field, exc.reason]
    return ['error', exc.code]


def _operation(controller, spans, op):
    name = op['name']
    args = [int(a) for a in op['args']]
    if name in ('claim', 'due'):
        span = getattr(controller, name)(*args)
        spans.append(span)
        row = ['span', str(span.first), str(span.count)]
        if span.count:
            row += [str(span.time(0)), str(span.time(span.count - 1))]
        return row
    if name == 'time':
        return ['int', str(spans[args[0]].time(args[1]))]
    if name == 'all':
        row = ['all']
        for slot, time_ns in islice(spans[args[0]].all(), args[1]):
            row.extend((str(slot), str(time_ns)))
        return row
    if name == 'next_due':
        slot, time_ns = controller.next_due()
        return ['next', str(slot), str(time_ns)]
    if name == 'observe':
        obs = controller.observe(*args)
        return ['observation', str(int(obs.status)), str(obs.error_ns)]
    if name == 'offset':
        return ['float', struct.pack('>d', controller.offset()).hex()]
    if name == 'state':
        return ['state', str(int(controller.state(*args)))]
    if name in ('set_trim', 'reset'):
        getattr(controller, name)(*args)
        return ['ok']
    method = 'trim' if name == 'pacer_trim' else name
    return ['int', str(getattr(controller, method)(*args))]


def _rows(case):
    try:
        factory = pll.bits_per_second if case['kind'] == 'bits' else pll.units_per_second
        rate = factory(*(int(x) for x in case['rate']))
    except pll.PllError as exc:
        yield _error(exc)
        return
    yield ['rate', str(rate.num), str(rate.den), str(rate)]
    controller = None
    try:
        if case['kind'] == 'pacer':
            controller = pll.Pacer(rate)
        elif case['kind'] == 'follower':
            fields = {}
            for name, value in case['config'].items():
                if name == 'Nominal':
                    value = pll.Rate()
                elif name in _FLOAT_FIELDS:
                    value = _float(value)
                else:
                    value = int(value)
                fields[_FIELDS[name]] = value
            controller = pll.Follower(replace(pll.default_follower_config(rate), **fields))
    except pll.PllError as exc:
        yield _error(exc)
        return
    spans = []
    for op in case['ops']:
        try:
            row = _operation(controller, spans, op)
        except pll.PllError as exc:
            row = _error(exc)
        yield row


def _matches(actual, expected, tolerance, name):
    if actual == expected:
        return True
    if len(actual) != len(expected) or actual[0] != expected[0]:
        return False
    # Only these numerical fields have an approved nonzero tolerance.
    if actual[0] == 'float' and name == 'offset' and tolerance != 'exact':
        a, e = _float(actual[1]), _float(expected[1])
        limit = 1e-12 if tolerance == 'moderate' else 1e-20
        return math.isfinite(a) and math.isfinite(e) and abs(a - e) <= limit
    limits = {}
    if tolerance == 'moderate':
        limits = {'observe': 1, 'local': 1, 'remote': 1, 'jitter': 2}
    elif tolerance == 'extreme':
        limits = {'local': 1}
    if name not in limits:
        return False
    # For observations the status (like every tag/error/state) stays exact.
    index = 2 if name == 'observe' else 1
    tag = 'observation' if name == 'observe' else 'int'
    return (actual[0] == tag and actual[:index] == expected[:index]
            and abs(int(actual[index]) - int(expected[index])) <= limits[name])


def replay_file(path) -> int:
    """Validate artifacts and check every row; stop with reproduction on disagreement."""
    data = load(path)
    verify_artifacts(data)
    checked = 0
    for case_index in range(len(data['cases'])):
        case = data['cases'][case_index]
        expected_rows = data['results'][case_index]
        count = 0
        for row_index, actual in enumerate(_rows(case)):
            expected = expected_rows[row_index] if row_index < len(expected_rows) else None
            op = case['ops'][row_index - 1] if 0 < row_index <= len(case['ops']) else None
            name = op['name'] if op else None
            if expected is None or not _matches(actual, expected, case['tolerance'], name):
                raise AssertionError(
                    f"case={case['id']!r} row={row_index} operation={op!r} "
                    f"expected={expected!r} actual={actual!r}; reproduce case={case!r}")
            count += 1
            checked += 1
        if count != len(expected_rows):
            raise AssertionError(
                f"case={case['id']!r} expected {len(expected_rows)} rows, got {count}; "
                f"reproduce case={case!r}")
    return checked
