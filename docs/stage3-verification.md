# Stage 3 — final owner delivery evidence

## Delivered status and provenance

Stage 3 is delivered on owner branch `stage3-verification`, following parent
acceptance of the independent reviewer (no issues). Accepted sandbox:
`/tmp/pll-stage3-implementation.Uf7owo/checkout`, branch `stage3-implementation`,
HEAD `ddfc6b3e75731ae5b63663e616a6daa76b349b27`, prepared owner baseline
`4677f227daafbc0ba266df5bada975f6ea9c6023`.
Owner implementation commit: `50ae1391d1b8e4661c5ad9719883c307d0e5cf23`.
Only scripts/replay_corpus.py, pyproject.toml and PROGRESS.md were transferred;
each was verified byte-identical. No merge/cherry-pick or protected-code changes.
The companion documentation commit updates README status and this record only.
No next stage is started; author review remains the next gate.

Accepted source/operator evidence: `/tmp/pll-stage3-implementation.Uf7owo/REVIEW.md`.
Independent review:
`/Users/rob/.pi/agent/sessions/--Users-rob-Development-pll-python--/subagent-artifacts/c70d4d92-8308-47d4-9c8e-735ea1d74d9a_reviewer_output.md`.
Fresh owner evidence and preserved artifacts (external, not in Git):
`/Users/rob/Development/pll-stage3-delivery-evidence-20261121-144326`.

## Fresh actual owner checks

CPython 3.15.0 (`python3`) and CPython 3.11.15 (`python3.11`) each passed:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/run_tests.py all 50
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check_tree.py
PYTHONDONTWRITEBYTECODE=1 bash scripts/loop.sh --check
PYTHONDONTWRITEBYTECODE=1 python3 -B -c 'import sys; sys.path[:0]=["scripts", "."]; from replay_corpus import replay_file; print("PASS REPLAY", replay_file("fixtures/go-public-api.json"))'
```

`validate.py` records exact commands/environment and source SHA256 snapshots
before/after every command in validation-results.json and ten snapshot files.
For the second pass, an external PATH shim names python3.11 as python3; runner
and task commands remain unchanged. Every source snapshot is identical around
checks: 50 explicit tests, discovery 50, syntax/whitespace/protection inventory,
all 15 unchanged judge gates and direct replay 2299 rows, on both interpreters.
Prior T1–T6/F1–F6 gates still account for 43 tests; seven corpus tests are new
in preparation, not changed during delivery. No tests/fixtures/guards/contracts
were edited. baseline-preservation.json proves all 22 production/prior-test
paths byte-identical to `878a652cf27c7587055ed7fe81e15b2fa5723168`.
owner-before.json records the clean tracked inventory; sandbox-before/after.json
and clean status prove the accepted sandbox stayed unchanged at its known HEAD.
No private runtime, upstream source, remote, provider or network was accessed.

Corpus remains 84 cases, 2202 operations, 2299 checked result rows; SHA256
`0a57a1d7ef6ed4b86745b00bdfe420cb005a1df87919851300efe06a0f9e853b`.
No fresh Go regeneration was performed during delivery. Historical regeneration
evidence below is distinct from fresh owner replay. Categories/status/state/trim
remain exact; only the approved per-fixture moderate and extreme numerical fields
have bounded tolerances specified by README/SPEC. No tolerance was relaxed.

## Fresh local distribution and preserved artifacts

Existing external pinned build interpreter (reused, not provisioned):
`/tmp/pll-stage3.I7Kron/build-env/bin/python`, CPython 3.11.15.
Verified versions: build 1.6.1, setuptools 84.2.1, wheel 0.48.0,
packaging 26.3, pyproject_hooks 1.3.3. No runtime dependencies/entry points.

Both judge passes freshly built wheel and sdist, rebuilt wheel from sdist,
inspected metadata/manifests/source bytes and installed offline/no-deps in fresh
external environments. Separate preservation command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B "/Users/rob/Development/pll-stage3-delivery-evidence-20261121-144326/preserve_distribution.py"
```

That external harness runs the unchanged check_distribution.main(), replacing
only its TemporaryDirectory context with a new persistent external workspace.
The exact explicit source copy and build/install/provenance/README checks are
therefore retained, not recreated approximately. distribution-final.log records
build commands (`-I -m build --no-isolation --sdist --wheel --outdir ...`, then
`--wheel` from unpacked sdist), manifests, and all four installed import paths.
Both direct and sdist-rebuilt wheels were installed `-I -m pip install
--no-index --no-deps` under 3.11 and 3.15 outside checkout, with PYTHONPATH unset;
`-I` probes assert site-packages provenance and execute all three README Python
fences. Fresh installed README examples and manifests pass after README updates.
Wheel metadata README payload and sdist README/source bytes were additionally
verified against the final owner README and production. distribution-snapshots.json
proves no source changes across these external builds/install checks.

Preserved under `/Users/rob/Development/pll-stage3-delivery-evidence-20261121-144326/distribution-final/`:

