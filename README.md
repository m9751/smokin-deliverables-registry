# smokin-deliverables-registry

**Where every published deliverable lives.** Open this repo → scroll → click a link.

<!-- catalog-start -->
**30 deliverables** · updated 2026-06-23
Interactive: [https://m9751.github.io/smokin-deliverables-registry/](https://m9751.github.io/smokin-deliverables-registry/)

| id | title | kind | account | status | url |
| --- | --- | --- | --- | --- | --- |
| account-povs | Account POVs Hub | proposal | none | draft | [open](https://m9751.github.io/account-povs/) |
| anypoint-entitlement-guide | Anypoint Platform Entitlement Guide | brief | none | draft | [open](https://anypoint-entitlement-guide.vercel.app) |
| aof-eval | AOF Eval Harness | tool | none | draft | [open](https://aof-eval.vercel.app) |
| bcbs-payer-webinar-campaign | BCBS Payer Webinar Campaign | campaign | none | draft | [open](https://m9751.github.io/bcbs-payer-webinar-campaign/) |
| beacon-dashboard | Beacon Engagement Dashboard | tool | none | draft | [open](https://m9751.github.io/beacon-dashboard/) |
| cms-api-hub | CMS API Hub | tool | none | draft | [open](https://cms-api-hub.vercel.app) |
| crossroads-solution-brief | Crossroads Solution Brief | brief | crossroads | draft | [open](https://crossroads-solution-brief.vercel.app) |
| dataunification-ms-anmed-052026 | AnMed Data Unification | brief | anmed | draft | [open](https://dataunification-ms-anmed-052026.vercel.app) |
| design-docs | Design Doc Skill | tool | none | draft | [open](https://m9751.github.io/design-docs/) |
| harness-resource-hub | Harness Resource Hub | onboarding | none | draft | [open](https://harness-resource-hub.vercel.app) |
| healthcare-agent-demo-vzrh | Healthcare Agent Demo | tool | none | draft | [open](https://healthcare-agent-demo-vzrh.vercel.app) |
| highfive-architecture | HighFive Architecture Brief | proposal | highfive | draft | [open](https://m9751.github.io/highfive-architecture/) |
| highfive-proposal | HighFive Proposal Deck | proposal | highfive | draft | [open](https://m9751.github.io/highfive-proposal/) |
| idp-roi-calculator-v1 | IDP ROI Calculator v1 | tool | none | draft | [open](https://idp-roi-calculator-v1.vercel.app) |
| idp-roi-calculator-wine | IDP ROI Calculator v2 | tool | none | draft | [open](https://idp-roi-calculator-wine.vercel.app) |
| master-identity-architecture | Master Identity Architecture | tool | none | draft | [open](https://master-identity-architecture.vercel.app) |
| momentum-architecture-read | Momentum Architecture Read | proposal | momentum | draft | [open](https://momentum-architecture-read.vercel.app) |
| momentum-architecture-read-v3 | Momentum Architecture Read v3 | proposal | momentum | draft | [open](https://momentum-architecture-read-v3.vercel.app) |
| mulesoft-claude-cursor-onboarding | MuleSoft Claude Code Onboarding Kit | onboarding | none | draft | [open](https://mulesoft-claude-cursor-onboarding.vercel.app) |
| musc-integration-abm | MUSC Integration ABM Campaign | campaign | musc | draft | [open](https://m9751.github.io/musc-integration-abm/) |
| musc-video | MUSC MuleSoft Walkthrough Video | brief | musc | draft | [open](https://musc-video.vercel.app) |
| number-one-son-for-dad | Number One Son | tool | none | draft | [open](https://number-one-son-for-dad.vercel.app) |
| payer-data-360-campaign | Payer Data 360 Webinar Campaign | campaign | none | draft | [open](https://m9751.github.io/payer-data-360-campaign/) |
| proposal-intel | Proposal Intelligence Dashboard | tool | none | draft | [open](https://m9751.github.io/proposal-intel/) |
| q1-idp-top-50 | Q1 IDP Top 50 Campaign Page | campaign | none | draft | [open](https://m9751.github.io/q1-idp-top-50/) |
| smokin-decision | Smokin Decision Web UI | tool | none | draft | [open](https://smokin-decision.vercel.app) |
| smokin-territory | SmokinTerritory Heatmap | tool | none | draft | [open](https://smokin-territory.vercel.app) |
| st-architecture | SmokinTerritory Architecture Reference | tool | none | draft | [open](https://m9751.github.io/st-architecture/) |
| st-cheatsheet | Command Cheat Sheet | tool | none | draft | [open](https://m9751.github.io/st-cheatsheet/) |
| st-top50 | Territory Top 50 Dashboard | tool | none | draft | [open](https://st-top50.vercel.app) |
<!-- catalog-end -->

Signal inventory (what's live/broken in tracking): [smokin-tracking-registry](https://github.com/m9751/smokin-tracking-registry)

---

## Reading order

> **STOP:** Read [AGENTS.md](AGENTS.md) before any edit, search, or recommendation.

| If you are asking… | Start here |
|---|---|
| "I was given a task / told to change something" | [`AGENTS.md`](AGENTS.md) — read before acting |
| "How do I compile and verify a change?" | **Quick start** below → `make verify` |
| "How do I add or edit a deliverable entry?" | [`AGENTS.md`](AGENTS.md) |
| "Why does this repo exist / what must not be repeated?" | [`spec/lessons.md`](spec/lessons.md) |
| "How is the registry structured / what are the rules?" | [`spec/architecture.md`](spec/architecture.md) |
| "What's the full design + review history?" | [`spec/design.md`](spec/design.md) |
| "What's the current state?" | [`STATUS.md`](STATUS.md) |

## Quick start

```bash
git clone https://github.com/m9751/smokin-deliverables-registry.git
make bootstrap   # install Python deps (pyyaml, jsonschema, requests)
make verify      # build + validate — exit 0 = ready
```

`make verify` compiles `deliverables/**/*.md` into `dist/` and refreshes the catalog table in this README. To pre-register a draft before its URL is live, set `status: draft` in the frontmatter (the URL gate is warn-only for drafts, fail-closed for `live`).

## Boundary — what is NOT here

- **Not the deliverables themselves.** This repo holds *pointers* (one frontmatter file per deliverable). The actual HTML/proposal lives at its Vercel/Pages URL.
- **Not engagement tracking.** Who-opened-what lives in the `proposal_engagement` table (SmokinTerritory). This registry bridges to it by the shared `id` (= beacon `proposal_id`), but does not store traffic.
- **Not a replacement for `/find`.** `/find` answers "did I ever build X?" across 4 Supabase tables. This registry answers "where is X live, and what's reusable in it." `/find` reads this registry's JSON as a 5th source.
- **`dist/` is generated** — never hand-edit; the compiler owns it (see Generated files).

## For agents landing here (read before any action)

1. **Read AGENTS.md before any action.** Before editing, searching, recommending, or querying anything in this repo, read [`AGENTS.md`](AGENTS.md) fully. This is a gate, not a reading-order option.
2. **Pull before editing.** Mac and Win11 both clone this repo — always `git pull` before editing to avoid silent drift.
3. **Edit the `.md`, never `dist/`.** You edit a deliverable's frontmatter file under `deliverables/<kind>/<id>.md`; the compiler regenerates `dist/` and the README catalog. Hand-editing `dist/` is overwritten on the next build.
4. **`status: live` is fail-closed.** A `live` entry whose URL cannot be resolved from the Vercel API or fails HTTP-verify makes the build FAIL. Use `status: draft` to pre-register. Never force a `live` URL you have not verified.
5. **Branch + PR for every change**, even one-liners — PRs are the audit trail.

## CI contract

CI runs `make bootstrap && make verify`. If CI is red:
1. Run `make verify` locally first.
2. If local passes and CI fails — CI environment drift. Fix `.github/workflows/ci.yml`.
3. If local fails — fix the `.md` entry (usually a schema or URL-gate failure).

## Generated files

`dist/deliverables_latest.json`, `dist/deliverables_latest.csv`, and `dist/index.html` are generated by `scripts/compile.py` from `deliverables/**/*.md`. They are gitignored and built by CI on deploy — never committed to `main`. Regenerate locally with `make build`.

The **README catalog table** (between `<!-- catalog-start -->` / `<!-- catalog-end -->`) is also compiler-owned — commit it when you add or change deliverables.