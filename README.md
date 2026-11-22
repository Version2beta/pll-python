# pll-python


The Rate, Pacer, complete Follower and `pllpace` command are implemented.
Version `0.1.0`.

This library helps audio/video, sensor, packet and device-buffer applications
pace units on their own timeline or learn the relationship to another clock.
A rational **Pacer** issues numbered slots without accumulated rounding drift.
A type-II, second-order phase-locked **Follower** estimates remote-clock phase
and frequency, filters delivery jitter, and maps ticks to local nanoseconds.
They work separately or together: follower trim can steer a pacer.


## Provenance, parity and non-goals

Source: Go `github.com/version2beta/pll`, revision
[`971282632129110794c9d6edd22026e9de2359be`](https://github.com/version2beta/pll/tree/971282632129110794c9d6edd22026e9de2359be). The basis is its complete `SPEC.md`, `README.md`,
`rate.go`, `pacer.go`, `span.go`, `follower.go`, errors/status/package comments,
and the rate, pacer, follower, examples, boundary and differential-model tests.
The original is provenance, not a runtime dependency.

Functional parity means exact pacer results, equivalent follower equations and
state transitions, error categories and atomic failures on the shared domain.
It does not mean Go ABI, duration formatting, writable span fields, iterator
protocol, zero-value controller structs, sentinel-error matching, memory layout,
or Go-specific arithmetic fast paths. Python representations are specified here.
There is **no transplanted claim** about Go nanosecond benchmarks, zero
allocations, race-detector results, simulator results or real-time scheduling.

This is a library, not a token bucket, sleeping rate limiter, scheduler, clock
servo/PTP/NTP client, counter-unwrapper, transport, payload queue or device driver.
The Go `cmd/pllpace`, `cmd/pllsim`, UDP tests, full simulator and benchmarking
commands were excluded from initial port scope. The
`pllpace` adapter is included; simulator and benchmark products remain deferred.

## Installation

Requires CPython 3.11+ with binary64 floats and unbounded integers.
No runtime dependencies. The distribution is `pll-python`; the import is `pll`.

After the 0.1.0 release is published:

```sh
python -m pip install pll-python==0.1.0
```

For a release candidate, install the validated wheel with
`python -m pip install --no-index --no-deps WHEEL_PATH`.
`pllpace` is the sole console entry point.

## Real-time pacing command (`pllpace`)

After local wheel installation, run `pllpace --help`, or use
`python -m pll.pllpace` (also available from this source checkout):

```sh
pllpace -seconds 0.1 -bps 8000 -unit-bytes 1000
python -m pll.pllpace --mode ticker --seconds 0.1 --bps 8000
pllpace -seconds 0.1 -bps 8000 -udp loopback -per-datagram 2
# Optional longer measurement; sends only to an in-process localhost receiver:
pllpace -find-max -seconds 2 -udp loopback -slack 5ms
```

Shares upstream `cmd/pllpace` option defaults (timing differences below): 100,000,000 bits/s,
1000 bytes/unit, 10 seconds/trial, pacer mode, discard output, one unit per
UDP datagram, search disabled, and 5ms search slack. Both `-flag` and `--flag`
forms (including `=value`) work. `-find-max` is a presence-only argparse flag,
not Go's `-find-max=true/false`; omit it for false. Argparse rejects positional
arguments/unknown options and uses exit 2 for syntax errors; semantic/runtime
errors use exit 1, interruption 130. Slack accepts signed composite Go-style
`ns`, `us`/`µs`/`μs`, `ms`, `s`, `m`, `h` durations (or `0`); seconds is a
finite floating-point count converted to integer ns. Source uint64/int64 and
platform-int envelopes and the 65507-byte UDP payload limit are retained.
All options are validated before payload allocation or sockets are opened.

Pacer mode uses `Pacer(bits_per_second(...))`, slot zero immediately due,
and batches at most 4096 units per wake-up without dropping backlog. Ticker
mode starts after one exact integer-ns period and emits one unit per wake-up,
dropping missed periods; it is a Python monotonic-clock/sleep comparison,
**not** Go's timer implementation or a real-time scheduler guarantee. Sleeps
are capped at the trial deadline, even at very low rates. Final partial groups
are flushed per trial, including flush time in elapsed/backlog/byte counts;
failed writes discard buffered data, never retry it in the next trial.
Discard ignores `-per-datagram`, matching upstream. UDP is used only with
`-udp loopback` or `-udp host:port` (bracket IPv6 addresses); remote destinations
are resolved/sent to only when explicitly selected. The localhost receiver and
sender are closed and the worker joined on success, error or interruption.
UDP writer acceptance does not acknowledge delivery; receipt is not measured.

Output includes progress each elapsed second, writer Mbps, offered units,
writer-accepted bytes, elapsed time, end backlog, wake-up count/average/max
batch, and pacer oldest-unit lateness median/p99/max (floor-index quantiles).
Durations are printed in milliseconds rather than Go duration formatting.
Search trials must be nonempty, have end backlog <= slack and lateness p99 <=
slack; rates double from `-bps` through at most 1,000,000,000,000 bits/s, then
bisect a passing/failing bracket until within 5% or adjacent integer rates.
If the initial rate fails it does not search below it. If all doubling trials
pass, only the highest *tested* rate is reported. This is an empirical local
measurement, not proof of a globally maximal sustainable rate or portable
performance. Trial duration, byte allocations and collected lateness samples
consume real time/memory; search can run many trials. Ctrl-C cancels it.

The library itself still performs no implicit effects. Importing `pll.pllpace`
starts no clocks, output, threads or sockets; effects belong to CLI invocation.

## First useful example

All times are **integer nanoseconds**, never floating seconds or `datetime`.

```python
from pll import Pacer, units_per_second

p = Pacer(units_per_second(48_000, 1))
rows = []
for now_ns in (0, 10_000_000, 25_000_000):
    span = p.due(now_ns, 4096)
    rows.append((span.first, span.count))
assert rows == [(0, 1), (1, 480), (481, 720)]
assert p.next_due() == (1201, 25_020_834)
```

At 10 ms, slot 480 is exactly due; slot zero was already consumed. At 25 ms,
slot 1200 is due. Slot 1201 has exact time `1201 * 10**9 / 48000`, whose
ceiling is 25,020,834 ns. A late call produces backlog rather than silently
losing work. The caller chooses to process it, cap each batch, or skip it.

## Public API

Signatures use ordinary Python annotations; `Iterator` is from `collections.abc`.
Methods not shown as properties are called methods. No async or blocking API.

| API | Result / meaning |
| --- | --- |
| `units_per_second(num: int, den: int) -> Rate` | Reduce by gcd; zero terms raise `InvalidRateError`. |
| `bits_per_second(bits: int, bits_per_unit: int) -> Rate` | Exactly the same fraction, bits/bits per unit. |
| `Rate()` | Immutable invalid zero sentinel, `num == den == 0`; factories create valid rates. Other direct constructor arguments are unsupported. |
| `Rate.num: int`, `Rate.den: int` | Read-only reduced terms. |
| `str(rate)` | `"48000 units/s"`, `"30000/1001 units/s"`, or `"invalid rate"`. |
| `Pacer(rate: Rate)` | Mutable owned controller, cursor 0, trim 0; invalid rate raises `InvalidRateError`. |
| `p.due(now_ns: int, max_count: int) -> Span` | Oldest due slots up to cap; advances cursor. |
| `p.claim(n: int) -> Span` | Next n slots, due or not; advances cursor. |
| `p.skip(now_ns: int, keep: int) -> int` | Skip oldest due slots except newest keep; returns skipped count. |
| `p.next_due() -> tuple[int, int]` | `(cursor_slot, first_due_ns)`, no mutation. |
| `p.set_trim(ppt: int) -> None` | Change timing from cursor. |
| `p.trim() -> int` | Current parts-per-trillion trim. |
| `Span()` | Immutable empty zero span (`first == count == 0`). Other direct construction unsupported. |
| `span.first: int`, `span.count: int` | Read-only issued extent. |
| `span.time(i: int) -> int` | Floored time of relative index i; `IndexError` for i < 0 or i >= count. No negative indexing. |
| `span.all() -> Iterator[tuple[int, int]]` | Fresh lazy iterator of `(slot, time_ns)`; early stop does not compute remaining items. |
| `default_follower_config(nominal: Rate) -> FollowerConfig` | Frozen dataclass value with defaults below; does not validate the nominal rate. |
| `FollowerConfig(...)` | Frozen dataclass with all ten required fields below, no hidden defaults; use the default factory and `dataclasses.replace`. Validation is at `Follower` construction. |
| `Follower(config: FollowerConfig)` | Mutable owned controller; validates config and snapshots it, initially unanchored. |
| `f.observe(local_ns: int, remote: int) -> Observation` | Feed reading; mutate only on successful return. |
| `f.local(remote: int) -> int` | Remote ticks to local ns. |
| `f.remote(local_ns: int) -> int` | Local ns to remote ticks. |
| `f.offset() -> float`, `f.trim() -> int`, `f.jitter() -> int` | Fractional rate offset, pacer-compatible ppt, RMS error ns. |
| `f.state(now_ns: int) -> State` | Pure query using supplied now. |
| `f.reset() -> None` | Clear all learned/history state; retain validated configuration. |
| `Observation.status: Status`, `Observation.error_ns: int` | Frozen dataclass; phase error, not an exception. |

`Status` is an `enum.IntEnum`: `ANCHORED=1`, `ACCEPTED=2`, `PENDING=3`,
`REJECTED=4`, `STEPPED=5`. `str()` is respectively `anchored`, `accepted`,
`pending`, `rejected`, `stepped`. `State` is an `IntEnum`: `ACQUIRING=0`,
`LOCKED=1`, `HOLDOVER=2`, with corresponding lowercase strings. For Go's
unknown-value string behavior, constructing either enum with any other byte
integer 0..255 is permitted as an unnamed value: `str(Status(9)) == "Status(9)"`
and `str(State(9)) == "State(9)"`. Unknown statuses are never emitted by the
library. Values outside the byte domain raise `ValueError`. Bool and non-int construction
raise `TypeError`, even if numerically equal to a member; int subclasses are accepted.

### Types, bounds and exceptions

These envelopes are deliberate compatibility constraints despite Python's
unbounded integers. Let `U = 2**64 - 1`, `Imin = -2**63`, `Imax = 2**63 - 1`.
Rate terms and slot/count/cap/keep arguments are integers in 0..U; valid rate
terms and claim/cap counts must be positive. Pacer times supplied by the caller
must fit signed 64-bit ns, then must be nonnegative. Follower local/now times
and remote ticks may be negative but must fit signed 64-bit. Config duration
fields fit signed 64-bit; step/lock counts also use signed 64-bit (the
64-bit compatibility baseline, rather than a platform-dependent Go `int`).
Trim inputs fit signed 64-bit, then must lie strictly between ±10**12.
Internal intermediate integer products are unbounded and must not overflow.

Validation checks **all argument types**, then **all input envelopes**, then
semantics; within each phase use signature order. Wrong object/type arguments
raise `TypeError`; `bool` is rejected. `int` subclasses are accepted for integer
arguments; `float` subclasses are accepted where float is required. The three
float config fields require Python `float`, not integer coercion. Config
retains the field-by-field exception below. Thus `units_per_second(-1, "x")`
raises TypeError, while `units_per_second(0, 2**64)` and `due(-1, 2**64)` raise
OverflowError before zero/negative semantic errors. An integer outside its input envelope
raises `OverflowError` (the built-in), distinct from a computed-result
`PllOverflowError`. Within-envelope zero rate terms raise `InvalidRateError`;
negative pacer time, zero count/cap or trim outside its open interval raise
`InvalidArgumentError`. Negative unsigned inputs are outside the input envelope,
not silently wrapped. Span indexing uses `IndexError` for any integer outside
0..count-1; non-integers raise `TypeError`.

All domain errors derive from exported `PllError(Exception)`, with `.code`:

| Exception | code | `str(exception)` |
| --- | --- | --- |
| `InvalidRateError` | `invalid_rate` | `pll: invalid rate` |
| `InvalidArgumentError` | `invalid_argument` | `pll: invalid argument` |
| `PllOverflowError` | `overflow` | `pll: overflow` |
| `OrderError` | `order` | `pll: reading out of order` |
| `NotAnchoredError` | `not_anchored` | `pll: follower has no reading yet` |
| `ConfigError` | `config` | `pll: FollowerConfig.<field> <reason>` |

`ConfigError` has read-only `.field: str` (the snake-case field below) and
`.reason: str`; other errors have no field/reason attributes promised. Config
validation is in table order: each field's type/envelope is checked, then its
semantic rule, before proceeding to the next field. Wrong config field types
or envelopes produce the corresponding built-in error; validly typed but
semantically invalid fields produce `ConfigError`. This adds a Python boundary
to Go's statically typed domain. Catch by class/code, not message parsing.

**Every failed public operation preserves the supplied state**, including order,
windows, outlier runs, jitter and issued spans; no partial controller mutation
or partial result is returned. This includes built-in validation exceptions.
Rejected and pending observations are successful results, not failed calls.
Controller constructors that fail do not expose a partly initialized object.

## Exact pacer contract

Slots start at 0; the cursor is the next slot neither issued nor skipped. It
never decreases. Slot U is **never issued or skipped**; cursor U is permitted,
so `first + count <= U`. The nominal rate is the reduced `num/den` units/s.
A segment has start slot S, integer anchor A ns and trim q ppt:

```text
T(s) = A + (s-S) * den * 10^21 / (num * (10^12 + q)), s >= S
initially S=0, A=0, q=0
```

Compute with exact integer/rational arithmetic, including extreme terms and
q = ±(10**12-1). The period may be reduced once, but no Go fast-path layout is
required. `Span.time` is floor(T); a slot is due only if exact T <= now.
Thus at period 8/3 ns, time(1) is 2 but it first becomes due at 3.
At rates above 10**9, times may repeat and remain non-decreasing.

* **due:** negative now or zero cap is invalid. Find the largest due slot L
  exactly (cap L at U). If none at/after cursor is due, return an empty span
  with `first=cursor`, without advancing. If cursor U itself is due, overflow;
  otherwise issue cursor through min(L,U-1), capped by max_count, oldest first.
  Earlier now values are allowed and may still drain their due backlog.
* **claim:** zero n is invalid. Overflow if n > U-cursor, or the last slot's
  **floored** time exceeds Imax; otherwise issue and advance, regardless of now.
* **skip:** D is the number due could issue ignoring its cap (excluding U).
  Advance by D-min(D,keep); keep=0 skips all available due slots. Negative now
  is invalid; cursor U with that slot due overflows, even if keep would retain it.
  With k>0, skip(now,k) then due(now,k) issues the newest k available due slots
  (or all if fewer). With k=0 do not call due with a zero cap.
* **next_due:** return cursor and ceil(T(cursor)). Overflow if cursor U or
  the **ceiling** exceeds Imax. A floor can fit when the ceiling does not.
* **set_trim:** reject q <= -10**12 or q >= 10**12. If q equals current trim,
  do nothing, even if the cursor time cannot fit. Otherwise compute
  S=cursor, A=floor(T_old(cursor)), q=new trim; overflow if A>Imax. The new
  anchor moves phase earlier by less than 1 ns, maintains non-decreasing
  times, and prevents accumulating fractional anchors. Existing spans retain
  their original timing independently of future trims.

An issued span is immutable and self-contained for timing, covers first through
first+count-1, and may outlive its pacer. Empty spans iterate zero items and
have no valid time index. Manually forged objects/private-field changes have no
timing guarantees. No operation materializes every slot merely to issue a span.

### More hand-checkable pacing examples

```python
from pll import Pacer, bits_per_second, units_per_second

r = units_per_second(60_000, 2002)
assert (r.num, r.den, str(r)) == (30_000, 1001, "30000/1001 units/s")
p = Pacer(r)
assert list(p.claim(4).all()) == [
    (0, 0), (1, 33_366_666), (2, 66_733_333), (3, 100_100_000)
]
byte_pacer = Pacer(bits_per_second(50_000_000, 8))
assert [byte_pacer.claim(n).time(0) for n in (1500, 400, 1500)] == [0, 240_000, 304_000]
p = Pacer(units_per_second(1000, 1))
assert p.skip(10_000_000, 3) == 8  # slots 0..10 due, keep 8..10
old = p.due(10_000_000, 3)
assert list(old.all()) == [(8, 8_000_000), (9, 9_000_000), (10, 10_000_000)]
p.set_trim(-500_000_000_000)  # half speed, anchored at slot 11 / 11 ms
assert list(p.claim(3).all()) == [(11, 11_000_000), (12, 13_000_000), (13, 15_000_000)]
assert old.time(2) == 10_000_000
```

Boundary fixture: rate `(2_000_000_000, U)` has period `Imax + 1/2` ns.
After claiming slot 0, next_due overflows, due(Imax,1) is empty at first=1,
but claim(1) succeeds with time Imax. At rate `(U,1)`, claim(U) reaches cursor
U; due(0,1) is empty but due(10**9,1), skip(10**9,0), claim(1) and next_due
all overflow. These must remain cheap span operations, not enormous iterations.

## Follower configuration (all defaults and validation)

Start from `default_follower_config(rate)` and use `dataclasses.replace`.
There is no live config mutation; construct a new follower to change settings.
The table order is the validation order; reasons are exact strings.

| Python field (Go field) | Type | Default | Invalid when / ConfigError reason |
| --- | --- | --- | --- |
| `nominal` (`Nominal`) | Rate | supplied rate | zero/invalid rate: `must be a valid Rate` |
| `bandwidth_hz` (`Bandwidth`) | float | 0.1 | nonfinite or <=0: `must be finite and > 0` |
| `damping` (`Damping`) | float | sqrt(2)/2 | nonfinite or <=0: `must be finite and > 0` |
| `max_offset_ppm` (`MaxOffsetPPM`) | float | 500.0 | nonfinite, <=0 or >=1000000: `must be finite, > 0 and < 1000000` |
| `window_ns` (`Window`) | int | 0 | <0: `must be >= 0` |
| `outlier_threshold_ns` (`OutlierThreshold`) | int | 5_000_000 | <=0: `must be > 0` |
| `step_after` (`StepAfter`) | int | 3 | <1: `must be >= 1` |
| `lock_threshold_ns` (`LockThreshold`) | int | 100_000 | <0: `must be >= 0` |
| `lock_count` (`LockCount`) | int | 8 | <1: `must be >= 1` |
| `holdover_after_ns` (`HoldoverAfter`) | int | 5_000_000_000 | <=0: `must be > 0` |

Defaults target low-jitter readings. An optional, not automatic, network profile
from the source uses bandwidth 0.005 Hz, window 1_000_000_000 ns, lock threshold
2_000_000 ns, outlier threshold 20_000_000 ns, other defaults unchanged. It trades
settling speed for filtering. No source simulator's measured accuracy or lock
latency is promised by this library.

## Follower state machine and numerical contract

Local times use a caller-chosen origin, possibly negative; remote is an already
unwrapped signed tick counter. Nominal tick period `Pn = float(den)*1e9/float(num)`
is binary64 ns. Hold anchor as integer `I0` plus binary64 fraction `frac`, remote
anchor `R0`, and offset y. Initially unanchored, y=0, jitter=0, acquiring.

```text
displacement(r) = ((ticks*Pn)/(1+y)) + frac
e = nanos_between(local,I0) - displacement(r)
remote speed = nominal * (1+y)
```

Here ticks=nanos_between(r,R0): this helper subtracts integers before conversion
when signed64 fits, otherwise subtracts the separately converted float operands.
Never form absolute predicted time as a float. Pn=(float(den)*1e9)/float(num),
wn=(2*pi)*bandwidth; preserve these groupings and the gain groupings below,
without FMA/reassociation. remote uses ((ns-frac)*(1+y))/Pn. Positive infinite
products are permitted only before the x/kp min caps. Do not compute 2*damping
before multiplying x, nor cap dt before multiplying wn.


Compute integer differences before converting to float when they fit signed
64-bit, preserving small differences at huge absolute times. If a difference
exceeds signed 64-bit, use `float(a)-float(b)` as in Go; do not wrap or round the
integer anchor itself to float. Converting a large difference to float can
still lose low bits beyond 2**53. Rebase on every loop update using integer plus
fraction anchors so precision does not depend on absolute local uptime.

### observe, in order

1. After the first reading, local must be >= the last successful reading's
   local, and remote strictly greater than its remote. Otherwise `OrderError`.
   Previous includes pending/rejected/stepped readings, not failed calls.
2. First reading (also after reset) anchors exactly to `(local,remote)`, offset
   zero, clears histories, and returns `Observation(Status.ANCHORED, 0)`.
3. With window_ns=0 feed each later reading as a sample. With window_ns>0,
   the first later reading opens a window at its local time, becomes candidate
   and returns pending with error_ns=0. Within the half-open window, replace
   the candidate only for a **strictly smaller signed** phase error, not smaller
   absolute error. Ties retain the earlier candidate. Loop mapping stays fixed.
4. At elapsed local >= window_ns, feed the old candidate, return its result,
   then open the next window with the triggering reading. Compute the new
   candidate error against the mapping **after** the flush. Window boundaries
   use exact elapsed comparison even across the signed-time range; do not
   overflow start+window. No timer/flush API exists: the final pending candidate
   is not fed without another boundary reading. Returned phase error and last
   accepted time belong to the candidate, not necessarily the triggering input.
5. If feeding would overflow the integer local anchor, raise PllOverflowError
   and commit nothing, including the triggering reading, candidate replacement,
   order coordinates or an earlier outlier run.

### Feeding a sample

Let e be its unrounded binary64 phase error in ns.

* If abs(e)>outlier_threshold_ns, it is an outlier. A run continues only when
  abs(e-e_first)<=threshold, measured against the **first** error of the run;
  otherwise start a new run of length 1. On reaching step_after, re-anchor
  exactly to the fed sample, keep y, clear lock/jitter/outlier run, record the
  sample local as last accepted and return stepped. Otherwise return rejected:
  mapping, lock, jitter and last accepted do not change, but outlier metadata
  and successful-input order do. An inlier ends the run only on successful feed.
* For an inlier let dt be local seconds since last anchor/step/loop update.
  If dt>0, compute using the **old mapping**:

  ```text
  wn = 2*pi*bandwidth_hz
  x = min(0.5, wn*dt)
  kp = min(1, 2*(damping*x))
  y_new = clamp(y - (x*x/dt)*e/1e9, -max_offset_ppm*1e-6, +max_offset_ppm*1e-6)
  v = displacement_old(remote) + kp*e
  whole = round_away(v)
  I0_new = I0 + whole; frac_new = v-whole; R0_new = remote
  ```

  Check I0_new against signed 64-bit before committing; set the update
  reference time to sample local. The capped product is essential for sparse
  readings and extreme finite gains; avoid overflow/NaN intermediates changing
  the capped result. In particular do not evaluate `Inf*0` by capping dt first.
  All positive finite bandwidth/damping inputs must work, including binary64
  extremes. With dt=0 no mapping/rate/reference update occurs.
* For every accepted inlier (including dt=0), increment the lock run up to
  lock_count if abs(e)<=lock_threshold_ns; otherwise clear it. Equality counts.
* Jitter: first accepted inlier after anchor/step/reset initializes m=e*e;
  later accepted inliers update `m += (e*e-m)/16`. Set last accepted to sample
  local and return accepted. Anchor/step are not jitter samples. Jitter is 0
  until two inliers have been accepted, then round_away(sqrt(m)) ns, saturated
  to the signed-time range. Use the unrounded e, not observation.error_ns.

For accepted/rejected/stepped results, observation.error_ns is round_away(e)
saturated to [Imin,Imax]. Anchored/pending errors are zero. There is no exception
merely because a finite phase error exceeds the signed duration range.

### Queries, rounding, holdover and reset

`round_away` means nearest integer with half ties away from zero, **not Python's
built-in round**, which uses ties to even. Mapping rounds displacement, not
absolute time:

* local(r) = I0 + round_away(frac + (r-R0)*Pn/(1+y)).
* remote(l) = R0 + round_away(((l-I0)-frac)*(1+y)/Pn).
* Both raise NotAnchoredError before anchoring and PllOverflowError if the final
  integer result does not fit signed 64-bit. Add rounded whole displacement to
  the integer base exactly, preserving base low bits. A displacement outside
  signed 64-bit is allowed if cancellation yields a fitting result; the Go
  wide-displacement behavior must be retained. Do not reject solely because
  the displacement itself exceeds Imax.
* offset returns y. trim returns round_away(y*10**12), clamped to
  ±999_999_999_999. Thus every follower trim is in pacer input range, even near
  max_offset_ppm's limit. Applying it can still fail if a pacer's new anchor
  overflows; this is not an atomic two-controller transaction.
* state(now) is holdover iff anchored and now-last_accepted>holdover_after_ns,
  comparing elapsed exactly without signed overflow. Equality is not holdover;
  earlier now is allowed and does not mutate history. Otherwise return locked
  if lock run reached lock_count, acquiring if not (also before anchoring).
  Pending/rejected readings do not refresh last accepted. Holdover does not
  alter the mapping; extrapolation continues with the last rate estimate.
* reset clears mapping, y, order, pending window, outlier run, lock and jitter;
  retains configuration. Earlier readings may anchor afresh.

Binary64 follower estimates are not exact rational time and arbitrarily distant
extrapolation is not nanosecond-accurate. Round trips can lose ticks/ns; no exact
inverse or cross-platform bit-identical float guarantee is made. Boundary
rounding, saturation and integer anchors are nevertheless contractual. For
example a 0.5 ns period with anchor `(local=1,remote=0)` maps remote -1 to
`1+round_away(-0.5)=0`; anchor `(-1,0)` maps remote 1 to 0.

### Cross-module success and failure

```python
from dataclasses import replace
from pll import (Follower, Pacer, Status, State, default_follower_config,
                 units_per_second, OrderError, InvalidArgumentError,
                 NotAnchoredError, ConfigError)

rate = units_per_second(1000, 1)
f = Follower(replace(default_follower_config(rate), bandwidth_hz=1.0, damping=1.0))
try:
    f.local(0)
except NotAnchoredError:
    pass
else:
    raise AssertionError("unanchored query must fail")
assert f.observe(0, 0).status == Status.ANCHORED
obs = f.observe(1_001_000_000, 1000)  # 1 ms late; dt=1.001 s, x=0.5, kp=1
assert (obs.status, obs.error_ns) == (Status.ACCEPTED, 1_000_000)
assert f.local(1000) == 1_001_000_000
assert f.trim() == -249_750_250  # y = -0.25 / 1.001 * 0.001
p = Pacer(rate)
p.claim(1000)
p.set_trim(f.trim())
assert list(p.claim(2).all()) == [(1000, 1_000_000_000), (1001, 1_001_000_249)]
before = (f.offset(), f.local(1000), p.next_due(), p.trim())
try:
    f.observe(1_001_000_000, 1000)  # remote did not increase
except OrderError:
    pass
else:
    raise AssertionError("order must fail")
try:
    p.set_trim(1_000_000_000_000)
except InvalidArgumentError:
    pass
else:
    raise AssertionError("trim must fail")
assert before == (f.offset(), f.local(1000), p.next_due(), p.trim())
try:
    Follower(replace(default_follower_config(rate), bandwidth_hz=0.0, lock_count=0))
except ConfigError as exc:
    assert (exc.field, exc.reason) == ("bandwidth_hz", "must be finite and > 0")
else:
    raise AssertionError("config must fail on its first invalid field")
```

Additional deterministic workflows, each starting with a fresh follower:

| Inputs/settings | Promised outcome |
| --- | --- |
| Default 1000 ticks/s; observe(0,0), then (k*10_000_000,k*10) for k=1..8 | Anchored, then eight accepted errors 0; offset/trim/jitter 0; locked at 80 ms. At now=5_080_000_000 still locked, at 5_080_000_001 holdover. |
| Same rate/defaults; anchor(0,0), then (10_000_000,2010), (20_000_000,2020), (30_000_000,2030) | Errors -2_000_000_000: rejected, rejected, stepped; y stays 0; local(2030)=30_000_000; acquiring, jitter 0. |
| Rate 10**9, window_ns=4; (0,0),(1,1),(4,4),(5,5) | Anchored, pending, pending, accepted. Equal errors keep candidate (1,1); (5,5) starts next window. Last accepted=1, not 5. |
| Rate 10**9; anchor(Imax,0); local(1) | PllOverflowError, state unchanged. |

## Ownership, effects and concurrency

Pacer and Follower each need one owner; aliases refer to the **same mutable
controller**. No thread safety, GIL-based transaction guarantee or async-task
synchronization is promised. Serialize calls externally or protect controllers
with a caller-owned lock. Copying/pickling controllers and persistence formats
are unsupported. Rate, Span, FollowerConfig and Observation are immutable
values; share them read-only, and old spans remain valid while a pacer changes.
No mutable caller configuration is retained. Results do not retain payload data.

The library does **no I/O, network access, timers, sleeping, subprocess/process
creation, threads, implicit clock reads, environment reads or credential access**.
It keeps only in-memory timing/config/history and touches no payloads. The
caller supplies monotonic elapsed ns, origin alignment, counter unwrapping,
clock acquisition, wakeups, cancellation, backpressure and transport adapters.
The pacer accepts an earlier now without rewinding; the follower rejects
backwards input, so choose clocks/adapters accordingly.

Build/install/test tools are different: Python may write `__pycache__`, pip can
write environment/build/cache files, tests consume CPU and may write controlled
fixture/cache outputs. None of these are promised library runtime effects.
No network or credentials are required by the deterministic checks.

## Verification

Run the deterministic standard-library tests from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_tree.py
```

Tests cover exact pacing against an independent rational oracle, follower
models and boundary cases, failure preservation, README examples and replay of
pinned public-Go fixtures. Finite fixtures are not proof of universal parity
or portable performance. See [delivery evidence](https://github.com/Version2beta/pll-python/blob/release/0.1.0/docs/stage3-verification.md)
for historical checks and their numerical limits.

To build a local distribution, use an existing build environment containing
[scripts/build-requirements.txt](https://github.com/Version2beta/pll-python/blob/release/0.1.0/scripts/build-requirements.txt), then run:

```sh
python -I -m build --no-isolation --sdist --wheel --outdir "$DIST_DIR"
```

Build from a separate source copy and choose an external output directory to
keep build artifacts outside the checkout. Build dependencies are not runtime
dependencies. No registry release is claimed.
