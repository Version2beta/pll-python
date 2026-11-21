# Historical Stage 1 delivery and verification

This document records Stage 1 only. Its absent-Follower/no-owner-Git statements
below describe that historical delivery, not the current checkout. Complete
Stage 2 Follower and owner Git history are now delivered; see
[Stage 2 delivery evidence](stage2-verification.md) for current status.

## Historical Stage 1 implementation delivery

Stage 1 exact Rate/Pacer/immutable lazy Span is implemented and delivered in
`/Users/rob/Development/pll-python`. Direct root `import pll` uses only the
standard library; no packaging/backend/install or distribution is claimed.
Follower/config/status/state/observation and follower-specific error exports
remain absent. Stop for author review before Follower or another stage.

The independently accepted source is sandbox
`/tmp/pll-python-stage1-run.RdLnsJ/implementation`, branch
`stage1-exact-pacing`, HEAD `11ac05ab686810a73303949cf2c166bafa48f981`.
Only `pll/_rate.py`, `pll/_pacer.py`, `pll/_span.py` and `PROGRESS.md` were
transferred verbatim. README and this verification document were then updated as
supervisor documentation maintenance outside the coder loop; no new loop was
needed or run. PROGRESS retains its historical attempt wording verbatim.

Fresh delivery evidence and complete pretransfer kit snapshot:
`/tmp/pll-python-stage1-delivery.kTAGVmjQ/`. Before edits, all 29 inventoried
owner paths exactly matched both repair `owner-final.json` and
`final-kit.sha256` in `/tmp/pll-python-stage1-repair.7pcgemkh/`. No unexpected
user kit change was found. `owner-before/` retains all 29 original files;
`owner-before.json` hashes every owner file, including `.wtha/`, without
exclusions. `validate_delivery.py`, `commands.json`, per-command stdout/stderr,
`validation-before.json`, `validation-after.json`, `owner-final.json`,
`current-kit.sha256` and `changed-paths.json` record the fresh checks.

Fresh commands (from owner root unless stated), with bytecode disabled:

| Command / observation | Delivery result |
| --- | --- |
| `python3 -B scripts/run_tests.py all 29` and `python3.11 -B scripts/run_tests.py all 29` | Each: 29 explicit per-test PASS rows and `PASS COUNT 29` |
| `python3 -B -m unittest discover -s tests -v` and Python 3.11 equivalent | Each: 29 tests, OK; includes exact stored-segment regression and both extracted pacing README fences |
| `python3 -B scripts/check_tree.py` and Python 3.11 equivalent | Each: 25 protected paths, syntax/whitespace pass |
| `PYTHONPATH=/Users/rob/Development/pll-python pythonX -B /tmp/pll-python-stage1-repair.7pcgemkh/interface_check.py` for both interpreters | PASS INTERFACE: 48k batches/ceiling, byte starts, skip/trim/retained spans, rollback/retry, U-sized lazy span |
| Separate fresh `import pll` with that owner PYTHONPATH for both interpreters | Verified exact owner `pll/__init__.py` path, nine-name exports and no Follower export |
| `PYTHONDONTWRITEBYTECODE=1 bash scripts/loop.sh --check` in committed sandbox, once per interpreter via external PATH shim | Each: seven pass rows; unchanged runner, no models |
| `cmp scripts/loop.sh /Users/rob/.pi/agent/skills/readme-loop/scripts/loop.sh`; `bash -n scripts/loop.sh` | Identical runner and valid shell syntax |
| External full owner hashes/path inventories around every command | Unchanged, including `.wtha/`; no new bytecode or unexpected paths |
| Final comparison against pretransfer snapshot and accepted sandbox | Exactly six approved changed owner paths; all 27 other-than-README/verification kit files equal sandbox bytes; clean sandbox checkout/index |

