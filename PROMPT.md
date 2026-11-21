Implement only the supplied task, from files alone.

1. Read README.md (authority), SPEC.md (subordinate), and PROGRESS.md.
2. Preserve exported names, signatures and contract comments. Already passing
   behavior stays unless this task requires changing it. Private integer
   algorithms/helpers are free within the protected value/issuance seam.
3. Never edit any approved README, tests, fixtures, supporting contracts,
   complete files, harness guards, LICENSE, .gitignore, tasks.json, PROMPT.md,
   SPEC.md or scripts/loop.sh. These paths are protected. Complete files are
   pll/__init__.py, pll/_errors.py and pll/_values.py. PROGRESS.md is writable.
4. Implement only in pll/_rate.py, pll/_span.py, pll/_pacer.py (new private
   implementation files are allowed, not new public exports or dependencies).
   No follower work, packaging backend, I/O, clocks, subprocesses or models.
5. If a new contract decision is needed, record the blocker in PROGRESS.md,
   do not invent an answer, and stop. The operator must withhold/stop the loop;
   progress notes do not automatically pause this unchanged runner.
6. Run the exact task command. Append three lines to PROGRESS.md: task id,
   what changed, remaining work or blocker. Stop; do not commit or mark done.
