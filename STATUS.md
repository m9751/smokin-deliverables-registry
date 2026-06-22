# STATUS — deliverables-registry

## Current phase

**Built locally, gates verified, pre-push.** Full Playbook A+B skeleton + working compiler (3 fail-closed gates) on disk. 3 of 4 hard gates PASS (proven this session); the 4th (PRM-CDXP-002 AERR) returned 62/100 first pass, fixes applied, re-audit pending. Not yet pushed to GitHub; no Pages deploy; no remote.

## Gate results (evidence)

- ✅ **Compiler gates** (Gate 1 fail-closed live URL, Gate 2 promotion, Gate 3 history) — proven: bad `live` entries `exit 1`, history grows on url change.
- ✅ **Step 13 command parity** — two `make verify` runs, both exit 0, byte-identical output.
- ✅ **Step 5 cold-agent nav** — fresh agent routed all 3 reading-order questions to the correct file, no memory.
- ⏳ **Step 15 AERR audit** — 62/100 first pass (CI secret wiring, this file's staleness, README footer); fixes applied, re-audit pending.
- Reviewer subagents: github-reviewer 0-HIGH (SHIP-WITH-HEDGES); python-reviewer merge-blockers in sweep.py fixed.

## Open items

- **Re-run PRM-CDXP-002 AERR** after the 3 fixes; target ≥75. Trigger: "re-audit the registry".
- **No remote yet** — `m9751/deliverables-registry` not created; nothing pushed. Operator decides when to push (push enables CI + Pages).
- **Secrets not set** — `VERCEL_TOKEN` / `VERCEL_TEAM` must be added as GitHub Secrets before a `live` Vercel entry can pass CI/deploy. Trigger: "wire registry secrets".
- **Branch protection** (github/AGENTS.md rule 5) — set required checks + PR review on `main` after push.
- **Seed/backfill pending** — first sweep → draft stubs → one review PR. Trigger: "seed the registry".
