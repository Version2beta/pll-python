# Current direct-request CLI contract

The user explicitly requested an equivalent of `../pll/cmd/pllpace` using the
delivered library. README's Real-time pacing command section is the current
contract for `pll/pllpace.py`, console script `pllpace = pll.pllpace:main`, its
stdlib tests and packaging guard updates. Core library production bytes and
existing APIs/tests remain unchanged. Explicit invocation effects are separate
from the effect-free library. No simulator, benchmark product, release,
dependency, version bump or model runner is introduced. Full inventory is now
60 tests; `tests.test_pllpace` adds ten bounded clock/writer/localhost checks.

The sections below record completed historical kits. Their writable/protected
paths and no-entry-point scope are historical, superseded only for this explicit
CLI addition and its coherent docs/tests/packaging verification changes.

---
# Stage 3 subordinate supporting contract

README.md Decisions, numerical contract and Stage 3 operations are authoritative.
Stage 1/2 code and all 43 tests remain byte-identical. No production repair is
allowed: any disagreement blocks for review before change or relaxed tolerance.

Complete/protected: all pll/*.py, all prior tests, fixtures, Go harness and case
generator, schema loader, distribution judge, MANIFEST.in, docs and runner.
Writable: scripts/replay_corpus.py, pyproject.toml, PROGRESS.md only.

| Promise | Check/task |
| --- | --- |
| All preceding APIs/effects/examples | unchanged T1–T6/F1–F6 (43 tests) |
| Canonical schema, complete artifacts, fixed seeded inputs, independent Fraction/Decimal | tests.test_corpus (7 tests), S1 |
| Public Go replay parity with normalized shared domain | S1 replay_file(path)->int returns 2299 checked rows, raises ValueError malformed schema, AssertionError disagreement with reproduction |
| Distribution metadata/archive/install/examples | S2 check_distribution.py |
| Full preserved + new stage | S3 last: 50 tests and build/install judge |

S1 must use complete corpus_schema.load/verify_artifacts then public pll APIs for
each case. Initial row is reduced Rate plus string, or normalized error. Config
construction adds one error row on failure; otherwise one result per operation.
Rate/Span results and operation args use canonical decimal strings; binary64
inputs/results use 16 lowercase hex bits (including config NaN/infinity/-0).
New controller per case, retained spans indexed in successful issuance order.
all is bounded by supplied limit; never materialize huge spans. Case tolerance
applies only to specified numerical fields, never category/status/state/errors:
exact by default; moderate error/local 1ns, remote 1tick, offset 1e-12, jitter 2ns;
extreme source-matrix local 1ns/offset 1e-20 only. Trim remains exact. No silent
zip truncation or skipped cases. Return number of checked result rows.

Go errors normalize to invalid_rate/invalid_argument/overflow/order/not_anchored;
ConfigError to config plus Go field and exact reason (Python field mapping:
Nominal=nominal, Bandwidth=bandwidth_hz, Damping=damping,
MaxOffsetPPM=max_offset_ppm, Window=window_ns,
OutlierThreshold=outlier_threshold_ns, StepAfter=step_after,
LockThreshold=lock_threshold_ns, LockCount=lock_count,
HoldoverAfter=holdover_after_ns). Return tags and string arrays are supplied.
Python exceptions vs Go sentinel errors, strict bool/type/envelopes, frozen values,
span index exceptions, iterator forms, unknown enum construction, zero-value
controller semantics and signed64 config count baseline are not raw Go parity.
Only shared valid signature types/envelopes are generated; prior Python tests
retain Python-only coverage. Go cannot override any approved Python promise.

S2 pyproject: setuptools.build_meta, requires setuptools==84.2.1 and wheel==0.48.0;
project name pll-python/version 0.1.0/description exact rational pacing and clock
following/readme README.md/requires-python >=3.11/license MIT/license-files LICENSE;
no dependencies, scripts, entry points or optional runtime requirements. Explicit
packages=["pll"], no automatic discovery, include-package-data=false. Supply PEP
621/639 metadata; no custom backend. MANIFEST.in is complete. Source and all pll
files must retain bytes; archive only public package, README, LICENSE, metadata.
Build-only tools are pinned in scripts/build-requirements.txt; judge requires
PLL_BUILD_PYTHON absolute external interpreter and performs no provisioning.

Independent checks are bounded, not exhaustive. Fraction tests independently
check corpus initial spans, Decimal 110-digit checks crosscheck source gain
matrix; retained moderate independent-model/Decimal/Fraction tests still run.
Final task replaces preceding whole-tree task. Metadata/replay are new work;
complete generated data has no invented implementation task. Stop after review;
no publishing, devices, release automation, provider/model call or live loop.

---
## Historical Stage 2 contract (superseded scope/operations, retained precision)

# Stage 2 supporting contract — pacing preservation and complete Follower

README.md is authority, including approved Decisions, Public API, config table,
Follower state machine/numerical contract, verification tolerances and Stage 2
kit operations. Pacing remains delivered/protected; follower work is complete scope.
No partial-follower exceptions.

Complete/protected: existing values/errors/exports, new _follower_values.py and
all delivered pacing production modules. Writable implementation: _follower.py
and new private follower helpers only, plus PROGRESS.md. No dependencies.
Default config, constructor and all methods keep the supplied signatures.
Config validates each field type/envelope/semantics before moving to the next;
other calls check all types, all signed64 envelopes, then semantics. Enums
reject bool/non-int before member lookup; unnamed byte values are supported.

Use pinned follower.go evaluation order, not obsolete upstream SPEC dt capping.
Subtract integer coordinates when signed64 fits; otherwise float(a)-float(b).
Predict displacement ((ticks*Pn)/(1+y))+frac; phase error uses displacement,
never absolute float prediction. Round ties away without losing already-integral
float low bits, add to integer base exactly and check final signed64 range.
Capped x/kp intermediates may be positive infinite; do not reject valid extreme
finite gains or compute Inf*0 via capped dt. Commit no state before all checks.

| README promise | Task | Source-named checks |
| --- | --- | --- |
| Prior exact pacing and examples, retained exact segment regression | T1–T6 | Original 29 tests; only obsolete export assertion updated |
| Defaults, frozen values, byte enums/errors, field-order validation | F1 | test_follower_config.py (2) |
| Anchors >2**53, ties/wide cancellation, validation/order/retry | F2 | test_follower.MappingTests (2) |
| Accepted loop, lock/jitter/holdover/reset, outliers/steps/saturation/rollback | F3 | test_follower.LoopTests (3) |
| Half-open windows, signed minimum/ties, postflush mapping, transactional flush | F4 | test_follower.WindowTests (2) |
| Independent moderate model and high precision extreme gains, clamps | F5 | test_follower_models.py (3) |
| Remaining README fence, cross-pacer and representative import/runtime effects | F6 | test_follower_workflows.py (2) |
| Whole Stage 1+2, syntax, whitespace and protection inventory | F7 last | all 43 tests |

Moderate-model fixture tolerances: error/local <=1ns, remote <=1 tick,
offset <=1e-12, jitter <=2ns. Extreme-gain source matrix only: local <=1ns,
offset <=1e-20 with Decimal precision 110 digits. Every classification,
hand-derived boundary and integer anchor assertion is exact. No universal
follower accuracy bound. No generated Go corpus, packaging, release, device,
performance or exhaustive effects/security claim. Stage 3 remains reviewed
corpus/packaging/release work, not deferred follower behavior.

## Retained pacing constraints

The private protected issuance seam supplies Rate._make(num, den),
Span._make(first, count, segment) and _Segment(start, anchor, numerator,
denominator, trim). They are complete unchecked constructors for validated
internal use. Segment numerator/denominator represent exact ns period; numerator
and denominator are positive. Span.time/all dispatch to implementation functions
span_time/span_all. all must call Span.time only when an item is requested, not
at iterator creation or for unconsumed items. Production and tests do not share
timing helpers. Protected value fields are not a new public API.

## Precision and validation

U=2**64-1; Imin=-2**63; Imax=2**63-1. Every multi-argument operation checks all
argument types, then all input envelopes, then semantics, in signature order in
each phase. Bool is rejected, int subclasses accepted. Normalize to
plain ints if useful; manually forged/private-field mutations have no timing
guarantees, as in the README. (Follower config is field-by-field; float subclasses are accepted.)

Rate terms/count/cap/keep use 0..U; time and trim use Imin..Imax. Invalid types
raise TypeError, envelope errors built-in OverflowError, zero rate terms
InvalidRateError, zero claim/cap or negative now or trim outside (-10**12,10**12)
InvalidArgumentError. Span.time differs: all integer indices outside 0..count-1
raise IndexError, even beyond the unsigned envelope. No negative indexing.
Pacer requires a Rate and rejects Rate() as InvalidRateError.

Use README's exact rational timing and floor/ceiling rules, unbounded products,
slot-U reservation, cursor-U due/skip errors only when due, claim last-floor
check, next_due ceiling check and changed trim floor-anchor check. Equal trim is
a true no-op even when cursor time cannot fit. set_trim at cursor U is allowed
if floor fits; next_due at U always overflows. due/skip exclude U from available
count. Empty due first is the cursor. All failed operations preserve controller
state and existing spans; constructors expose no partial successful result.
Span issuance must not enumerate its extent. Old spans retain immutable timing,
can outlive controllers; fresh all iterators advance independently and lazily.
Controllers are owned mutable aliases, no synchronization/copy/pickle promises.
