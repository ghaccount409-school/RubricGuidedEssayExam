#!/usr/bin/env python3
"""Build static site/reports/index.html for GitHub Pages from CI artifacts."""
from __future__ import annotations

import html
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _junit_totals(path: Path) -> dict[str, int]:
    if not path.is_file():
        return {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    tree = ET.parse(path)
    root = tree.getroot()
    suites = root.findall(".//{*}testsuite")
    if not suites and root.tag.endswith("testsuite"):
        suites = [root]
    total = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    for ts in suites:
        total["tests"] += int(ts.attrib.get("tests", 0))
        total["failures"] += int(ts.attrib.get("failures", 0))
        total["errors"] += int(ts.attrib.get("errors", 0))
        total["skipped"] += int(ts.attrib.get("skipped", 0))
    return total


def _passed(t: dict[str, int]) -> int:
    return max(
        0,
        t["tests"] - t["failures"] - t["errors"] - t["skipped"],
    )


def _bandit_summary(path: Path) -> tuple[dict[str, int], list[dict]]:
    if not path.is_file():
        return {}, []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}, []
    results = data.get("results") or []
    counts: dict[str, int] = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    rows: list[dict] = []
    for r in results:
        sev = str(r.get("issue_severity", "LOW")).upper()
        if sev not in counts:
            sev = "LOW"
        counts[sev] = counts.get(sev, 0) + 1
        rows.append(
            {
                "severity": sev,
                "file": r.get("filename", ""),
                "line": r.get("line_number", ""),
                "text": (r.get("issue_text") or "")[:200],
            }
        )
    rows.sort(key=lambda x: ("HIGH", "MEDIUM", "LOW").index(x["severity"]) if x["severity"] in ("HIGH", "MEDIUM", "LOW") else 3)
    return counts, rows[:50]


def _pip_audit_summary(path: Path) -> tuple[int, list[dict]]:
    if not path.is_file():
        return 0, []
    try:
        raw = path.read_text(encoding="utf-8").strip()
        if not raw:
            return 0, []
        data = json.loads(raw)
    except json.JSONDecodeError:
        return 0, []
    out: list[dict] = []
    total = 0
    deps = []
    if isinstance(data, dict) and "dependencies" in data:
        deps = data["dependencies"]
    elif isinstance(data, list):
        deps = data
    for dep in deps:
        if not isinstance(dep, dict):
            continue
        name = dep.get("name", "")
        for v in dep.get("vulns") or []:
            total += 1
            if len(out) >= 40:
                continue
            vid = ""
            if isinstance(v, dict):
                vid = str(v.get("id") or (v.get("aliases") or [""])[0] or "")
            out.append({"name": str(name), "id": vid})
    return total, out


