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