| Artifact (relative path) | SHA256 |
| --- | --- |
| dist/pll_python-0.1.0-py3-none-any.whl | a2761aa9cc522222e4d44ba41dbfc6d5c6343471497022c1252cf4b0e097b041 |
| dist/pll_python-0.1.0.tar.gz | eb6bd8530b167db6122c8c2934cc2ea157b830343bab74c84ea55069b2175952 |
| sdist-wheel/pll_python-0.1.0-py3-none-any.whl | a2761aa9cc522222e4d44ba41dbfc6d5c6343471497022c1252cf4b0e097b041 |

artifacts.json records absolute paths, hashes, sizes and inspected manifests.
These are local 0.1.0 artifacts, not registry availability or publication.
An initial *extra* metadata-payload assertion in the external evidence harness
failed because email.get_payload() decoded UTF-8 as ASCII replacement characters;
using get_payload(decode=True) correctly compares raw bytes. No project source,
judge, contract or tolerance changed. The fresh corrected preservation run passed;
the earlier run/log is retained separately and is not delivered artifact evidence.

## Limits and next gate

Bounded deterministic tests/corpus and local builds do not establish exhaustive
correctness/security, universal float accuracy, platform/device performance or
release readiness. No publishing, registry lookup, release automation, devices,
new provisioning, system install, provider call or next stage occurred here.
Artifacts/evidence/build environments remain external and must be preserved by
the operator if later needed. No build cache, wheel or evidence is staged.

---
## Historical preparation evidence (not current status or launch instructions)

Everything below records earlier preparation/repair and private-reference checks.
Statements about stubs, withheld launch, provisioning or pending review apply
only to those historical revisions, not the accepted owner delivery above.

### Stage 3 preparation evidence

Preparation only; no live implementation loop/provider calls. Stage 1/2 owner
baseline is 878a652cf27c7587055ed7fe81e15b2fa5723168. Stage 2 evidence remains
historical in stage2-verification.md. Production bytes and 43 preceding tests
are preserved; only replay and packaging metadata are implementation stubs.

Approved scope: deterministic public-API corpus and local wheel/sdist installed
verification. No publishing, release automation/devices or runtime dependencies.
All complete source/artifacts/tests/contracts are protected; local freedom only
scripts/replay_corpus.py and pyproject.toml, plus writable PROGRESS.md.

External evidence root: /tmp/pll-stage3.I7Kron (not copied to coder inventory).
Build prerequisite selection used bounded trusted PyPI index checks, then one
isolated external Python 3.11 venv install. Pins: build 1.6.1, setuptools 84.2.1,
wheel 0.48.0, packaging 26.3, pyproject_hooks 1.3.3. These available versions were
checked together; established setuptools supports explicit package inventory and
PEP 639 MIT metadata. Build tools only, not runtime deps. No system installation.
Exact command: `$BUILD_ENV/bin/python -m pip --isolated install --index-url
https://pypi.org/simple --no-cache-dir -r scripts/build-requirements.txt`.
Provisioning is separate from offline judge, which never installs prerequisites.

Corpus: 84 cases, 2202 operations, 2299 result rows. Canonical JSON decimal-string
integers and binary64 hex values; per-case tolerance/rationale. Fixed LCG32 seed
21274, recurrence recorded in payload. Generation command and Go version/platform,
pinned Go SHA, source/harness SHA256s are embedded, no unstable timestamp.
Corpus digest is fixtures/go-public-api.sha256. Source is public API only,
external module replace, GOPROXY=off GOSUMDB=off GOTOOLCHAIN=local. Observed Go
1.27.2 darwin/arm64 supports source go1.23 baseline. Each invocation executes
harness twice; two complete independent invocations compared byte-identical.
Go result replay is generation from identical stored inputs; Python private replay
checked 2299 rows before kit tasks. Two ports agreeing is not independent proof.
Independent checks include Fraction initial-span cases, Decimal 110-digit source
gain matrix and retained moderate model/Decimal/Fraction suite. This is broader
bounded coverage, not exhaustive correctness, security or real-device evidence.

Coverage includes rate/bits reduction/errors, pacer neighbors/backlog/earlier now,
skip/trim/error retry, huge counts and cursor/time overflow, retained span time/
bounded All, seeded pacing, follower full public operations/statuses/errors,
lock/holdover/reset, dt=0, windows/signed boundaries/ties, outlier first-reference/
steps/order, overflow repeated retry, wide cancellation, half ties at huge origins,
nonfinite/signed-zero config and extreme finite gains, noisy seeded moderate run.
Python-only types/envelopes/enum/value semantics remain in preceding tests.
No universal float bit equality or tolerance is claimed; categories are exact.

Validation results are recorded below after final verification.

## Verified kit results

- Actual delivered owner production, not Stage 2 private reference: all unchanged
  T1–T6/F1–F6 commands pass (43 tests). Git baseline comparison of all pll source
  and preceding tests is byte-identical. No production change or discrepancy.
- Stub kit unchanged runner `--check`: 12 retained rows pass; S1, S2, final S3
  fail nonzero. S1 fails on the required successful replay, S2 fails package
  metadata/manifest assertions, not absence of build prerequisites.
