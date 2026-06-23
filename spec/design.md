# Deliverables Registry — Design Spec

> **Date:** 2026-06-22
> **Status:** Design approved (brainstorming) + Grok review folded + Codex adversarial review folded (3 findings fixed), pending operator spec review → writing-plans
> **Author:** Michael Busacca + Claude (Opus 4.8)
> **Repo:** `m9751/smokin-deliverables-registry` (sibling: `m9751/smokin-tracking-registry` for signal inventory)

## Compiler acceptance criteria (encodes the Codex next-steps as testable gates)

The implementation plan must turn these into compiler tests. A build that violates any of these FAILS (non-zero exit), it does not warn-and-pass:

1. **Publish gate by status.** `status: live` is **fail-closed** — a live row with an unresolved (API-failed) or non-200 URL is rejected; its prior known-good URL is retained and the row is marked `url_status: unresolved` + `url_error`. `status: draft` is warn-only (may carry a formula-derived, unverified URL).
2. **Deploy-stub contract.** Deploy-skill-created stubs are `status: draft` only. Promotion to `live` requires the promotion gate (non-placeholder `summary`, valid `account`, ≥1 tag, API/hand-typed + verified URL). Upserts are **idempotent, keyed by `id`** — a repeat deploy never duplicates a row and never downgrades a `live` row.
3. **History model.** Before any downstream consumer treats the registry as authoritative, the output carries structured release history (`history[]` per row, or a separate append-only `deliverables_history.jsonl`) so a bad publish or URL change is traceable and reversible.

## Goal

One always-current, machine-readable index of every deliverable Michael publishes (proposals, campaigns, onboarding/resource pages, briefs, tools), so neither Michael nor an agent ever hunts for "where is the thing" again. The index doubles as a **reuse menu** (shop for existing assets when building something new) and a **downstream source list** (other tools fetch it as their asset catalog).

Origin: a 2026-06-22 session where 4+ rounds were wasted because the live deliverable (`harness-resource-hub`) could not be found — there was no live map of published deliverables.

## Two problems this solves

1. **Organization / discovery** — name, id, description, and an index that auto-updates and can be instantly scanned.
2. **Reporting formats** — a fixed machine output (JSON) and a fixed human output (catalog page).

Explicitly **out of scope** (operator dropped): freshness/decay sweeps, follow-up tracking. (Future jobs B and C were declined; primary future jobs are **D = downstream asset menu** and **A = reuse engine**.)

## Architecture (one paragraph)

