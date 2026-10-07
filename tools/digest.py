#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""월간 정보점검 결과 종합 → artifacts/monthly_report.md
사용: REPORT_DIR=artifacts python3 tools/digest.py
입력(있으면): broken_links.json · sources_status.json · official_site_scan.json
"""
import json, os, datetime

OUT = os.environ.get("REPORT_DIR", "artifacts")


def load(name, default):
    p = os.path.join(OUT, name)
    if not os.path.exists(p):
        return default
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return default


today = datetime.date.today().isoformat()
lines = [f"# 도쿄23 스팟 정보 월간점검 — {today}", ""]

# 1) 깨진 링크
bl = load("broken_links.json", None)
lines.append("## 1. 외부 링크 상태")
if bl is None:
    lines.append("- (결과 파일 없음 — check_links.py 실행 실패)")
elif not bl:
    lines.append("- 이상 없음 ✅")
else:
    lines.append(f"- 문제 {len(bl)}건 (봇 차단 포함)")
    lines.append("")
    lines.append("| 상태 | 링크 | 스팟 | 비고 |")
    lines.append("|---|---|---|---|")
    for b in bl:
        lines.append(f"| {b.get('status')} | {b.get('url','')[:90]} | {','.join(b.get('spots',[]))} | {b.get('note','')} |")

# 2) 추적 소스 접속
ss = load("sources_status.json", None)
lines += ["", "## 2. 추적 소스 사이트 접속"]
if ss is None:
    lines.append("- (결과 파일 없음 — check_sources.py 실행 실패)")
else:
    down = [x for x in ss if x.get("status") != 200]
    sig = [x for x in ss if x.get("signals")]
    lines.append(f"- 점검 {len(ss)}곳 / 접속 이상 {len(down)}곳 / 변경 시그널 감지 {len(sig)}곳")
    if down:
        lines += ["", "**접속 이상**", ""]
        lines += [f"- [{x['status']}] {x['name']} — {x['url']}" for x in down]
    if sig:
        lines += ["", "**시그널 감지(수동 확인 필요)**", ""]
        lines += [f"- {x['name']}: {' · '.join(x['signals'])}" for x in sig]

# 3) 공식 사이트 스캔
of = load("official_site_scan.json", None)
lines += ["", "## 3. 공식 사이트 변경 시그널"]
if of is None:
    lines.append("- (결과 파일 없음 — crawl_official.py 실행 실패)")
else:
    strong = [x for x in of if x.get("signals")]
    err = [x for x in of if x.get("status") is None or (isinstance(x.get("status"), int) and x["status"] >= 400)]
    lines.append(f"- 스캔 {len(of)}곳 / 시그널 {len(strong)}곳 / 접속 실패 {len(err)}곳")
    if strong:
        lines += ["", "| No | 스팟 | 상태 | 시그널 |", "|---|---|---|---|"]
        for x in strong:
            lines.append(f"| {x['no']} | {x['names'][:24]} | {x.get('status')} | {' · '.join(x['signals'])} |")
    if err:
        lines += ["", "**접속 실패** " + ", ".join(f"{x['no']} {x['names'][:16]}" for x in err)]

lines += ["", "---", "", "_자동 생성: tokyo23-guide.github.io 월간 점검 워크플로_", ""]
os.makedirs(OUT, exist_ok=True)
p = os.path.join(OUT, "monthly_report.md")
open(p, "w", encoding="utf-8").write("\n".join(lines))
print(f"종합 리포트 → {p}")
