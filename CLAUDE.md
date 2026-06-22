# CLAUDE.md — deliverables-registry

Source-of-truth index of published deliverables and their live URLs.

**Reading order:** see [README.md](README.md). **Authority + workflow:** see [AGENTS.md](AGENTS.md).

Repo-specific rules that override global defaults here:
1. **Edit the `.md`, never `dist/`** — `scripts/compile.py` owns `dist/`; hand edits are overwritten.
2. **`status: live` is fail-closed** — an unverified live URL fails the build; pre-register with `status: draft`.
3. **`id` is one slug for four things** — Vercel project = Pages repo = beacon `proposal_id` = this entry's id. Never invent a separate id.
