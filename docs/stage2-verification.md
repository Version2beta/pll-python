# Stage 2 complete Follower — final delivery evidence

## Delivered status and provenance

Stage 2 is delivered on owner branch `stage2-follower`, after parent independent
acceptance (no review issues) of sandbox `stage2-implementation` at
`1094afb3db1ede7c96f4f2033131423b32e6c4e6`, located at
`/tmp/pll-stage2-live.xDEfgw/implementation`. Source/review/run evidence remains at
`/tmp/pll-stage2-live.xDEfgw/`, including `review.md`. Original implementation
commits are `346495e` (F1), `658e5f2` (F2), and `1094afb` (F5); the complete full
SHAs and transferred SHA-256 hashes are recorded in delivery `provenance.json`.
Owner started clean at `37fc53c417aecc6fd14fa6eb540fb4af5d8f894f`; every tracked
path matched that baseline and the prior owner-before hashes. Sandbox was clean,
its entire tracked source matched accepted HEAD, and its only changes from that
baseline were `pll/_follower.py` and `PROGRESS.md`. Those two files were transferred
byte-for-byte, without merge/cherry-pick or alteration of the attempt history.
README and verification documentation are authorized post-loop maintenance.

Complete Follower is available by direct root import, including windows,
outliers and steps. No packaging, release, broader Go differential corpus,
performance, real-device or exhaustive security/correctness claim is made.
Stage 3 remains deferred for author review. No new models, installs, remotes,
upstream writes or future-stage work were needed for this delivery. `.wtha/`
was not accessed, copied or staged; snapshots use explicit tracked paths only.

## Fresh owner validation

Delivery evidence: `/var/folders/vw/fh_b6s2s4l154vl9dl21lx480000gn/T/pll-stage2-delivery.uazbwzw1/` (outside owner). `owner-before/` contains only
explicit tracked-path snapshots; `owner-before.json`, `provenance.json`,
`commands.json`, per-command stdout/stderr and `validation-final.json` retain
hashes, exact commands and results. Reproduction script:
`/tmp/pll-stage2-validate-owner.py`. No private source was shipped in the kit.

Fresh checks executed from the actual owner root, with bytecode disabled:

| Commands / observation | Observed result |
| --- | --- |
| `python3 -B scripts/run_tests.py all 43` and `python3.11` equivalent | Both: 43 explicit PASS observations, `PASS COUNT 43`; no skips/expected failures |
| `python3 -B -m unittest discover -s tests -v` and `python3.11` equivalent | Both: 43 tests, OK |
| `python3 -B scripts/check_tree.py` and `python3.11` equivalent | Both: `PASS PROTECTIONS 34`, syntax/whitespace pass |
| `PYTHONDONTWRITEBYTECODE=1 bash scripts/loop.sh --check`, default and external Python 3.11 PATH shim | Both: all 13 T1–T6/F1–F7 rows pass; no model calls |
| External `interface_check.py` on both interpreters with owner `PYTHONPATH` | All three extracted README Python fences pass; asserts exact owner `pll.__file__` and `pll._follower.__file__`, not sandbox |
| Copied external `outlier_continuation_probe.py OWNER_ROOT` on both interpreters | Active outlier-run overflow/valid continuation passes for window_ns=0 and 2 |
| `cmp scripts/loop.sh` against installed skill; `bash -n scripts/loop.sh` | Byte-identical runner and valid shell syntax |
| `cmp` baseline snapshots of `_pacer.py`, `_rate.py`, `_span.py`, `_values.py`, `scripts/loop.sh` | Every file unchanged |
| Tracked source hashes and visible inventory around each validation command | No source or inventory mutation; no staged files |
| `git diff --check` | Pass |

Observed interpreters: CPython 3.15.0 (`python3`) and 3.11.15 (`python3.11`).
Transferred follower SHA-256:
`30939f80188ee271e6142e7f31a6d3be552991ef8db701ca2ca31ac5b480ca94`.
PROGRESS SHA-256: `3c3d07111d8a48daae8e1e48c79b161eec95ec4996cbb2ce9c36ae70bf9250de`.
The exact final diff paths are `pll/_follower.py`, `PROGRESS.md`, `README.md`,
`docs/stage2-verification.md`, and `docs/verification.md`. All other tracked paths,
including pacing, seams, tests, fixtures and runner, remain baseline-identical.
PROGRESS preserves original attempt wording as historical provenance; this
section records completed owner delivery. Stage 2 handoff stops here.

## Historical preparation evidence

The following sections record preparation only, before the isolated accepted
implementation run and final owner delivery; stub/private-reference and next-gate
statements below are historical, not current status.

## Scope and identity