Runtimes observed: CPython 3.15.0 (`python3`) and 3.11.15 (`python3.11`).
The reproducible external validation command is:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/pll-python-stage1-delivery.kTAGVmjQ/validate_delivery.py
```

Delivered production SHA-256 (also byte-compared to accepted sandbox):

```text
f379b25de37f970d9bf26f07cde47fc2a60a766dff4b9fc418ad210b525bc3f2  pll/_rate.py
1dd96e53df0063dd7f4b66cb9edb8daa285c91d88d17c34f3909852916e9ef5c  pll/_pacer.py
a8d47dae9d25b5bfd5cea5ed5a31b03636b891c7764a73c070d40fc590bafa20  pll/_span.py
```

Owner remains without `.git`; committed history stays in the sandbox. The
unchanged runner cannot honestly perform its Git-based ignore check in owner;
it was not run there and no Git initialization or ignore workaround was made.
Direct owner checks above establish delivery without claiming an owner runner
pass. Sandbox protected files match owner except the two documented post-loop
documentation updates. No owner staging, commits, installs, remotes, model calls,
new tests, inventory changes or future-stage work occurred. All 31 owner files
remain present; only the four transferred files and two documentation files
changed. `.wtha/` and all unrelated owner files are byte-preserved.

Limitations remain: no installed packaging/distribution, exhaustive import or
security proof, Go-generated differential corpus, arbitrary interpreter matrix,
Follower, performance, release or real-device verification. The representative
runtime-effect trap starts after import; fresh direct import success is not an
import-effects trap. Historical reference checks establish feasibility only;
Stage 1 implementation claims are bounded by the historical delivery evidence above.

## Historical preparation verification

The following records the original **kit feasibility evidence**, not current
owner status. At preparation the owner contained intentional stubs and had no
Git repository. That preparation launched no live loop or model call; private
reference/raw evidence remain at `/tmp/pll-python-kit.kIGWjY/`. Revised
enforcement and isolated repair evidence follow this historical record.

## Identity and boundaries

- Upstream pinned/read-only: `../pll`, SHA
  `971282632129110794c9d6edd22026e9de2359be`. Existing untracked `docs/` was
  observed and preserved; no upstream files/remotes were changed or fetched.
- Skill source: `/Users/rob/.pi/agent/skills/readme-loop/`.
- `scripts/loop.sh` is byte-identical to skill `scripts/loop.sh`, SHA-256
  `4ed33daa824bd8ed999c141cf4abd55921981f5e8de86948408552b52dbb207f`.
- Read kit-format source SHA-256:
  `972367a9a45222b3070518ea3f632a2c974c2869aa0d39ba775dcf061a7de199`.
  Private source snapshots were compared byte-for-byte with installed sources.
- Local runtimes checked: CPython 3.11.15 and 3.15.0. Standard library only;
  no dependencies installed. Bash/Git/jq/timeout were already available.
- Disposable `stubs/` and `reference/` fixture Git repositories only. Commits
  establish fixture baselines, not owner commits. Owner `.wtha/` was untouched
  and is deliberately absent from the 29-file delivery inventory.

## Observed checks

| Command / observation | Result |
| --- | --- |
| Each of the seven exact `tasks.json` commands on supplied stubs | All seven nonzero, including final whole-tree gate; not vacuous success |
| Unchanged `bash scripts/loop.sh --check` on stubs | Exit 1, seven FAIL rows |
| Each task on private reference | All seven exit 0; every full-line stdout expectation matched |
| Same unchanged runner `--check` on reference | Exit 0, seven pass rows; also exercises every earlier task and kit checks |
| `python3 -B scripts/run_tests.py all 29` on reference | 29 explicit per-test stdout PASS observations and `PASS COUNT 29`; no skips/expected failures |
| CPython 3.11 direct whole stage and unchanged runner via private python3 PATH shim | 29 PASS observations; seven passing judge rows |
| `python3 -B scripts/check_tree.py` | Syntax compiled in memory, whitespace clean, all 25 protected paths match JSON-decoded grep EREs; four intentionally writable paths |
| External fixture snapshots around every task/runner check | Full source bytes/path inventory unchanged, excluding only Git and `.loop/` artifacts; no staged or dirty fixture files |
| Manual public-interface check (`interface_check.py`, private) | PASS: 48k due batches/ceiling; byte-rate starts; skip/trim/retained spans; invalid-trim rollback and valid retry; cheap U-sized span with lazy first item and sampled last floor |
| `cmp scripts/loop.sh` with skill source; `bash -n` | Identical runner; shell syntax valid |
| Skill `bash scripts/test_loop.sh` using disposable fake-coder fixtures | All 26 cases passed; all 26 deliberate regressions caught; no live model calls |

Task test counts are T1=6, T2=5, T3=4, T4=5, T5=5, T6=4; T7 runs all 29
(last, not an additional test). The independent Fraction oracle binary-searches
due slots and checks 1,280 seeded mixed operations across eight extreme/ordinary
rates, plus separate neighbors. Both script-style pacing README fences execute.
Hand-derived fixtures are not a Go-generated differential corpus.

The first fake-coder suite invocation was interrupted after partial output; it
had no completion summary and was not counted as success. No process remained
when resumed. A complete fresh rerun produced the 26/26 summary above; the
partial log is retained separately for honesty/audit.

## Evidence and rerun

Delivery inventory: [kit-files.txt](kit-files.txt). The private evidence root has:

- `verify.py`: copies only that inventory into disposable stub/reference Git,
  runs every task plus the unchanged judge, checks exact observations and source
  nonmutation, and verifies no staged files. Reference code lives separately in
  `reference-code/`, never in the delivered kit.
- `stubs-T*.stdout/.stderr`, `reference-T*.stdout/.stderr`, and corresponding
  `*-judge.*`; final aggregate `verification-final.log`.
- `reference-python311.*`, `reference-python311-judge.*`,
  `interface.stdout/.stderr`, `interface_check.py`, `matrix-final.log`.
- `fake-coder-regressions.log` (interrupted) and
  `fake-coder-regressions-resumed.log` (complete 26/26).
- `source-identity.log`, `final-kit.sha256`, private runner/format source copies.

Historical preparation owner-tree checks (then expected to fail on stubs;
these now pass on the delivered implementation):

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_tree.py
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/run_tests.py all 29
```

