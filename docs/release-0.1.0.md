# 0.1.0 release candidate

Registry publication is reserved for the owner. PyPI rejected both `pll-python`
and `pypll` as too similar to existing projects. The replacement distribution is
`phase-locked-loop` 0.1.0; import `pll`, the CLI, and the repository are unchanged.
Acceptance of the new name is unknown until an authenticated upload succeeds.

## Local evidence

All 60 tests pass on Python 3.11, 3.12, 3.13, 3.14 and 3.15. The distribution judge
scripts/check_distribution.py (name and normalized artifact paths updated only) passes with the pinned build-requirements.txt:
wheel and sdist allowlists, metadata, source/license identity, wheel rebuilt
from sdist, isolated installed README examples and both CLI entry points.
Twine 7.0.0 metadata checks pass.

Compatibility CI must pass on the exact candidate before publication. GitHub
reviews and checks are separate from local validation; no independent human
approval is asserted here. Core source, tests, numerical tolerances and corpus
are unchanged. Previous README is retained in pre-release-readme.md as historical
context, not current authority or launch instructions.

## Owner publication

Artifacts and logs are outside Git at `/tmp/phase-locked-loop-release-010`; temporary storage may
be lost. Verify SHA-256 values in SHA256SUMS and source identity before upload.
Do not rebuild from an edited checkout or replace an existing published version.

Use /tmp/pll-release-build-010/bin/python -m twine upload --repository pypi with
the two explicit files in /tmp/phase-locked-loop-release-010/dist (the 0.1.0 wheel
and source archive). Authenticate at the terminal prompt; never put tokens in
command arguments or Git.

After publication, verify official registry metadata and fresh consumer installs,
imports/examples and any installed CLI. Only then report registry release success.
Version tags must identify the final validated commit; never move a public tag.
