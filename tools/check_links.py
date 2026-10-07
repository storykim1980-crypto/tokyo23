#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""스팟 페이지 외부 링크 상태 점검 (링크 로트 탐지)
사용: python3 scripts/check_links.py [repo_path]
출력: reports/broken_links.json
"""
import re, glob, os, json, sys
import requests, concurrent.futures as cf
requests.packages.urllib3.disable_warnings()

REPO = sys.argv[1] if len(sys.argv) > 1 else "."
OUT = os.environ.get("REPORT_DIR", "artifacts")
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
      "Accept-Language": "ja,en;q=0.8"}
SKIP = ("tokyo23-guide.com", "google.com/maps", "google.com/search",
        "instagram.com/explore", "commons.wikimedia", "googleapis", "gstatic",
        "wikipedia.org/wiki/Special", "x.com/", "twitter.com/")

links = {}
for f in sorted(glob.glob(os.path.join(REPO, "spot", "*.html"))):
    s = open(f, encoding="utf-8").read()
    for u in set(re.findall(r'href="(https?://[^"]+)"', s)):
        if any(k in u for k in SKIP):
            continue
        links.setdefault(u, []).append(os.path.basename(f)[:3])

def chk(u):
    try:
        r = requests.get(u, headers=UA, timeout=20, verify=False, allow_redirects=True, stream=True)
        n = len(r.raw.read(6000, decode_content=True)) if r.status_code < 400 else 0
        return u, r.status_code, n
    except Exception as e:
        return u, f"ERR:{type(e).__name__}", 0

bad = []
with cf.ThreadPoolExecutor(20) as ex:
    for u, st, ln in ex.map(chk, links.keys()):
        botblock = isinstance(st, int) and st in (401, 403, 429)
        if isinstance(st, str) or (isinstance(st, int) and st >= 400 and not botblock) or (isinstance(st, int) and st < 400 and ln < 400):
            bad.append({"url": u, "status": st, "bytes": ln, "spots": links[u],
                        "note": "bot차단(브라우저 정상)" if botblock else ""})
json.dump(bad, open(os.path.join(OUT, "broken_links.json"), "w"), ensure_ascii=False, indent=1)
print(f"검사 {len(links)}개 / 문제 {len(bad)}개 -> {OUT}/broken_links.json")
for b in bad:
    print(f"  [{b['status']}] {b['url'][:100]} {b['note']}")

sys.exit(1 if (bad and "--strict" in sys.argv) else 0)
