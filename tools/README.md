# 월간 정보점검 도구

tokyo23-guide.com 스팟 정보가 오래되지 않도록, 일본 현지 소스와 공식 사이트를
주기적으로 점검하는 스크립트 모음입니다.

| 스크립트 | 하는 일 | 출력 |
|---|---|---|
| `check_links.py` | 각 스팟 페이지의 외부 링크 접속 점검(링크 로트 탐지) | `broken_links.json` |
| `check_sources.py` | 추적 중인 일본 현지 소스 20곳 접속 점검 + 변경 시그널 키워드 스캔 | `sources_status.json` |
| `crawl_official.py` | 스팟 공식 사이트 37곳을 스캔해 "휴업·이전·가격 개정·예약제" 등 변경 시그널 수집 | `official_site_scan.json` |
| `digest.py` | 위 3개 결과를 하나의 Markdown 리포트로 종합 | `monthly_report.md` |

## 로컬 실행

```bash
pip install requests beautifulsoup4
export REPORT_DIR=artifacts
python3 tools/check_links.py .
python3 tools/check_sources.py
python3 tools/crawl_official.py --repo . --out artifacts
python3 tools/digest.py
```

`broken_links.json` 의 401·403·429 는 봇 차단(브라우저에서는 정상)일 수 있으니
`note` 필드를 함께 보세요.

## 자동 실행

`.github/workflows/monthly-check.yml` 이 **매월 1일 06:00 JST** 에 위 4개를 실행하고,
결과를 `monthly-report` 아티팩트(90일 보관)와 **이슈(라벨 `info-check`)** 로 남깁니다.
GitHub에서 직접 실행하려면 Actions 탭 → *월간 정보점검* → **Run workflow**.

> 저장소 Settings → Actions → General 에서 워크플로 권한이 허용되어 있어야 하며,
> 최초 1회 `info-check` 라벨을 만들어 두면 이슈 생성이 깔끔합니다.
