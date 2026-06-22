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
    params = {"limit": 100}
    if team:
        params["teamId"] = team
    out = set()
    try:
        r = requests.get(f"{VERCEL_API}/v9/projects",
                         headers={"Authorization": f"Bearer {token}"},
                         params=params, timeout=15)
        if r.status_code != 200:
            print(f"ERROR: Vercel API {r.status_code}", file=sys.stderr)
            sys.exit(1)
        for p in r.json().get("projects", []):
            out.add(p["name"])
    except requests.RequestException as exc:
        print(f"ERROR: Vercel API: {exc}", file=sys.stderr)
        sys.exit(1)
    return out


def _owner_from_repo_env():
    raw = os.environ.get("GITHUB_REPO", "")
    if "/" not in raw:
        return None
    owner = raw.split("/", 1)[0].strip()
    return owner or None


def pages_repos():
    token = os.environ.get("GITHUB_TOKEN")
    owner = _owner_from_repo_env()
    if not token or not owner:
        return set()
    out = set()
    try:
        r = requests.get(f"{GITHUB_API}/users/{owner}/repos",
                         headers={"Authorization": f"Bearer {token}"},
                         params={"per_page": 100}, timeout=15)
        if r.status_code != 200:
            # fail hard: a GitHub outage must NOT silently report "no Pages repos",
            # which would mask a live-but-unfiled deliverable (the bot's whole job).
            print(f"ERROR: GitHub repos API {r.status_code} — cannot confirm Pages coverage", file=sys.stderr)
            sys.exit(1)
        for repo in r.json():
            if repo.get("has_pages"):
                out.add(repo["name"])
    except requests.RequestException as exc:
        print(f"ERROR: GitHub repos API: {exc}", file=sys.stderr)
        sys.exit(1)
    return out


def open_missing_issue_ids():
    """ids that already have an open `missing:` issue (dedup)."""
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPO")
    if not token or not repo:
        return set()
    out = set()
    try:
        r = requests.get(f"{GITHUB_API}/repos/{repo}/issues",
                         headers={"Authorization": f"Bearer {token}"},
                         params={"state": "open", "labels": "missing-deliverable", "per_page": 100},
                         timeout=15)
        if r.status_code == 200:
            for issue in r.json():
                title = issue.get("title", "")
                if title.startswith("missing: "):
                    out.add(title[len("missing: "):].split()[0])
    except requests.RequestException:
        pass
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
