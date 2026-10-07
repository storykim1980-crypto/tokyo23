#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tokyo23-guide.com 스팟 공식 사이트 일괄 점검 스크립트
- 각 스팟 HTML에서 공식 사이트 URL / 전화 / 영업시간 / 휴무 / 가격을 추출
- 공식 사이트에 접속해 '변경 시그널' 키워드를 찾아 리포트
출력: <out>/official_site_scan.json  (+ 콘솔 요약)
사용: python3 tools/crawl_official.py [--repo .] [--out artifacts]
"""
import re, json, glob, os, ssl, sys, time
import urllib.request, urllib.error
import requests
from bs4 import BeautifulSoup

requests.packages.urllib3.disable_warnings()

import argparse
_ap = argparse.ArgumentParser()
_ap.add_argument("--repo", default=os.environ.get("REPO", "."))
_ap.add_argument("--out", default=os.environ.get("REPORT_DIR", "artifacts"))
_A = _ap.parse_args()
BASE = _A.repo
OUT = _A.out
os.makedirs(OUT, exist_ok=True)

SIGNALS = [
    "臨時休業", "休業", "閉店", "閉業", "移転", "改装", "改修", "リニューアル",
    "値上げ", "価格改定", "営業時間変更", "営業時間の変更", "定休日変更",
    "一時休業", "休館", "工事", "キャッシュレス", "予約制", "整理券",
    "お知らせ", "重要なお知らせ", "お詫び",
]
# 강한 시그널(사이트 갱신의 결정적 단서)
STRONG = ["臨時休業", "閉店", "閉業", "移転", "リニューアル", "値上げ", "価格改定",
          "営業時間変更", "定休日変更", "休館", "改装", "改修", "キャッシュレス"]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

def parse_spots():
    rows = []
    for f in sorted(glob.glob(os.path.join(BASE, "spot", "*.html"))):
        s = open(f, encoding="utf-8").read()
        num = os.path.basename(f).split("-")[0]

        def ko(pat, g=1):
            m = re.search(pat, s, re.S)
            if not m:
                return ""
            v = m.group(g)
            k = re.search(r'data-ko="(.*?)"', v, re.S)
            if k:
                v = k.group(1)
            return re.sub(r"&nbsp;", " ", re.sub(r"<[^>]+>", "", v)).strip()

        site = re.search(r'<a[^>]*href="(https?://[^"]+)"[^>]*data-i18n="btnSite"', s)
        if not site:
            site = re.search(r'data-i18n="btnSite"[^>]*href="(https?://[^"]+)"', s)
        tel = re.search(r'href="tel:([^"]+)"', s)
        rows.append({
            "no": num,
            "file": os.path.relpath(f, BASE),
            "names": ko(r'<p class="names">(.*?)</p>'),
            "hours": ko(r'<dt[^>]*data-i18n="mHours"[^>]*>.*?</dt><dd[^>]*>(.*?)</dd>'),
            "closed": ko(r'<dt[^>]*data-i18n="closed"[^>]*>.*?</dt><dd[^>]*>(.*?)</dd>'),
            "price": ko(r'<dt[^>]*data-i18n="mPrice"[^>]*>.*?</dt><dd[^>]*>(.*?)</dd>'),
            "site": site.group(1) if site else "",
            "tel": tel.group(1) if tel else "",
        })
    return rows


def fetch(url, timeout=20):
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout,
                         verify=False, allow_redirects=True)
        return r.status_code, r.url, r.text
    except Exception as e:
        return None, url, f"__ERROR__ {type(e).__name__}: {e}"


def scan(html):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    text = re.sub(r"\s+", " ", soup.get_text(" "))
    hits = {}
    for kw in SIGNALS:
        for m in re.finditer(kw, text):
            ctx = text[max(0, m.start() - 90): m.end() + 90].strip()
            hits.setdefault(kw, []).append(ctx)
    # 중복 문맥 제거, 각 키워드 최대 3개
    return {k: list(dict.fromkeys(v))[:3] for k, v in hits.items()}


def main():
    spots = parse_spots()
    report = []
    for sp in spots:
        if not sp["site"]:
            continue
        code, final, html = fetch(sp["site"])
        item = dict(sp)
        item["status"] = code
        item["final_url"] = final
        if code is None or code >= 400:
            item["error"] = html[:200]
            item["signals"] = {}
        else:
            item["signals"] = scan(html)
        report.append(item)
        strong = [k for k in STRONG if k in item.get("signals", {})]
        print(f"{sp['no']} {sp['names'][:22]:24s} HTTP={code} signals={strong}")
        time.sleep(0.6)

    json.dump(report, open(os.path.join(OUT, "official_site_scan.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"\n{len(report)} sites scanned -> {OUT}/official_site_scan.json")


if __name__ == "__main__":
    main()
