# AGENTS.md — deliverables-registry

Claude Code deliverables librarian — maintains the source-of-truth index of every published deliverable (proposal, campaign, onboarding page, brief, tool) and its live URL.

> **Authority:** Files in this repo are the source of truth. If memory or recall.md conflicts with what you read here, trust what you read. Reconcile the stale memory before proceeding — do not proceed on the stale version. Disk (this repo) = truth → smokin-os indexes it → MEMORY.md caches it (reconcile to disk, never override).

## Spec navigation

Start at [`spec/README.md`](spec/README.md). Common entry points:
- [`spec/lessons.md`](spec/lessons.md) — why this repo exists; incidents not to repeat.
- [`spec/architecture.md`](spec/architecture.md) — structure, the one-slug rule, the 3 compiler gates.
- [`spec/design.md`](spec/design.md) — full design + Grok/Codex review history.
- [`README.md`](README.md) — Quick start, reading order, CI contract.

## smokin-tracking-registry (sibling)

Signal inventory lives in **[smokin-tracking-registry](https://github.com/m9751/smokin-tracking-registry)** → `INDEX.md` + `signals.csv`. This repo is **pages only** (`deliverables_latest.json` + `deliverables_latest.csv`). Do not add signal rows here.

## Key constraint

**You edit the `.md`, the compiler owns `dist/`.** Edit `deliverables/<kind>/<id>.md`; run `make verify`; the compiler regenerates `dist/deliverables_latest.json` + `dist/index.html`. Never hand-edit `dist/` — it is overwritten on every build. And: **`status: live` is fail-closed** — a live entry with an unresolvable/unverified URL fails the build; use `status: draft` to pre-register.

## Primary task — add or edit a deliverable entry

1. `git pull && git checkout -b feat/<id>`
2. Create/edit `deliverables/<kind>/<id>.md` where `id` = the Vercel project name = the Pages repo name = the beacon `proposal_id` (one slug, all four).
3. Fill frontmatter: `id, title, host, kind, status, created` (required); `account, tags, summary` (for reuse); `url` only when `host: custom`.
4. New entries start `status: draft`. Promote to `live` only when `summary` is real (not `TODO`), `account` is a valid slug or `none`, and there is ≥1 `tag`.
5. `make verify` — must exit 0. A `live` entry whose URL fails resolution/verify will FAIL here by design.
6. `git add deliverables/<kind>/<id>.md` (by name), commit, push, open PR.

## NEVER

- **Never hand-edit `dist/`** — the compiler owns it; your edit is lost on next build.
- **Never set `status: live` with a placeholder `summary: TODO`** — the promotion gate rejects it.
- **Never force a `live` URL you have not verified** — the fail-closed gate exists because publishing a wrong/dead URL as authoritative is the exact failure this repo prevents (2026-06-22 incident).
- **Never `git add -A` / `git add .`** — stage by name; `.env` must never be committed.
- **Never commit `dist/`, `.env`, or `.venv/`** to `main` — they are gitignored generated/secret artifacts.

## Git workflow

```bash
git pull && git checkout -b feat/<id>
# edit deliverables/<kind>/<id>.md
make verify                       # must exit 0
git add deliverables/<kind>/<id>.md
git commit -m "feat(<kind>): add <id>"
git push -u origin feat/<id>
gh pr create --base main
# squash-merge, delete branch
```
