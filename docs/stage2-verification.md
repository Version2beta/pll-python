# Stage 2 complete Follower kit — preparation evidence

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
