# Lessons — Running Log

> **Valid-as-of:** 2026-06-22 (founding). Repo scaffolded to new-repo Playbook A+B.
> **Falsification-pointer:** Verify `spec/architecture.md` (the 3 compiler gates + one-slug rule) before citing how the compiler behaves.
> **Review-trigger:** 2026-09-22 (90 days) or when the URL-resolution logic or frontmatter schema changes.
> **Stale when:** the Vercel production-URL pattern changes, a new `host` type is added, or the frontmatter/output schema changes.

Incidents and decisions that must not be repeated.

## L1 — Founding decision (2026-06-22)

**Why this repo exists.** On 2026-06-22, ~4 conversation rounds were lost hunting the live deliverable `harness-resource-hub`: the operator knew it had hits that day, but every query returned "nothing recent" because the agent had baked the wrong `proposal_id` (`mulesoft-anypoint-onboarding`) into its `WHERE` clause. The data was never missing — the *map* was. There was no live index of published deliverables, so the agent guessed an identifier and chased the guess.

**Decision:** build a deliverables registry — one frontmatter file per published deliverable, compiled to a machine-readable JSON catalog on GitHub Pages, cloned from the proven `prompt-registry` pattern. The repo shape (its own repo vs. inside an existing one) was an explicit operator decision (STRATEGY gate, Playbook A line 29): **its own repo**.

**Lesson carried into the design (the fail-closed gates):** the failure class is "publish a wrong identifier/URL as authoritative." So the compiler is fail-closed for `status: live` — it will FAIL the build rather than emit an unverified live URL. Draft entries warn; live entries must resolve from the Vercel API and pass HTTP-verify. This is L1's failure mode encoded as a build gate.

## L2 — Adversarial-review findings folded pre-build (2026-06-22)

Before any code, the design was reviewed twice. Grok (7 points) and Codex (3 findings) both flagged the same risk class as L1: bad data published as authoritative. The 3 Codex gates — fail-closed live URL, draft-stub + promotion gate + idempotent upsert, preserved `history[]` — are in `spec/architecture.md` as the compiler's acceptance criteria. Do not weaken them to "warn"; that re-opens L1.
