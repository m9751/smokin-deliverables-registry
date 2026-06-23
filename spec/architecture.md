# Architecture — smokin-deliverables-registry

> **Valid-as-of:** 2026-06-22 (founding). Clone of the prompt-registry compiler pattern + 3 Codex-hardening gates.
> **Falsification-pointer:** Verify `scripts/compile.py` (the actual gate implementation) before citing exact compiler behavior — this doc is the contract, the script is the source of truth.
> **Review-trigger:** 2026-09-22 (90 days) or when URL-resolution or schema changes.
> **Stale when:** the Vercel production-URL pattern changes, a `host` type is added, or the frontmatter/output schema changes.

## What it is

A frontmatter-only registry. One `.md` file per published deliverable under `deliverables/<kind>/<id>.md`. A compiler reads them all, resolves each live URL, and emits two artifacts to `dist/` (published on GitHub Pages): `deliverables_latest.json` (machine catalog) and `index.html` (human catalog). Cloned from `m9751/prompt-registry` (`scripts/compile_prompts.py` + `compile-and-deploy.yml`), minus the prompt-body/feedback-footer logic, plus URL resolution + 3 gates.

## The one-slug rule (load-bearing)

```
id = Vercel project name = GitHub Pages repo name = beacon proposal_id
```

One slug does four jobs: it names the entry, derives the live URL, names the Pages repo, and joins to engagement tracking in `proposal_engagement` (SmokinTerritory) by the shared `proposal_id`. Never mint a separate id.

## URL resolution (per entry, in the compiler)

| host | how url is resolved |
|---|---|
| `vercel` | **Vercel API** project lookup → production URL (authoritative). Formula `https://<id>.vercel.app` is fallback ONLY when API unreachable AND `status: draft`. |
| `github-pages` | `https://m9751.github.io/<id>/` |
| `custom` | hand-typed `url` (required in frontmatter) |

Every resolved url is HTTP-verified. Each output row records `url_source` (`vercel-api` \| `formula` \| `hand-typed`) and `url_status` (`resolved` \| `unresolved`).

## The 3 compiler gates (acceptance criteria — fail-closed)

These encode `spec/lessons.md` L1 ("don't publish a wrong URL as authoritative"). A build that violates any gate exits non-zero.

### Gate 1 — Fail-closed URL for `status: live`
Warn-not-fail applies ONLY to `draft`. For `live`: if the Vercel API lookup fails OR HTTP-verify returns non-200, the compiler does NOT publish/overwrite the url — it keeps the prior known-good url from the existing `deliverables_latest.json`, sets `url_status: unresolved` + `url_error`, and FAILS the build. A formula-derived url is never authoritative for a `live` row.

### Gate 2 — Draft-by-default + promotion gate + idempotent upsert
A `live` row is REJECTED unless ALL hold: `summary` is non-placeholder (not `TODO`/empty), `account` is a valid slug or `none`, `len(tags) >= 1`, and url is `vercel-api`/`hand-typed` + verified. Deploy-created stubs are `status: draft`. Upserts are keyed by `id`: a repeat compile never duplicates a row and never downgrades a `live` row to `draft`.

### Gate 3 — Current-pointer + preserved history
The top-level row stays most-recent-only (the scannable view). On any change to a row's `url` or `status`, the prior `{url, url_source, status, changed_at}` is appended to that row's `history[]` (read from the existing `deliverables_latest.json` before overwrite).

## Files

- `scripts/compile.py` — the compiler (the 3 gates live here).
- `scripts/deliverable_schema.json` — frontmatter JSON Schema (required fields, enums).
- `scripts/output_schema.json` — schema for `deliverables_latest.json`.
- `deliverables/<kind>/<id>.md` — one entry per deliverable.
- `dist/` — generated, gitignored, compiler-owned.
- `sweep-ignore.txt` — non-deliverable allowlist for the sweep bot.

## Relationship to `/find`

`/find` answers "did I ever build X?" across 4 Supabase tables. This registry answers "where is X live + what's reusable." They do not compete: `/find` reads `deliverables_latest.json` as a 5th source. Stated in `AGENTS.md` so the two indexes never diverge.
