#!/usr/bin/env python3
"""Publish small public-data receipts through the GitHub Checks API using gh.

A neutral check makes the JSON accessible even when sandbox TLS cannot download
Azure-hosted Actions artifacts. Credentials stay in standard GitHub Actions
secret handling and are never copied into the payload, receipts or logs.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--name", default="Public-data receipt (neutral, inspect JSON)")
    args = parser.parse_args()
    body = json.loads(args.receipt.read_text())
    canonical = json.dumps(body, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    encoded = base64.b64encode(canonical).decode("ascii")
    digest = hashlib.sha256(canonical).hexdigest()
    summary = f"UTF-8 JSON receipt, base64 encoded to survive GitHub Markdown escaping. SHA-256: {digest}\n\n```base64json\n{encoded}\n```"
    if len(summary.encode()) > 60_000:
        raise ValueError("receipt exceeds Check summary budget; do not silently truncate")
    repo, sha, run = os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_SHA"], os.environ["GITHUB_RUN_ID"]
    payload = {"name": args.name, "head_sha": sha,
               "status": "completed", "conclusion": "neutral",
               "details_url": f"https://github.com/{repo}/actions/runs/{run}",
               "output": {"title": "Download success/failure is inside the receipt, not implied by a green workflow",
                          "summary": summary}}
    path = Path(".cache") / "probe-check-payload.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(payload, allow_nan=False))
    result = subprocess.run(["gh", "api", "--method", "POST", f"repos/{repo}/check-runs", "--input", str(path),
                             "--jq", "{id,name,conclusion}"], capture_output=True, text=True, check=True, timeout=60)
    print(result.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