Prepared on actual delivered Stage 1, **not** the private Stage 1 reference.
Owner Git initialization was explicitly authorized. Baseline `52dc8f5` on
`stage2-follower` commits only the 29 explicit delivered kit paths. This preserves
Stage 1 provenance: accepted source branch stage1-exact-pacing, revision
11ac05ab686810a73303949cf2c166bafa48f981, from the sandbox recorded in
[historical verification](verification.md). That document's no-Git and
absent-follower statements are historical, superseded by this overlay.

`/.wtha/` was added narrowly to .git/info/exclude **before** staging because
owner explicitly required private runtime state never enter commits. No contents
were inspected, copied or staged. No blanket staging was used. No remote,
installation, model/provider call, Go harness or live implementation loop ran.

Upstream `../pll` remains read-only at
971282632129110794c9d6edd22026e9de2359be. External verification compares every
tracked upstream file hash before/after and source identity; status is clean.
Delivered _rate.py/_span.py/_pacer.py/_values.py bytes match the baseline;
all pacing behavioral tests are unchanged. Only the obsolete nine-export and
absent-follower assertions in test_rate.py were deliberately updated.

## External evidence (not shipped to coder)

`/tmp/pll-python-stage2.h0poaS/` contains probe.py, reference_follower.py,
verify.py, inventory-only stubs/reference fixture Git repositories, every task's
stdout/stderr, both unchanged-runner judge logs, Python 3.11 logs, results.json,
source-identity.json and verification.log. No private reference is in kit-files.

Reproduce without models:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/pll-python-stage2.h0poaS/probe.py
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/pll-python-stage2.h0poaS/verify.py
```

The disposable arithmetic probe preceded reference/kit work: min-subnormal and
max-finite capped products, ties, wide cancellation, and compute-before-commit
overflow/retry arithmetic. It is feasibility arithmetic, not a production test.

## Observed validation

- Actual owner `bash scripts/loop.sh --check`: six prior pass rows, seven
  intentional follower/final FAIL rows, exit 1; raw logs retained externally.
- Public-interface manual script (interface_check.py, external) passes on both
  interpreters: lock/holdover equality, outlier-step sequence, windows and
  cross-pacer snapshots. This is private-reference use, not owner delivery.
- Stub tree: T1–T6 all pass (29 original tests); F1–F6 and final F7 all fail
  nonzero through exact task commands and unchanged runner --check. Stub failure
  is expected; the owner kit intentionally does not implement Follower yet.
- Private reference: all 13 task commands and all 13 unchanged runner judge rows
  pass. Final gate prints 43 explicit per-test stdout observations and
  `PASS COUNT 43`: 29 retained + 14 new tests, no skips/expected failures.
- CPython 3.15.0 and 3.11.15: whole reference stage passes, including unchanged
  runner --check under each interpreter (external PATH shim for 3.11).
- Syntax/whitespace guard prints `PASS PROTECTIONS 34` and
  `PASS SYNTAX AND WHITESPACE`; complete seams, delivered pacing, every README,
  test/fixture/doc/harness path are covered by JSON-decoded grep ERE patterns.
- Exact model/error/status boundaries remain exact. The 500-update independent
  moderate model uses only its stated local/error <=1ns, remote <=1tick,
  offset <=1e-12, jitter <=2ns tolerances. Decimal 110-digit source-specific
  36-case extreme-gain matrix uses local <=1ns and offset <=1e-20, not a
  universal accuracy claim. Initial one-update negative clamp expectation was
  corrected: a single capped update cannot reach -1; repeated samples test clamp.
- All three README Python fences execute: two pacing fences retained plus
  follower-to-pacer workflow. Runtime/representative fresh-import effects checks
  pass; this is not exhaustive security/import-effects proof.
- External inventory snapshots show source nonmutation around every command,
  no staged/dirty fixture files, unchanged owner inventory and upstream tracked
  hashes; .git/.loop artifacts are outside source snapshots.
- Runner byte-identical to installed skill (SHA256
  4ed33daa824bd8ed999c141cf4abd55921981f5e8de86948408552b52dbb207f).
  Skill kit-format SHA256
  972367a9a45222b3070518ea3f632a2c974c2869aa0d39ba775dcf061a7de199.
- `bash /Users/rob/.pi/agent/skills/readme-loop/scripts/test_loop.sh`: all 26
  fake-coder cases pass; all 26 deliberate regressions caught. Log retained
  externally. No real model calls.

## Next gate and limitations

Review this verified kit/revision before the isolated implementation loop using
README's exact pinned commands and existing spending limits. Preparation stops
here. Follower implementation is still stubs; passing private reference proves
bounded feasibility, not delivered implementation, live model availability,
Go differential-corpus parity, installed packaging, performance, release,
real-device results, exhaustive correctness or a process-security boundary.
Broader reviewed Go corpus and packaging/release remain Stage 3.
