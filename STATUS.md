# STATUS — deliverables-registry

## Current phase

**Scaffolding (local, pre-push).** Repo built locally to new-repo Playbook A + B; not yet pushed to GitHub, no Pages deploy, no CI run. Awaiting operator review of the conformance table and the three hard gates (cold-agent nav, command parity, PRM-CDXP-002 AERR).

## Open items

- **Compiler not yet built** — `scripts/compile.py` + the 3 gates pending. Trigger: "build the registry compiler".
- **CI + sweep workflows not yet written** — `compile-and-deploy.yml`, `ci.yml`, `sweep.yml` pending. Trigger: "add registry workflows".
- **Three hard gates not yet run** — Step 5 cold-agent nav, Step 13 command parity, Step 15 AERR ≥75. Repo is NOT "live" until all three pass. Trigger: "run the registry gates".
- **No remote yet** — `m9751/deliverables-registry` not created; nothing pushed. Operator decides when to push.
- **Seed/backfill pending** — first sweep → draft stubs → one review PR. Trigger: "seed the registry".
