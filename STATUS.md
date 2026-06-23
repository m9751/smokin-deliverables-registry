# STATUS — deliverables-registry

## Current phase

**Pushed (private), core verified, CI blocked on billing.** Repo is live at `m9751/deliverables-registry` (private). Compiler + 3 fail-closed gates proven locally across 4 adversarial-audit rounds; core clean. Branch protection + delete-on-merge set. CI and Pages **have not run** — GitHub Actions is blocked by an account billing issue (not a code defect).

## Gate results (evidence)

- ✅ **Compiler gates** (Gate 1 fail-closed live URL, Gate 2 promotion, Gate 3 history) — proven: bad `live` entries exit 1, history grows on url change.
- ✅ **Step 13 command parity** — two `make verify` runs, both exit 0, byte-identical.
- ✅ **Step 5 cold-agent nav** — fresh agent routed all 3 reading-order questions correctly.
- ✅ **XSS (HIGH)** — `render_html` escapes every field + http(s)-only href allowlist; proven with Python HTMLParser (zero executable elements from a malicious probe).
- ✅ **Sweep hardening** — full pagination (Vercel cursor / GitHub page), fail-closed `filed_ids` (won't mass-flag on missing dist), resolved owner-type (org vs user), dedup fail-hard.
- ⚠️ **Step 15 AERR** — oscillated 62→86→70 across rounds as adversarial review probed `sweep.py` deeper; the compiler core had 0 findings every round. Remaining ~6 points are after-push-only (branch protection evidence, hosted CI/Pages proof, CI secrets) and cannot be recovered while CI is billing-blocked.
- Reviewers: github-reviewer 0-HIGH; python-reviewer merge-blockers fixed.

## Open items (BLOCKED ON OPERATOR — not code)

1. **CLEAR GITHUB ACTIONS BILLING.** CI/Compile-and-Deploy/Sweep will not start: *"job was not started because recent account payments have failed or your spending limit needs to be increased."* Fix in GitHub → Settings → Billing & plans. Private-repo Actions consume paid minutes. Until cleared, no CI, no Pages deploy, no sweep. Trigger: **"registry CI billing"**.
2. **SET VERCEL SECRET.** Add `VERCEL_TOKEN` (read-only) + optional `VERCEL_TEAM` as repo secrets (Settings → Secrets → Actions). Required before any `status: live` Vercel entry passes Gate 1 in CI. Operator sets this — agent does not enter credentials. Trigger: **"wire registry secrets"**.
3. **After 1+2:** push any commit → CI runs `make verify` (same path proven locally) → Pages publishes `deliverables_latest.json`. Note: Pages on a PRIVATE repo needs GitHub Pro/Enterprise; on free, serve the JSON via authed API or make the Pages site internal.
4. **Seed/backfill** — once CI runs, sweep finds live deploys → draft stubs → one review PR. Trigger: **"seed the registry"**.

## Repo facts
- Remote: `m9751/deliverables-registry` (private). 6 commits on `main`. Branch protection on; delete-branch-on-merge on.
- Build: `make bootstrap && make verify` (Python 3.9 local / 3.11 CI). dist/ is generated, gitignored, Action-owned.
- Design spec: `spec/design.md` (also at `~/repos/smokin-os/docs/superpowers/specs/2026-06-22-deliverables-registry-design.md`).