def build_page(
    out_dir: Path,
    *,
    junit: Path,
    security_junit: Path,
    bandit: Path,
    pip_audit: Path,
    repo: str,
    run_url: str,
) -> None:
    main = _junit_totals(junit)
    sec = _junit_totals(security_junit)
    b_counts, b_rows = _bandit_summary(bandit)
    vuln_n, vuln_rows = _pip_audit_summary(pip_audit)

    main_pass = _passed(main)
    sec_pass = _passed(sec)

    def esc(s: str) -> str:
        return html.escape(s, quote=True)

    bandit_rows_html = ""
    if b_rows:
        bandit_rows_html = "<table><thead><tr><th>Severity</th><th>File</th><th>Line</th><th>Detail</th></tr></thead><tbody>"
        for r in b_rows:
            bandit_rows_html += (
                f"<tr><td>{esc(r['severity'])}</td><td><code>{esc(r['file'])}</code></td>"
                f"<td>{r['line']}</td><td>{esc(r['text'])}</td></tr>"
            )
        bandit_rows_html += "</tbody></table>"
    else:
        bandit_rows_html = "<p class=\"ok\">No Bandit findings (or scan not run).</p>"

    pip_rows_html = ""
    if vuln_rows:
        pip_rows_html = "<table><thead><tr><th>Package</th><th>Advisory</th></tr></thead><tbody>"
        for r in vuln_rows:
            pip_rows_html += f"<tr><td>{esc(r['name'])}</td><td>{esc(r['id'])}</td></tr>"
        pip_rows_html += "</tbody></table>"
    elif vuln_n == 0:
        pip_rows_html = "<p class=\"ok\">No known dependency vulnerabilities reported by pip-audit.</p>"
    else:
        pip_rows_html = f"<p>{vuln_n} issue(s); see raw JSON in CI artifacts if needed.</p>"

    run_link = f'<p><a href="{esc(run_url)}">View this run on GitHub Actions</a></p>' if run_url else ""

    html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>RGEE — Test &amp; security reports</title>
  <style>
    :root {{ font-family: system-ui, sans-serif; background: #0f1419; color: #e6edf3; }}
    body {{ max-width: 56rem; margin: 0 auto; padding: 1.5rem; line-height: 1.5; }}
    h1 {{ font-size: 1.5rem; margin-top: 0; }}
    h2 {{ font-size: 1.15rem; margin-top: 2rem; border-bottom: 1px solid #30363d; padding-bottom: 0.35rem; }}
    .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1rem 1.25rem; margin: 1rem 0; }}
    .stats {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(8rem, 1fr)); gap: 0.75rem; }}
    .stat {{ background: #21262d; padding: 0.75rem; border-radius: 6px; text-align: center; }}
    .stat strong {{ display: block; font-size: 1.75rem; color: #58a6ff; }}
    .ok {{ color: #3fb950; }}
    .warn {{ color: #d29922; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
    th, td {{ border: 1px solid #30363d; padding: 0.4rem 0.5rem; text-align: left; }}
    th {{ background: #21262d; }}
    code {{ font-size: 0.85em; }}
    a {{ color: #58a6ff; }}
    footer {{ margin-top: 3rem; font-size: 0.85rem; color: #8b949e; }}
  </style>
</head>
<body>
  <h1>RubricGuidedEssayExam — CI reports</h1>
  <p>Automated test results and security checks from the latest successful deploy workflow.</p>
  {run_link}

  <h2>Test suite (pytest)</h2>
  <div class="card">
    <div class="stats">
      <div class="stat"><strong>{main_pass}</strong> passed</div>
      <div class="stat"><strong>{main['failures']}</strong> failed</div>
      <div class="stat"><strong>{main['errors']}</strong> errors</div>
      <div class="stat"><strong>{main['skipped']}</strong> skipped</div>
      <div class="stat"><strong>{main['tests']}</strong> total</div>
    </div>
  </div>

  <h2>Security tests (pytest <code>-m security</code>)</h2>
  <div class="card">
    <div class="stats">
      <div class="stat"><strong>{sec_pass}</strong> passed</div>
      <div class="stat"><strong>{sec['failures'] + sec['errors']}</strong> failed</div>
      <div class="stat"><strong>{sec['tests']}</strong> total</div>
    </div>
    <p class="ok">Security-focused HTTP checks (no stack traces in 404s, safe error handling).</p>
  </div>

  <h2>Static analysis (Bandit)</h2>
  <div class="card">
    <p>
      HIGH: <span class="warn">{b_counts.get('HIGH', 0)}</span> ·
      MEDIUM: <span class="warn">{b_counts.get('MEDIUM', 0)}</span> ·
      LOW: {b_counts.get('LOW', 0)}
    </p>
    {bandit_rows_html}
  </div>

  <h2>Dependency audit (pip-audit)</h2>
  <div class="card">
    <p>Known vulnerabilities in locked/installed dependencies: <strong>{vuln_n}</strong></p>
    {pip_rows_html}
  </div>

  <footer>
    Repository: {esc(repo)} · Generated in CI — not real-time.
  </footer>
</body>
</html>
"""

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(html_out, encoding="utf-8")


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    site = root / "site"
    junit = Path(os.environ.get("JUNIT_PATH", root / "junit.xml"))
    sj = Path(os.environ.get("SECURITY_JUNIT_PATH", root / "security-junit.xml"))
    bandit = Path(os.environ.get("BANDIT_JSON_PATH", root / "bandit.json"))
    pip_audit = Path(os.environ.get("PIP_AUDIT_JSON_PATH", root / "pip_audit.json"))
    repo = os.environ.get("GITHUB_REPOSITORY", "local/dev")
    run_url = os.environ.get("GITHUB_SERVER_URL", "") and os.environ.get("GITHUB_RUN_ID", "")
    if run_url:
        run_url = f"{os.environ['GITHUB_SERVER_URL']}/{repo}/actions/runs/{os.environ['GITHUB_RUN_ID']}"

    build_page(
        site,
        junit=junit,
        security_junit=sj,
        bandit=bandit,
        pip_audit=pip_audit,
        repo=repo,
        run_url=run_url,
    )
    print(f"Wrote {site / 'index.html'}")


if __name__ == "__main__":
    main()
    sys.exit(0)
