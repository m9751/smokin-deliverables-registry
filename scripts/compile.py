#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compile.py — Deliverables Registry Compiler

Cloned from prompt-registry/scripts/compile_prompts.py (rglob discovery, YAML
frontmatter via safe_load, jsonschema validation, full dist/ overwrite,
sys.exit(1) on error). Deliverables have NO body, so the fence/footer logic is
dropped. Added: URL resolution + the 3 Codex-hardening gates (spec/architecture.md).

Modes:
  (default)   build  — resolve URLs (network), apply gates, write dist/
  --lint             — schema-only, NO network, NO URL resolution (fast static check)
  --check            — build, then validate dist/deliverables_latest.json against output_schema

Exit codes:
  0 = success
  1 = validation / gate failure (printed to stderr)
"""

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import yaml
import jsonschema

try:
    import requests
except ImportError:
    requests = None  # only needed for URL resolution (build mode); --lint works without it

# --------------------------------------------------------------------------- paths
REPO_ROOT = Path(__file__).resolve().parent.parent
DELIVERABLES_DIR = REPO_ROOT / "deliverables"
DIST_DIR = REPO_ROOT / "dist"
FM_SCHEMA_PATH = REPO_ROOT / "scripts" / "deliverable_schema.json"
OUT_SCHEMA_PATH = REPO_ROOT / "scripts" / "output_schema.json"
LATEST_JSON = DIST_DIR / "deliverables_latest.json"
INDEX_HTML = DIST_DIR / "index.html"

SCHEMA_VERSION = "1.0"
PAGES_BASE = "https://m9751.github.io"
VERCEL_API = "https://api.vercel.com"


# --------------------------------------------------------------------------- helpers
def _fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def _warn(message: str) -> None:
    print(f"WARN: {message}", file=sys.stderr)


def _today() -> str:
    return datetime.date.today().isoformat()


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def extract_frontmatter(filepath: Path) -> dict:
    """Parse YAML frontmatter. Deliverables are frontmatter-only (no body required)."""
    content = filepath.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\n(.*?)\n---\n?", content, re.DOTALL)
    if not fm_match:
        _fail(f"{filepath}: missing or malformed YAML frontmatter (expected --- delimiters)")
    try:
        fm = yaml.safe_load(fm_match.group(1))
    except yaml.YAMLError as exc:
        _fail(f"{filepath}: YAML parse error: {exc}")
    if not isinstance(fm, dict):
        _fail(f"{filepath}: frontmatter parsed to non-dict type")
    # pyyaml turns bare ISO dates into datetime.date — coerce to ISO string
    for key, val in list(fm.items()):
        if isinstance(val, (datetime.date, datetime.datetime)):
            fm[key] = val.isoformat()
    return fm


def load_prior() -> dict:
    """Prior compiled output, keyed by id. Source of known-good URLs (Gate 1) and history (Gate 3)."""
    if not LATEST_JSON.exists():
        return {}
    try:
        data = json.loads(LATEST_JSON.read_text(encoding="utf-8"))
        return {row["id"]: row for row in data.get("deliverables", [])}
    except (json.JSONDecodeError, KeyError):
        return {}


# --------------------------------------------------------------------------- URL resolution
def http_ok(url: str) -> bool:
    if requests is None:
        return False
    try:
        r = requests.head(url, allow_redirects=True, timeout=10)
        if r.status_code >= 400:  # some hosts reject HEAD; retry GET
            r = requests.get(url, allow_redirects=True, timeout=10, stream=True)
        return r.status_code < 400
    except requests.RequestException:
        return False


def vercel_production_url(deliverable_id: str) -> Optional[str]:
    """Authoritative production URL from the Vercel API. None on any failure."""
    token = os.environ.get("VERCEL_TOKEN")
    if requests is None or not token:
        return None
    team = os.environ.get("VERCEL_TEAM")
    params = {"teamId": team} if team else {}
    try:
        r = requests.get(
            f"{VERCEL_API}/v9/projects/{deliverable_id}",
            headers={"Authorization": f"Bearer {token}"},
            params=params, timeout=10,
        )
        if r.status_code != 200:
            return None
        # production alias if present, else <name>.vercel.app
        data = r.json()
        targets = (data.get("targets") or {}).get("production") or {}
        alias = targets.get("alias") or []
        if alias:
            return f"https://{alias[0]}"
        name = data.get("name", deliverable_id)
        return f"https://{name}.vercel.app"
    except (requests.RequestException, ValueError):
        return None


def resolve_url(fm: dict, network: bool) -> Tuple[Optional[str], str, str, Optional[str]]:
    """
    Returns (url, url_source, url_status, url_error).
    Gate 1 logic lives in the caller, which decides fail-closed vs warn by status.
    """
    host = fm["host"]
    did = fm["id"]

    if host == "custom":
        url = fm.get("url")
        if not url:
            return None, "none", "unresolved", "host=custom requires a hand-typed url"
        ok = http_ok(url) if network else True
        return (url, "hand-typed", "resolved", None) if ok else (url, "hand-typed", "unresolved", "HTTP verify failed")

    if host == "github-pages":
        url = f"{PAGES_BASE}/{did}/"
        ok = http_ok(url) if network else True
        return (url, "github-pages", "resolved", None) if ok else (url, "github-pages", "unresolved", "HTTP verify failed")

    # host == "vercel"
    if network:
        api_url = vercel_production_url(did)
        if api_url and http_ok(api_url):
            return api_url, "vercel-api", "resolved", None
        # API failed → formula is fallback (caller enforces draft-only for live)
        formula = f"https://{did}.vercel.app"
        ok = http_ok(formula)
        return (formula, "formula", "resolved", None) if ok else (formula, "formula", "unresolved", "Vercel API unreachable and formula URL failed verify")
    else:
        # --lint: no network, assume formula shape, mark unresolved-by-skip
        return f"https://{did}.vercel.app", "formula", "unresolved", "lint mode (no network)"


# --------------------------------------------------------------------------- gates
PLACEHOLDER_SUMMARIES = {"", "todo", "tbd"}


def promotion_gate_ok(fm: dict) -> Tuple[bool, str]:
    """Gate 2: a row may be `live` only if it carries real reuse metadata."""
    summary = str(fm.get("summary", "")).strip().lower()
    if summary in PLACEHOLDER_SUMMARIES:
        return False, "summary is placeholder/empty (TODO/TBD not allowed for status:live)"
    account = fm.get("account", "none")
    if not re.match(r"^([a-z0-9\-]+|none)$", str(account)):
        return False, f"account '{account}' is not a valid slug or 'none'"
    if len(fm.get("tags", []) or []) < 1:
        return False, "status:live requires >=1 tag"
    return True, ""


def apply_history(prior_row: Optional[dict], new_url: Optional[str], new_source: str, new_status: str) -> list:
    """Gate 3: append prior {url,source,status} to history[] when url or status changed."""
    if prior_row is None:
        return []
    history = list(prior_row.get("history", []))
    changed = (prior_row.get("url") != new_url) or (prior_row.get("status") != new_status)
    if changed:
        history.append({
            "url": prior_row.get("url"),
            "url_source": prior_row.get("url_source", "none"),
            "status": prior_row.get("status", "draft"),
            "changed_at": _now_iso(),
        })
    return history


# --------------------------------------------------------------------------- compile
def compile_registry(lint: bool) -> dict:
    fm_schema = json.loads(FM_SCHEMA_PATH.read_text(encoding="utf-8"))
    network = not lint
    prior = load_prior()

    if not DELIVERABLES_DIR.exists():
        _fail(f"deliverables dir not found: {DELIVERABLES_DIR}")

    files = sorted(f for f in DELIVERABLES_DIR.rglob("*.md") if f.name != "AGENTS.md")
    rows = []
    seen_ids = {}
    errors = []

    for fp in files:
        fm = extract_frontmatter(fp)
        # schema validation (fail-closed for all rows — malformed frontmatter never ships)
        try:
            jsonschema.validate(instance=fm, schema=fm_schema)
        except jsonschema.ValidationError as exc:
            _fail(f"{fp}: schema validation failed: {exc.message}")

        did = fm["id"]
        # filename must equal id (idempotent-upsert key + no surprise slugs)
        if fp.stem != did:
            _fail(f"{fp}: filename stem '{fp.stem}' != id '{did}'")
        if did in seen_ids:
            _fail(f"duplicate id '{did}' in {fp} and {seen_ids[did]}")
        seen_ids[did] = fp

        status = fm["status"]
        url, url_source, url_status, url_error = resolve_url(fm, network)

        # ---- Gate 2: promotion gate (live requires real reuse metadata) ----
        if status == "live":
            ok, why = promotion_gate_ok(fm)
            if not ok:
                errors.append(f"{fp}: [Gate 2] status:live rejected — {why}")
                continue

        # ---- Gate 1: fail-closed URL for live ----
        prior_row = prior.get(did)
        if status == "live":
            live_authoritative = url_source in ("vercel-api", "hand-typed", "github-pages")
            if url_status != "resolved" or not live_authoritative:
                # keep prior known-good url, mark unresolved, FAIL the build
                kept_url = prior_row.get("url") if prior_row else None
                errors.append(
                    f"{fp}: [Gate 1] status:live URL unresolved "
                    f"(source={url_source}, {url_error}). Kept prior url={kept_url!r}. "
                    f"Use status:draft to pre-register."
                )
                url, url_status = kept_url, "unresolved"
        # draft / retired: warn-only on unresolved
        elif url_status == "unresolved" and not lint:
            _warn(f"{fp}: {status} URL unresolved ({url_error}) — allowed for non-live.")

        # ---- Gate 3: preserve history ----
        history = apply_history(prior_row, url, url_source, status)

        row = {
            "id": did,
            "title": fm["title"],
            "host": fm["host"],
            "kind": fm["kind"],
            "account": fm.get("account", "none"),
            "tags": fm.get("tags", []),
            "summary": fm.get("summary", ""),
            "status": status,
            "created": fm["created"],
            "url": url,
            "url_source": url_source,
            "url_status": url_status,
            "history": history,
            "source_file": fp.relative_to(REPO_ROOT).as_posix(),
        }
        if url_error and url_status == "unresolved":
            row["url_error"] = url_error
        rows.append(row)

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    rows.sort(key=lambda r: r["id"])
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _today(),
        "count": len(rows),
        "deliverables": rows,
    }


# --------------------------------------------------------------------------- outputs
def write_outputs(payload: dict) -> None:
    DIST_DIR.mkdir(exist_ok=True)
    LATEST_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    INDEX_HTML.write_text(render_html(payload), encoding="utf-8")


def _link_cell(d: dict) -> str:
    url = d.get("url")
    if not url:
        return "—"
    return '<a href="' + url + '">link</a>'


def render_html(payload: dict) -> str:
    rows_html = "\n".join(
        '<tr data-kind="{kind}" data-account="{account}" data-status="{status}">'
        "<td>{id}</td><td>{title}</td><td>{kind}</td>"
        "<td>{account}</td><td>{status}</td><td>{tags}</td><td>{link}</td></tr>".format(
            kind=d["kind"], account=d.get("account", "none"), status=d["status"],
            id=d["id"], title=d["title"], tags=", ".join(d.get("tags", [])),
            link=_link_cell(d),
        )
        for d in payload["deliverables"]
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Deliverables Registry</title>"
        "<style>body{font-family:system-ui;margin:2rem}table{border-collapse:collapse;width:100%}"
        "th,td{border:1px solid #ddd;padding:6px 10px;text-align:left;font-size:14px}"
        "th{background:#f4f4f4}</style></head><body>"
        f"<h1>Deliverables Registry</h1><p>{payload['count']} deliverables · generated {payload['generated_at']}</p>"
        "<table><thead><tr><th>id</th><th>title</th><th>kind</th><th>account</th>"
        "<th>status</th><th>tags</th><th>url</th></tr></thead><tbody>"
        f"{rows_html}</tbody></table></body></html>"
    )


def check_output() -> None:
    out_schema = json.loads(OUT_SCHEMA_PATH.read_text(encoding="utf-8"))
    if not LATEST_JSON.exists():
        _fail("dist/deliverables_latest.json missing — run build first")
    data = json.loads(LATEST_JSON.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(instance=data, schema=out_schema)
    except jsonschema.ValidationError as exc:
        _fail(f"output schema validation failed: {exc.message}")
    print(f"OK: {data['count']} deliverables validate against output_schema.json")


# --------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lint", action="store_true", help="schema-only, no network")
    ap.add_argument("--check", action="store_true", help="build + validate dist against output_schema")
    args = ap.parse_args()

    if args.check:
        payload = compile_registry(lint=False)
        write_outputs(payload)
        check_output()
        return

    payload = compile_registry(lint=args.lint)
    if not args.lint:
        write_outputs(payload)
    print(f"OK: compiled {payload['count']} deliverables"
          f"{' (lint: schema-only, no network)' if args.lint else ' -> dist/'}")


if __name__ == "__main__":
    main()