- External private reference only implements the two new task files: replay and
  pyproject metadata. All 15 unchanged-runner judge rows pass; 50 explicit tests
  pass on Python 3.15.0 and Python 3.11.15, including seven new corpus checks.
  It uses actual delivered production unmodified, not any Stage 2 reference.
- Reference distribution judge passes direct wheel and wheel rebuilt from sdist;
  each is installed `--no-index --no-deps` into fresh external Python 3.11 and
  3.15 venvs. All three extracted README Python examples pass with `-I`, unset
  PYTHONPATH and installed-site import provenance asserted. License, no runtime
  dependencies/entrypoints, explicit source bytes and manifests checked. The raw
  SDIST/WHEEL MANIFEST rows and installed __file__ paths are in ref-dist.log and
  reference-judge.log externally. No wheel/sdist or private reference is delivered.
- Source/harness hashes and corpus digest are checked; repeated complete offline
  Go generation is byte-identical (corpus-first.json/corpus-second.json). Active
  outlier-run failed feed is compared to failure-omitted control through step,
  exposing hidden rollback/order continuation. Statuses/categories stay exact.
- Runner matches installed skill byte-for-byte; inherited fake-coder suite passes
  all 26 cases and catches all 26 deliberate mutations (fake-runner.log). No model.
- Syntax/whitespace/protection check and git diff --check pass. Judge snapshots
  and upstream before/after hashes are retained externally. No source mutation,
  upstream writes, remotes, publication or system installs were needed.

Review this preparation branch before any live loop. Actual new functionality
is intentionally not delivered yet: stub failure/private reference success proves
bounded feasibility, not accepted coder implementation, model availability,
registry availability, universal interpreter/platform accuracy, exhaustive
security or real-device behavior. External prerequisites must be reprovisioned
if the disposable build environment is removed. There is no network in tests,
judge or Go generation. Only prerequisite provisioning used the trusted index.

Final hardening also asserts pyproject's explicit package inventory and backend/
project metadata directly, preventing auto-discovery from passing accidentally.
The final generator confines GOCACHE/GOPATH to its disposable temporary directory.
Preliminary harness builds used Go's normal build cache; no arbitrary cache
contents were searched/read as evidence. Final two-generation equality was
rechecked with isolated caches, and upstream source hashes remain unchanged.

## Preparation repair after independent BLOCK review

Review of revision `06b2da258b29202699b39dedb4d1a3ad21df1295` found P1:
malformed provenance and operation records could escape the complete loader,
causing arbitrary replay exceptions or skipped harness checks. Live launch stays
withheld. This is protected preparation maintenance, not a coder attempt or a
new contract, production repair, or tolerance change.

The complete loader now explicitly validates provenance shapes/values, the exact
three-file harness hash inventory, and the pinned Go source-manifest fingerprint;
no supplied path is read before that inventory check. Operation arities, numeric
signed/unsigned envelopes, controller compatibility, config shapes and supported
Nominal sentinel are checked before replay. Result rows validate operation tags,
status/state domains, signed/unsigned fields, normalized error shapes, retained
span references and extents. The loader does not catch arbitrary replay errors;
validly shaped but numerically wrong expected results still reach replay and
raise AssertionError. Malformed shared-domain data raises ValueError.

The existing malformed-schema test now exercises replay_file directly with
null/empty/wrong-shaped provenance, path/hash substitutions, negative unsigned
and overflowing signed inputs, incompatible controller operations, bad arity,
config and status/result shapes. Test-method count remains seven (50 whole-tree).
On the preceding guard this focused regression test fails with 27 failures and
18 errors; on the repaired guard every malformed case raises ValueError.
Canonical corpus bytes remain unchanged: 84 cases, 2299 rows, SHA256
`0a57a1d7ef6ed4b86745b00bdfe420cb005a1df87919851300efe06a0f9e853b`.

Fresh repair evidence: `/tmp/pll-stage3-repair.Ok3Tjn/`, preserving original
`/tmp/pll-stage3.I7Kron/` evidence. `baseline-preservation.json` records each of
22 production/prior-test paths with baseline and current SHA256 and byte equality
against `878a652cf27c7587055ed7fe81e15b2fa5723168`.
`baseline-production-prior-tests.diff` is the independently reproducible empty
baseline-to-current diff for exactly those paths, not merely clean-checkout
status. `repair.diff` records the complete preparation repair. No prior test or
production bytes changed, and no upstream or private runtime was accessed.

Fresh unchanged-runner --check verification is repeated on private two-task
reference and supplied stubs with Python 3.11 and 3.15. Reference: all 15 task
rows pass, including 50 tests and wheel/sdist installed README examples. Stubs:
12 retained rows pass and S1/S2/S3 fail as intended on both interpreters. Source
snapshots around judges are identical. The original external pinned build venv
is reused; no new provisioning/network/system installation is needed. Distribution
checks use external temporary builds and fresh local wheel-install environments,
no-index/no-deps, with installed import provenance asserted. Runner bytes remain
identical to the skill. No model calls/live loop or release effects occurred.
Stop here for independent re-review; bounded coverage limitations still apply.