For an independent reference review while the private evidence directory exists:

```sh
cd /tmp/pll-python-kit.kIGWjY/reference
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/run_tests.py all 29
bash scripts/loop.sh --check
PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 python3.11 -B ../interface_check.py
```

Re-run the inherited runner regression suite without models:

```sh
bash /Users/rob/.pi/agent/skills/readme-loop/scripts/test_loop.sh
```

At original preparation, no previous Python stage existed. Owner implementation,
installed packaging, model availability/live integration, arbitrary interpreter
matrix, exhaustive no-effect/security proof, Go differential corpus, follower,
performance and real-device behavior were unverified. Launch was withheld for
independent kit review and clean sandbox setup. That historical launch status
is not the status of the separately authorized isolated implementation run.

## Revised exact-segment enforcement

Original isolated-run evidence is preserved unchanged at
`/tmp/pll-python-stage1-run.RdLnsJ/RESULT.md`. Candidate
`5cd825c04de21963b09c39f95df6aa5f326c09c4` passed the original 29 tests but
stored nominal rather than exact trimmed ns period terms in `_Segment`.
Supervisor approval treats this as noncompliance with existing SPEC Scope and
seams and protected `pll/_values.py`, not a new contract choice.

The existing `test_floor_anchor_and_retained_spans` now checks positive terms
and rational cross multiplication against the exact formula for initial,
negative-trim, positive-trim and retained spans. It uses only the protected
issuance seam, accepts reduced or unreduced equivalent fractions and imposes no
additional controller layout. Test count stays 29; tasks/expectations, README,
SPEC, complete values and runner are unchanged. The runtime-effect test is
unchanged: it traps representative operations after import, not fresh-import
effects; source review remains necessary and is not exhaustive security proof.

Revised evidence is outside owner and coder kit at
`/tmp/pll-python-stage1-repair.7pcgemkh/`: `verify.py`, disposable `stubs/` and
`reference/`, per-task/runner logs, `verification.log`, source hashes and a
separate result record. Every task and unchanged runner fails on original
stubs; every task, unchanged runner and all 29 tests pass on the private
reference. External snapshots check tree nonmutation and no staged files.
Reference source and all original evidence are preserved. The revised test
also rejects the original candidate before any coder repair.

At that enforcement gate, only the verified test and verification document were
authorized for application to the isolated sandbox before a separately authorized
bounded unchanged-runner repair; owner production still remained stubs. The
revised external `RESULT.md` records that repair and final HEAD. Subsequent
independent review accepted the repair for the owner transfer documented above.
Original stub/reference/run/repair evidence is retained unchanged. Return to
author review after Stage 1; do not chain future stages.
