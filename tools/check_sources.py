#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""일본 현지 추적 소스 URL 접속 점검 + (선택) 변경 키워드 스캔
사용: python3 scripts/check_sources.py
"""
import requests, concurrent.futures as cf, json, re, time, os
from bs4 import BeautifulSoup
requests.packages.urllib3.disable_warnings()
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
      "Accept-Language": "ja"}

SOURCES = {
 # 공공·교통
 "GO TOKYO(도쿄도 공식)": "https://www.gotokyo.org/",
 "도쿄도 산업노동국": "https://www.sangyo-rodo.metro.tokyo.lg.jp/",
 "도영교통": "https://www.kotsu.metro.tokyo.jp/",
 "도쿄도 중앙도매시장(휴시일)": "https://www.tsukiji.or.jp/",
 # 구·지역 관광
 "중앙구 관광협회": "https://www.chuo-kanko.or.jp/",
 "중앙구 특파원 블로그": "https://tokuhain.chuo-kanko.or.jp/",
 "아사쿠사 관광연맹": "https://e-asakusa.jp/",
 "아사쿠사 대백과": "https://asakusa.gr.jp/",
 "요코소 신주쿠": "https://www.yokoso-shinjuku.com/",
 "시나가와구 관광협회": "https://www.shinagawa-kanko.or.jp/",
 "오타구 관광협회": "https://www.ota-kanko.jp/",
 "세타가야navi": "https://www.setagaya-navi.com/",
 "시부야구 관광협회": "https://play-shibuya.com/",
 "이타바시 관광": "https://itabashi-kanko.jp/",
 "네리마구 관광": "https://www.nerima-kanko.jp/",
 "네리마 아니메": "https://animation-nerima.jp/",
 "가쓰시카구 관광": "https://katsushika-kanko.jp/",
 "스미다 관광": "https://visit-sumida.jp/",
 "고토구 관광": "https://www.koto-kanko.jp/",
 "TOKYO상점가 나비": "https://akitenpo.tokyo/",
}
SIGNALS = ["臨時休業", "休業", "閉店", "移転", "リニューアル", "改修", "値上げ", "休館"]

OUT = os.environ.get("REPORT_DIR", "artifacts")
os.makedirs(OUT, exist_ok=True)


def chk(kv):
    k, u = kv
    try:
        r = requests.get(u, headers=UA, timeout=20, verify=False)
        s = BeautifulSoup(r.text, "html.parser")
        for t in s(["script", "style", "noscript"]):
            t.decompose()
        txt = re.sub(r"\s+", " ", s.get_text(" "))
        hits = [w for w in SIGNALS if w in txt]
        return k, u, r.status_code, len(r.content), hits
    except Exception as e:
        return k, u, f"ERR:{type(e).__name__}", 0, []

if __name__ == "__main__":
    out = []
    with cf.ThreadPoolExecutor(12) as ex:
        for k, u, st, ln, hits in ex.map(chk, SOURCES.items()):
            mark = "OK" if st == 200 else "  "
            print(f"{mark} [{st}] {ln:>8}B  {k}  {('signals=' + str(hits)) if hits else ''}")
            out.append({"name": k, "url": u, "status": st, "bytes": ln, "signals": hits})
    json.dump(out, open(os.path.join(OUT, "sources_status.json"), "w"), ensure_ascii=False, indent=1)
