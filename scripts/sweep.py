#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sweep.py — Deliverables Registry safety-net bot (Component 2, spec/design.md).

Lists live Vercel projects + GitHub Pages repos, diffs against the registry's
filed ids, and opens a GitHub issue for anything LIVE BUT UNFILED. It never
auto-writes a deliverable file (it cannot know summary/tags/account — the
reuse fields). Flag, don't fabricate.

Noise control:
  - dedup: never opens a second issue for an id that already has an open `missing:` issue
  - allowlist: skips anything in sweep-ignore.txt (non-deliverables)

Modes:
  --dry-run   list missing ids, do NOT open issues (default when no token)

Env:
  VERCEL_TOKEN, VERCEL_TEAM   — list Vercel projects
  GITHUB_TOKEN, GITHUB_REPO   — open issues (owner/repo)

Exit codes: 0 = ran (missing items reported), 1 = hard error (API auth, etc.)
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests not installed (pip install -r requirements.txt)", file=sys.stderr)
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
LATEST_JSON = REPO_ROOT / "dist" / "deliverables_latest.json"
IGNORE_FILE = REPO_ROOT / "sweep-ignore.txt"
VERCEL_API = "https://api.vercel.com"
GITHUB_API = "https://api.github.com"


def load_ignore():
    if not IGNORE_FILE.exists():
        return set()
    out = set()
    for line in IGNORE_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.add(line)
    return out


def filed_ids():
    if not LATEST_JSON.exists():
        return set()
    try:
        data = json.loads(LATEST_JSON.read_text(encoding="utf-8"))
        return {row["id"] for row in data.get("deliverables", [])}
    except (json.JSONDecodeError, KeyError):
        return set()


def vercel_projects():
    token = os.environ.get("VERCEL_TOKEN")
    if not token:
        return set()
    team = os.environ.get("VERCEL_TEAM")
    out = set()
    until = None  # Vercel cursor pagination: pagination.next is a timestamp passed as `until`
    headers = {"Authorization": f"Bearer {token}"}
    for _ in range(1000):  # hard cap: 100k projects, defends against a broken cursor loop
        params = {"limit": 100}
        if team:
            params["teamId"] = team
        if until is not None:
            params["until"] = until
        try:
            r = requests.get(f"{VERCEL_API}/v9/projects", headers=headers, params=params, timeout=15)
        except requests.RequestException as exc:
            print(f"ERROR: Vercel API: {exc}", file=sys.stderr)
            sys.exit(1)
        if r.status_code != 200:
            print(f"ERROR: Vercel API {r.status_code}", file=sys.stderr)
            sys.exit(1)
        body = r.json()
        for p in body.get("projects", []):
            out.add(p["name"])
        nxt = (body.get("pagination") or {}).get("next")
        if not nxt:
            break
        until = nxt
    return out


def _owner_from_repo_env():
    raw = os.environ.get("GITHUB_REPO", "")
    if "/" not in raw:
        return None
    owner = raw.split("/", 1)[0].strip()
    return owner or None


