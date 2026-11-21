# Implementation progress

Kit prepared and privately verified; production files remain intentional stubs.
Append three lines per attempt: task id; work performed; remaining work/blocker.
No implementation attempts have been launched. New contract decisions block work.
T1
Implemented units_per_second and bits_per_second in pll/_rate.py: all types checked first (bool rejected), then 0..2**64-1 envelopes, then zero-term InvalidRateError, gcd reduction into Rate._make. tests.test_rate 6/6 PASS (COUNT 6); check_tree PASS.
Remaining: none for T1; Pacer/Span and T2-T7 untouched; no contract decision needed. Not committed or marked done.
T2
Implemented Pacer constructor (TypeError for non-Rate, InvalidRateError for Rate()), claim (type, then 0..U envelope, then zero/InvalidArgumentError, then U-cursor and last-floor Imax overflow checks, atomic cursor advance, lazy Span._make) and next_due (cursor U and ceiling Imax overflow) plus trim() reading the segment, using private floor/ceil helpers in pll/_span.py. tests.test_pacer_claim 5/5 PASS (COUNT 5); check_tree PASS; tests.test_rate still 6/6 PASS.
Remaining: due, skip, set_trim and Span.time/all (T3-T5) untouched; no contract decision needed. Not committed or marked done.
T3
Implemented span_time in pll/_span.py: _checked_int (TypeError for bool/non-int, int subclasses copied), then IndexError outside 0..count-1 with no negative indexing, then floor_slot_time(segment, first+i). Implemented span_all as a generator: range(count), one span.time(i) per requested item, yielding (first+i, time). tests.test_span 4/4 PASS (COUNT 4); tests.test_rate and tests.test_pacer_claim still 11/11 OK; check_tree PASS.
Remaining: Pacer.due, skip, set_trim (T4-T5) untouched; no contract decision needed. Not committed or marked done.
T4
Implemented exact due/backlog and newest-keep skip in pll/_pacer.py using integer inverse timing, lazy empty/capped spans, phased validation and atomic cursor-U overflow handling. Exact task command tests.test_pacer_due 5: PASS COUNT 5; prior rate/claim/span tests: 15/15 OK; check_tree protections/syntax/whitespace and git diff --check passed.
Remaining: no T4 blocker or new contract decision; set_trim and T5-T7 untouched. Not committed or marked done.
T5
Implemented set_trim in pll/_pacer.py with type/envelope/semantic validation, equal-trim no-op, checked old-cursor floor anchoring and atomic immutable segment replacement preserving issued spans. Exact task command: PASS COUNT 5; prior rate/claim/span/due tests: 20/20 OK; check_tree protections/syntax/whitespace and git diff --check passed.
Remaining: no T5 blocker or new contract decision; T6-T7 untouched. Not committed or marked done.
T5
Corrected pll/_pacer.py and pll/_span.py to store and consume exact trimmed segment periods, reduced on trim changes, preserving floor anchors, retained snapshots, equal-trim no-ops and atomic failures. Exact task command: PASS COUNT 5; prior rate/claim/span/due tests: 20/20 OK; check_tree protections/syntax/whitespace and git diff --check passed.
Remaining: no new contract decision or T5 blocker; T6-T7 untouched. Not committed or marked done.
F1
Implemented default config and field-by-field type, signed64 envelope and semantic validation with a frozen configuration snapshot in pll/_follower.py; exact task command passed both tests (PASS COUNT 2).
Remaining: F2-F7 follower mapping, loop, windows and numerical/workflow validation; no new contract decision or blocker. Not committed or marked done.
F2
Implemented integer-base mappings, ties-away rounding, wide cancellation, phased validation and transactional observations in pll/_follower.py, with required reset/query state and complete window/outlier/step handling rather than special-case shortcuts; exact task command passed (PASS COUNT 2), and git diff --check passed.
Remaining: F3-F7 loop/window/model/workflow and whole-suite validation have not been run; no new contract decision or blocker. Not committed or marked done.
F5
Converted outlier/run-agreement and lock thresholds to binary64 in pll/_follower.py to preserve pinned Go comparison behavior at signed64 boundaries; exact task command passed (PASS COUNT 3).
Remaining: broader regression/workflow and whole-suite validation not run in this attempt; no new contract decision or blocker. Not committed or marked done.

Stage 3 preparation (not a coder attempt): 43 preceding owner checks preserved;
protected deterministic Go corpus/schema/harness/tests and external build/install
judge added. S1 replay and S2 metadata remain stubs; S3 is the final gate.
No live loop/model calls; return verified preparation for parent review.

Stage 3 preparation repair after P1 review: complete schema guard now validates
provenance, operation/controller domains and result shapes before replay; focused
malformed tests run through replay_file. Production/prior tests/corpus unchanged.
Live launch withheld pending independent re-review; no coder/model attempt.
