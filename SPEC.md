# Stage 1 supporting contract — exact pacing

**Subordinate to README.md**, especially Decisions and review gate; Public API;
Types, bounds and exceptions; Exact pacer contract; both pacing example sections;
Ownership, effects and concurrency; and Kit operations. Those approved README
promises are authority. This file is binding only consistently with them. A
conflict or new decision blocks work; record it in PROGRESS.md and stop for
operator/author review. Never change tests/README to fit implementation.

## Scope and seams

Implement only Rate factories, exact Pacer and immutable lazy Span. Import `pll`,
CPython 3.11+, standard library only, direct root import without installation.
Follower/config/status/state/observation and follower-specific errors are absent.
No model, clock, I/O, environment, thread, subprocess, transport, payload,
packaging/build backend, remote access or release work belongs to this stage.

Complete; do not change: pll/__init__.py (exact nine-name __all__), pll/_errors.py
(domain classes/code/messages), pll/_values.py (frozen slot-based Rate, Span and
private _Segment seam). README, SPEC, PROMPT, tasks, LICENSE, .gitignore, tests,
fixtures, docs and scripts are protected, including all approved future READMEs.
PROGRESS.md is writable. The coder implements pll/_rate.py, pll/_span.py and
pll/_pacer.py; new private implementation helpers are allowed. Keep public names,
signatures and contract comments. No public constructor arguments for Rate/Span.

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
guarantees, as in the README. (The future follower config is field-by-field and
float subclasses are accepted, but no follower validation is implemented here.)

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

## Promise/check map and task order

All commands and exact per-test stdout observations/counts are in tasks.json.
The protected runner prints PASS only from unittest.addSuccess, rejects wrong
suite counts, skips, expected failures and zero tests. Exit 0 alone is insufficient.

| Approved README promise | Task | Acceptance source/checks |
| --- | --- | --- |
| Rate reduction/string/sentinel, exact factory equivalence, U terms, immutability, type/envelope/semantic precedence; stage export/signatures; errors | T1 | tests/test_rate.py, 6 tests |
| Owned controller initialization, contiguous claims, future claims, exact ceil, atomic failures, huge lazy extent and floor-fit/ceil-overflow | T2 | tests/test_pacer_claim.py, 5 tests |
| Floor timing incl repeats, immutable independent spans, sentinel/empty/index validation, fresh lazy/early-stop iterators and cheap U extent | T3 | tests/test_span.py, 4 tests; fixtures/pacing.json |
| Exact due vs floor/ceil neighbors, earlier-now backlog/cap, alias ownership, newest keep/keep=0, empty first, multiphase validation/rollback, due at U | T4 | tests/test_pacer_due.py, 5 tests |
| Floor anchoring, no-op repeat trim, retained spans, extreme trim/rates, overflow rollback, cursor U trim | T5 | tests/test_pacer_trim.py, 5 tests |
| Exact oracle/invariants across 1,280 seeded mixed operations and retained spans, independent neighbor checks; both README pacing fences; representative prohibited effects/source hashes | T6 | tests/test_models.py (2), test_readme.py (1), test_effects.py (1); tests/stage_suite.py aggregates exactly 4 |
| All prior promises together, syntax/whitespace and full protection inventory | T7 last | scripts/check_tree.py and scripts/run_tests.py all 29 |

The Fraction model evaluates the formula independently and binary-searches due
slots instead of sharing production inverse-period arithmetic; exact results and
error categories are required. Hand-derived fixtures and floor/ceil boundary
checks cross-check it. README tests extract/run exactly the two pacing Python
fences (not doctest, not future follower examples). Large spans are sampled, not
iterated. Harness commands disable bytecode, compile source in memory and must
not change the source tree. External verification snapshots the delivered tree
before/after task commands and unchanged runner --check (excluding only .git
and .loop artifacts); the runtime-effect test also compares source hashes.

## Limitations and decisions

No previous Python stage exists. No Go-generated differential corpus is claimed;
fixtures are hand-derived from equations/examples with pinned provenance. Tests
provide useful evidence, not exhaustive proof or a process/security sandbox.
No live models, installed build, performance, all-interpreter matrix or real-device
trial is verified. Future follower equations/config/precision policy, differential
corpus, distribution/release/backend and integration choices return to author
review before affected tasks. Local freedom includes private helpers and exact
integer algorithms within the complete seam; it never includes changing approved
behavior/protections or weakening tests for a reference defect.