Clone the proven `m9751/prompt-registry` pattern, pointed at deliverables instead of prompts. Each deliverable is a small **frontmatter-only markdown file**. A **GitHub Action compiles** all files into `deliverables_latest.json` (machine) + an `index.html` catalog (human), published on GitHub Pages. A **daily bot** lists live Vercel projects + GitHub Pages repos and **opens a GitHub issue** for anything live-but-unfiled (file-first with a bot safety net — the operator's choice "C"). The repo is built to the **new-repo Playbook A + B** standard (App/service type).

## The load-bearing decision — one slug, four jobs

```
id  =  Vercel project name  =  GitHub Pages repo name  =  beacon proposal_id
```

Because the id equals the Vercel project name, the live URL is **derivable** — but the formula is a *fallback*, not the primary source (Grok gap #1):

**URL resolution order (compile step):**
1. **Vercel host → query the Vercel API** for the project's real production URL. This is authoritative and handles team-vs-personal scope, 63-char truncation, and anti-phishing shortening.
2. **Pages host →** `https://m9751.github.io/<id>/`.
3. **Formula fallback** (`https://<id>.vercel.app`) only when the API is unreachable — and only for `status: draft` (see fail-closed gate below).
4. **HTTP-verify** the resolved URL.
5. **Log any formula-vs-API mismatch** so the formula assumption is auditable.

**Fail-closed gate by status (Codex HIGH #1).** The warn-not-fail behavior applies ONLY to `draft` rows. For `status: live`:
- If the Vercel API lookup fails (outage/timeout/scope mismatch) **OR** HTTP verification returns non-200, the compiler **does NOT publish or overwrite the live URL.** It **keeps the prior known-good URL** and marks the row `url_status: unresolved` with `url_error: <reason>` metadata; the build surfaces this as a failed check, not a silent warning.
- A `live` row may only carry a URL that was resolved from the **Vercel API or a hand-typed `custom` host** and passed HTTP-verify. A formula-derived URL is **never** authoritative for a `live` row.
- Rationale: downstream tools and `/find` treat `deliverables_latest.json` as the source of truth for live links — a fail-open path would let an API outage publish a wrong or dead URL as authoritative. That is the exact stale-assumption failure class this project exists to kill.

> **Why the change:** live URLs are `https://<id>.vercel.app` (e.g. `crossroads-solution-brief.vercel.app`), NOT `<id>-<scope-slug>.vercel.app` — that pattern is the git/CLI preview URL, not production. Prefer the API; never trust the formula blind. (This is the exact stale-assumption failure class that started the originating session.)

And because the id equals the beacon `proposal_id`, any index row bridges directly to its engagement tracking in `proposal_engagement` (ST) with one lookup. The index and the traffic data share the key.

## File layout

```
smokin-deliverables-registry/
├── README.md  AGENTS.md  CLAUDE.md  STATUS.md   # Playbook A root files
├── Makefile  .env.example                        # Playbook B (App/service)
├── .github/workflows/compile-and-deploy.yml      # compile Action (SHA-pinned)
├── .github/workflows/sweep.yml                   # daily safety-net bot
├── scripts/compile.py  deliverable_schema.json
├── deliverables/
│   ├── proposal/<id>.md
│   ├── campaign/<id>.md
│   ├── onboarding/<id>.md
│   ├── brief/<id>.md
│   └── tool/<id>.md
└── dist/deliverables_latest.json  index.html     # published to Pages
```

## Frontmatter schema (every deliverable file)

```yaml
id: harness-resource-hub        # = Vercel project / Pages repo / beacon proposal_id
title: Harness Resource Hub     # human name
host: vercel                    # vercel | github-pages | custom  → picks URL resolution
url: https://harness-resource-hub.vercel.app   # resolved via Vercel API (formula fallback) + HTTP-verified; REQUIRED hand-typed when host=custom
kind: onboarding                # proposal | campaign | onboarding | brief | tool
account: none                   # account slug (lowercase-kebab, e.g. crossroads) | none  — NOT free text, NOT account_id18
tags: [resource-hub, mulesoft]  # shop-by-topic (reuse)
summary: One line — what it is and what is reusable in it.
status: live                    # live | draft | retired
created: 2026-06-18             # when shipped
```

**Versioning policy:** current-pointer + preserved history (Codex MED #3). The catalog still shows **one current row per deliverable** (most-recent-only at the top level — the simple scan the operator asked for). But the prior state is **not discarded**: each row carries an immutable, append-only `history[]` of past releases — `{ url, url_source, status, changed_at }` per transition. This keeps the human view simple while preserving rollback/forensic state (a bad publish or URL change can be traced and reverted). Two acceptable implementations, decided in the plan: an embedded `history[]` array on the row, OR a separate append-only `deliverables_history.jsonl` artifact emitted alongside `deliverables_latest.json`. The git history of the deliverable file is the backstop, but the registry output itself carries the structured history so downstream consumers don't have to parse git.

## Component 1 — Compile Action (the spine)

Cloned from prompt-registry's `compile_prompts.py` + `compile-and-deploy.yml`. On push to `deliverables/**`:
1. Read every file's frontmatter; validate against `deliverable_schema.json`.
2. Derive each `url` from `id` + `host`; HTTP-verify it (warn, don't fail, on non-200 so drafts can pre-register).
3. Emit `dist/deliverables_latest.json` (array of all rows).
4. Regenerate `dist/index.html` (human catalog).
5. Publish `dist/` to GitHub Pages.

## Component 2 — Sweep bot (the safety net)

A scheduled workflow (daily). Reads:
- **Vercel API** — list projects → stable production URLs.
- **GitHub API** — list repos with Pages enabled → Pages URLs.

Diffs the live set against the index `id`s. For anything **live but unfiled**, it **opens a GitHub issue** (`missing: <id> is live but not in the registry`). It does **not** auto-write the file — it cannot know `summary`/`tags`/`account` (the reuse-bearing fields), so the operator writes the one file. Flag, don't fabricate.

**Noise control (Grok gap #4):**
- **Deduplicate** — do not open a second issue for an `id` that already has an open `missing:` issue.
- **Allowlist of non-deliverables** — a repo-config list (`sweep-ignore.txt`) excludes platform/app projects that are NOT customer deliverables (e.g. `smokin-territory`, `cms-api-hub`, `aof-eval`). Sweep ignores anything on the list.

## Component 3 — Reports (the two outputs)

1. **`deliverables_latest.json`** — machine catalog at a stable Pages endpoint; downstream tools (campaigns, briefs, morning brief) fetch it as their asset list. **(serves D.)**
2. **`index.html`** — human catalog page: searchable/filterable table, grouped by `kind`, filter by `account`/`tags`, each row links to the live URL. **(serves A — shop for reusable assets.)**

## Standards compliance (non-negotiable)

- **new-repo Playbook A + B** (App/service type): root files, manifest, cold-agent nav test; Makefile front-door (`make bootstrap`/`verify`), `.env.example`, Quick start.
- **github/AGENTS.md 5 hard rules:** README/LICENSE/.gitignore present; third-party `uses:` pinned to 40-char SHA + `# vX.Y.Z`; secrets via `${{ secrets.NAME }}` only; sanitize `github.event` before shell; protected main with required checks + PR review; delete merged branches.

## Relationship to `/find` (Grok gap #2 — avoids a dual index)

`/find` already searches 4 Supabase tables (ST/WD/smokin-ops/account_artifacts) for "did I ever build X?" The registry is NOT a competing index; it is the authority for a narrower question.

| System | Answers | Source |
|---|---|---|
| **`/find`** (unchanged) | "did I ever build X?" — all shipped work, any type | 4 Supabase tables |
| **Registry** | "where is the **live URL** for X, and what's reusable in it?" | `deliverables_latest.json` |

**Decision:** `/find` gains a **5th source** — it queries `deliverables_latest.json` alongside the 4 tables. One front door, not two commands. The registry does NOT replace `/find`; it feeds it the live-URL answer. (Prevents the two-divergent-indexes risk.)

## Agent discovery / pointer wiring (Grok gap #3 — the manifest must be POINTED to)

Lesson from the prompt-registry-domain-catalog spike: a manifest is consumed **on instruction, not spontaneously** — memory overrides files unless something explicitly points to the catalog. The plan MUST wire all of:

1. **Root `AGENTS.md` pointer** in the registry: "For any live deliverable URL, fetch `deliverables_latest.json` FIRST — do not guess the URL or query tracking by a remembered slug."
2. **Cold-agent nav test** (Playbook A requirement): a fresh agent asked *"where is harness-resource-hub?"* must route to the registry, not hunt. This is the literal failure that started this project — it is the acceptance test.
3. **Skill updates** — `find`, `proposal-deploy`, `pov-builder` reference the stable JSON endpoint.

## Custom hosts (Grok gap #5)

`host: custom` is supported for custom domains / subpaths (e.g. `m9751.github.io/account-povs/usacs/`). When `host=custom`, `url` is **required and hand-typed** (not derived) and is still HTTP-verified.

## Outputs — schema, template, endpoint (Grok "missing from spec")

- **`deliverables_latest.json` schema** — its own JSON Schema (not just the frontmatter schema): top-level `{ generated_at, count, deliverables: [...] }`; each row carries the resolved+verified `url`, plus the provenance/safety fields the Codex fixes require: `url_source` (`vercel-api` | `formula` | `hand-typed`), `url_status` (`resolved` | `unresolved`), optional `url_error`, and `history[]` (`{ url, url_source, status, changed_at }` per past transition).
- **`index.html` generation** — a static template rendered by `compile.py` (same owner-of-dist discipline as prompt-registry; never hand-edit `dist/`).
- **Stable JSON endpoint** — `https://m9751.github.io/smokin-deliverables-registry/deliverables_latest.json` (the address downstream tools and `/find` fetch).
- **Stable CSV export** — `https://m9751.github.io/smokin-deliverables-registry/deliverables_latest.csv`.
- **Falsification pointer / review trigger** (prompt-registry-catalog pattern): spec is stale when the Vercel URL pattern changes, a new host type is added, or the frontmatter schema changes; review in 90 days.

## Resolved decisions (were open items)

- **URL `scope-slug`** → RESOLVED: prefer Vercel API production URL; formula `https://<id>.vercel.app` is fallback only; always HTTP-verify; log mismatches. (See URL resolution order above.)
- **Deploy-skill auto-create** → RESOLVED: **yes, tighten file-first — but stubs are `draft`, never `live` (Codex HIGH #2).** `proposal-deploy` / `colab-deploy` gain a step that commits a **stub** deliverable file (`id`, resolved `url`, **`status: draft`**, `summary: TODO`) at deploy time. The operator enriches `tags`/`summary`/`account` after, then promotes to `live`.
  - **Promotion gate (draft → live):** a row may become `live` only when ALL hold — `summary` is non-placeholder (not `TODO`), `account` is a valid slug or `none`, **≥1 tag**, and the URL resolved from Vercel API / hand-typed `custom` and passed HTTP-verify. The compiler rejects a `live` row that fails the gate.
  - **Idempotent upsert:** the deploy step is **keyed by `id`** — a repeat or concurrent deploy of the same `id` updates the existing file in place (never appends a duplicate, never downgrades a `live` row back to `draft`). Re-running a deploy is a no-op on an already-filed `id`.
  - Rationale: emitting `status: live` with `summary: TODO` would publish incomplete metadata as production-ready, and retries could upsert low-quality live rows. Draft-by-default + a promotion gate means nothing is `live` until a human has filled the reuse fields. The sweep bot is a **backstop only**.
- **Seed / backfill** → RESOLVED: first-run script = run the sweep once manually → generate `deliverables/<kind>/<id>.md` **stubs** for every live deploy found → one review PR where the operator fills the reuse fields.
