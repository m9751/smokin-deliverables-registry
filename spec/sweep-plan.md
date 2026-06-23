# Sweep Plan — populate smokin-deliverables-registry and prove completeness

> **Valid-as-of:** 2026-06-23. Written after reading `scripts/sweep.py`, `scripts/deliverable_schema.json`,
> `spec/architecture.md`, `AGENTS.md`, `README.md`, and querying ST `public.deliverables` (405 rows / 163 with url).
> **Goal:** every live deliverable that should be in the registry IS in the registry — with proof it missed nothing.

## The coverage problem (why the built-in sweep is not enough)

`sweep.py` discovers from exactly **two** sources: live **Vercel projects** + **GitHub Pages repos**.
It does NOT read the Supabase `deliverables` tables. So a deliverable logged in Supabase with a live
URL but no Vercel project / Pages repo of the same slug is **invisible to the bot**. ST alone has
**163 rows with a url**. Therefore "nothing missed" requires a THIRD source the bot ignores.

**Three discovery sources, unioned:**
1. Vercel projects (via `sweep.py` / Vercel API)
2. GitHub Pages repos (via `sweep.py` / GitHub API)
3. Supabase `public.deliverables` rows with a non-empty url (ST; later WD/SO if in scope) — manual query

The registry's filed set must cover the **union** of all three. Proof = the difference (union − filed) is empty
or fully explained (allowlisted as non-deliverable).

## Phase 0 — establish the baseline (read, don't write)
- DC0: `make build` → `dist/deliverables_latest.json` exists; record current filed count (expect 1 = harness-resource-hub).
- DC0: capture the three raw discovery lists to `/tmp` (vercel.txt, pages.txt, supabase.txt) for diffing.

## Phase 1 — discover (automated, read-only)
- 1a. Vercel + Pages: run `python3 scripts/sweep.py --dry-run`. Capture every `MISSING (dry-run): <id> [host]` line.
- 1b. Supabase: query ST `public.deliverables` for rows with a url. Extract a candidate slug per row
  (from the url host/path). This is the source the bot cannot see.
- 1c. Union the three lists; subtract the current filed set + `sweep-ignore.txt`. Result = **candidate list**.

## Phase 2 — file EVERY candidate (no screening — operator decides removals)
**I do NOT screen anything out.** Every discovered slug becomes an entry. The ignore list is
operator-controlled only — I never auto-add to it. Michael is the only one who removes items.
Apply the schema rules per `deliverable_schema.json` only to make each entry VALID (not to exclude):
- `id` = lowercase/numbers/dashes; **same slug** as Vercel/Pages/beacon. Never invent a second id.
- `kind` ∈ {proposal, campaign, onboarding, brief, tool} — pick the closest fit; if genuinely unclear,
  file it anyway with a best-guess kind and FLAG it in the PR for Michael to correct. Never drop it.
- Required frontmatter: id, title, host, kind, status, created. `url` only when host=custom.
- The full discovered list is shown to Michael; he names anything to remove. Default = keep all.

## Phase 3 — file as DRAFT (safe; nothing goes live unverified)
- Every IN candidate → `deliverables/<kind>/<id>.md`, **`status: draft`**.
- Draft = URL gate is warn-only; nothing published, nothing can fail the build on an unverified URL.
- One branch, staged by name (never `git add -A`), one PR. `make verify` must exit 0.

## Phase 4 — promote to LIVE only what passes the gate
Per Gate 2 (promotion) — a row may flip to `live` ONLY when ALL hold:
- `summary` is real (not TODO/empty), `account` is a valid slug or `none`, `len(tags) >= 1`,
- url resolves via Vercel API / hand-typed AND HTTP-verifies 200 (Gate 1, fail-closed).
- Operator reviews the draft list; I promote the approved ones in one batch. CI verifies every live URL.

## Phase 5 — PROVE completeness (the part that makes "nothing missed" a fact, not a claim)
A literal sweep, not recall. Completeness = the union of all three sources is fully accounted for.
- **DC-proof-1 (Vercel/Pages):** re-run `python3 scripts/sweep.py --dry-run` → output is
  `OK: registry covers all live deliverables (none missing).` Zero MISSING lines. (This is the bot's own
  fail-closed proof for sources 1+2.)
- **DC-proof-2 (Supabase):** re-run the Phase-1b query; every returned slug is either filed in the registry
  OR present in `sweep-ignore.txt`. Set difference = empty. Show the difference query output literally.
- **DC-proof-3 (no orphans):** every filed `id` maps back to a real live URL (HTTP 200) — `make verify` exit 0
  with all live rows `url_status: resolved`.
- **DC-proof-4 (decisions logged):** every IGNORE has a line+reason in `sweep-ignore.txt` (so "excluded"
  is auditable, not silent). Count of (candidates) = count(IN filed) + count(IGNORE listed). Numbers reconcile.

## What would make this FAIL (kill conditions — state them, don't paper over)
- Any slug in the Supabase set that is neither filed nor ignored → sweep is incomplete; do not claim done.
- A url-bearing Supabase row whose slug cannot be matched to a Vercel/Pages/custom host → flag it, decide IN/IGNORE, do not drop silently.
- `sweep.py --dry-run` still prints MISSING after filing → registry does not cover sources 1+2.

## Scope question for the operator (before Phase 1)
- This plan covers **ST** `public.deliverables` (Supabase source) + Vercel + Pages.
  WD and smokin-ops also have `deliverables` tables. **In scope or ST-only for now?**
