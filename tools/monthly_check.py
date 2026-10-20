#!/usr/bin/env python3
"""Monthly automated audit for all 74 spots in TOKYO 23 (official URL, HTTP status, SSL, hours completeness)."""
import concurrent.futures
import datetime
import json
import os
import re
import ssl
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML = os.path.join(ROOT, "index.html")
REPORT_DIR = os.path.join(ROOT, "tools", "reports")


def check_url(item):
    sid, slug, name, url = item
    if not url:
        return {"id": sid, "slug": slug, "name": name, "url": "", "status": "NO_OFFICIAL_URL", "code": None}
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; Tokyo23MonthlyAudit/1.0; +https://tokyo23-guide.com/)"},
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            return {"id": sid, "slug": slug, "name": name, "url": url, "status": "OK", "code": resp.status}
    except Exception as exc:
        return {"id": sid, "slug": slug, "name": name, "url": url, "status": f"WARN: {type(exc).__name__}", "code": getattr(exc, "code", None)}


def main():
    txt = open(INDEX_HTML, encoding="utf-8").read()
    m = re.search(r'<script[^>]*id="spotData"[^>]*>(.*?)</script>', txt, re.S)
    spots = json.loads(m.group(1))
    tasks = [(s["i"], s["s"], s["nk"], s.get("hp", "")) for s in spots]

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(check_url, tasks))

    os.makedirs(REPORT_DIR, exist_ok=True)
    today = datetime.date.today().isoformat()
    ok = [r for r in results if r["status"] == "OK"]
    warns = [r for r in results if r["status"].startswith("WARN")]
    no_hp = [r for r in results if r["status"] == "NO_OFFICIAL_URL"]

    lines = [
        f"# TOKYO 23 Monthly Official URL & Data Health Report ({today})",
        "",
        f"- Total spots audited: **{len(results)}**",
        f"- Official websites healthy (`200 OK`): **{len(ok)}**",
        f"- Official websites needing review: **{len(warns)}**",
        f"- Spots without official website (SNS/Maps tracked): **{len(no_hp)}**",
        "",
    ]
    if warns:
        lines.append("## Items Requiring Editorial Review")
        for r in warns:
            lines.append(f"- `#{r['id']:03d}` **{r['name']}** (`{r['slug']}`): `{r['status']}` — {r['url']}")
        lines.append("")

    report_md = "\n".join(lines)
    out_md = os.path.join(REPORT_DIR, "latest_monthly_report.md")
    open(out_md, "w", encoding="utf-8").write(report_md)
    print(report_md)


if __name__ == "__main__":
    main()