def _authenticated_login(headers):
    """The login of the token's own account, or None on failure."""
    try:
        r = requests.get(f"{GITHUB_API}/user", headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json().get("login")
    except requests.RequestException:
        pass
    return None


def _pages_endpoint(owner, headers):
    """
    Pick the listing endpoint that returns PUBLIC + PRIVATE repos the token can see.
    - owner == authenticated user  -> /user/repos?affiliation=owner  (public + private)
    - otherwise (org)              -> /orgs/{owner}/repos?type=all    (public + private the token can see)
    The bare /users/{owner}/repos path returns PUBLIC ONLY, which would silently
    drop private/org Pages deliverables — the exact safety-net hole this avoids.
    """
    me = _authenticated_login(headers)
    if me and me.lower() == owner.lower():
        return f"{GITHUB_API}/user/repos", {"affiliation": "owner"}
    return f"{GITHUB_API}/orgs/{owner}/repos", {"type": "all"}


def pages_repos():
    token = os.environ.get("GITHUB_TOKEN")
    owner = _owner_from_repo_env()
    if not token or not owner:
        return set()
    out = set()
    headers = {"Authorization": f"Bearer {token}"}
    url, base_params = _pages_endpoint(owner, headers)
    page = 1
    for _ in range(1000):  # hard cap: 100k repos
        params = dict(base_params, per_page=100, page=page)
        try:
            r = requests.get(url, headers=headers, params=params, timeout=15)
        except requests.RequestException as exc:
            # fail hard: an outage must NOT silently report "no Pages repos",
            # which would mask a live-but-unfiled deliverable (the bot's whole job).
            print(f"ERROR: GitHub repos API: {exc}", file=sys.stderr)
            sys.exit(1)
        if r.status_code != 200:
            print(f"ERROR: GitHub repos API {r.status_code} at {url} — cannot confirm Pages coverage",
                  file=sys.stderr)
            sys.exit(1)
        batch = r.json()
        if not batch:
            break
        for repo in batch:
            # /user/repos returns repos across all owners the user can access; keep only this owner's
            repo_owner = (repo.get("owner") or {}).get("login", "")
            if repo_owner.lower() != owner.lower():
                continue
            if repo.get("has_pages"):
                out.add(repo["name"])
        if len(batch) < 100:
            break
        page += 1
    return out


def open_missing_issue_ids():
    """ids that already have an open `missing:` issue (dedup), fully paginated.

    Fails hard on API error: a silently-empty dedup set would let the bot re-open
    issues that already exist (duplicate churn). The dedup list must be trustworthy
    or the run must stop.
    """
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPO")
    if not token or not repo:
        return set()
    out = set()
    headers = {"Authorization": f"Bearer {token}"}
    page = 1
    for _ in range(1000):
        try:
            r = requests.get(f"{GITHUB_API}/repos/{repo}/issues", headers=headers,
                             params={"state": "open", "labels": "missing-deliverable",
                                     "per_page": 100, "page": page}, timeout=15)
        except requests.RequestException as exc:
            print(f"ERROR: GitHub issues API (dedup): {exc}", file=sys.stderr)
            sys.exit(1)
        if r.status_code != 200:
            print(f"ERROR: GitHub issues API {r.status_code} (dedup) — refusing to "
                  f"run with an unreliable dedup set", file=sys.stderr)
            sys.exit(1)
        batch = r.json()
        if not batch:
            break
        for issue in batch:
            title = issue.get("title", "")
            if title.startswith("missing: "):
                rest = title[len("missing: "):].split()
                if rest:
                    out.add(rest[0])
        if len(batch) < 100:
            break
        page += 1
    return out


def open_issue(deliverable_id, host):
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPO")
    body = (f"`{deliverable_id}` is live on **{host}** but has no entry in the registry.\n\n"
            f"Add `deliverables/<kind>/{deliverable_id}.md` with frontmatter "
            f"(id, title, host, kind, status, created; plus account/tags/summary for reuse). "
            f"Start `status: draft`, promote to `live` once the reuse fields are filled.")
    try:
        r = requests.post(f"{GITHUB_API}/repos/{repo}/issues",
                          headers={"Authorization": f"Bearer {token}"},
                          json={"title": f"missing: {deliverable_id} ({host})",
                                "body": body, "labels": ["missing-deliverable"]},
                          timeout=15)
        return r.status_code in (200, 201)
    except requests.RequestException as exc:
        # do not crash the loop mid-sweep; caller logs FAILED and continues
        print(f"WARN: issue POST failed for {deliverable_id}: {exc}", file=sys.stderr)
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report only, do not open issues")
    args = ap.parse_args()

    ignore = load_ignore()
    filed = filed_ids()
    live = {(p, "vercel") for p in vercel_projects()} | {(p, "github-pages") for p in pages_repos()}

    missing = [(pid, host) for (pid, host) in sorted(live)
               if pid not in filed and pid not in ignore]

    if not missing:
        print("OK: registry covers all live deliverables (none missing).")
        return

    already = open_missing_issue_ids()
    dry = args.dry_run or not (os.environ.get("GITHUB_TOKEN") and os.environ.get("GITHUB_REPO"))

    for pid, host in missing:
        if pid in already:
            print(f"SKIP (issue open): {pid}")
            continue
        if dry:
            print(f"MISSING (dry-run): {pid} [{host}]")
        else:
            ok = open_issue(pid, host)
            print(f"{'OPENED' if ok else 'FAILED'} issue: {pid} [{host}]")


if __name__ == "__main__":
    main()
