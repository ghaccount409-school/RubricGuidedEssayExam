#!/usr/bin/env python3
"""Run pytest suites and write JSON for the GitHub Pages site (stats.json)."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def _parse_counts_line(line: str) -> dict[str, int]:
    out = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0, "deselected": 0}
    for m in re.finditer(r"(\d+)\s+(passed|failed|errors?|skipped|deselected)\b", line, re.I):
        n, kind = int(m.group(1)), m.group(2).lower()
        if kind.startswith("error"):
            out["errors"] = n
        else:
            out[kind] = n
    return out


def _parse_pytest_log(text: str) -> dict[str, int]:
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    for line in reversed(lines):
        if re.search(r"\d+\s+(passed|failed|errors?|skipped|deselected)\b", line, re.I):
            raw = _parse_counts_line(line)
            if any(raw.values()):
                p = raw.get("passed", 0)
                f = raw.get("failed", 0)
                e = raw.get("errors", 0)
                s = raw.get("skipped", 0)
                d = raw.get("deselected", 0)
                return {
                    "passed": p,
                    "failed": f,
                    "errors": e,
                    "skipped": s,
                    "deselected": d,
                    "total": p + f + e + s,
                }
    return {
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "skipped": 0,
        "deselected": 0,
        "total": 0,
    }


def _run_pytest(root: Path, extra: list[str]) -> tuple[str, int]:
    cmd = [sys.executable, "-m", "pytest", "-q", "--tb=no", "--no-header"] + extra
    env = os.environ.copy()
    env.setdefault("MOCK_LLM", "1")
    env.setdefault("DATABASE_URL", "sqlite:///:memory:")
    proc = subprocess.run(
        cmd,
        cwd=root,
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.stdout + "\n" + proc.stderr, proc.returncode


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("site-pages/pages/stats.json"),
        help="Where to write stats JSON",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    out_general, code_g = _run_pytest(root, ["tests/general"])
    out_sec, code_s = _run_pytest(root, ["tests/security"])

    general = _parse_pytest_log(out_general)
    security = _parse_pytest_log(out_sec)

    repo = os.environ.get("GITHUB_REPOSITORY", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    workflow_url = ""
    if repo and run_id:
        workflow_url = f"{server}/{repo}/actions/runs/{run_id}"

    payload = {
        "updated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "pytest_exit_codes": {"general": code_g, "security": code_s},
        "all_passed": code_g == 0 and code_s == 0,
        "general": general,
        "security": security,
        "workflow_run_url": workflow_url,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.output}")
    # Always exit 0 so Pages deploy still publishes failure counts in stats.json.


if __name__ == "__main__":
    main()
