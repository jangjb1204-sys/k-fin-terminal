# API 키 정리

개인용 앱이라 로그인은 필요 없습니다. API 키는 배포 환경의 환경변수나 Vercel/Streamlit Secrets에 넣으면 됩니다.

## 바로 있으면 좋은 키

| 우선순위 | 키 | 용도 | 없을 때 |
|---|---|---|---|
| 1 | `GEMINI_API_KEY` | 뉴스 번역, 한국어 AI 요약/분석 | 규칙 기반 요약만 사용 |
| 2 | `POLYGON_API_KEY` | 미국 주식/ETF 근실시간 시세, 지수/원자재/환율 보강, 집계 캔들 | Yahoo 지연 데이터만 표시 |
| 3 | `DART_OPEN_API_KEY` | 한국 DART 공시 | DART는 `API 필요` 표시 |
| 4 | `SEC_USER_AGENT` | SEC submissions/companyfacts 호출 식별자 | SEC 공시는 제한 또는 미연동 |

## 추천

지금 단계에서는 `GEMINI_API_KEY`와 `POLYGON_API_KEY`만 먼저 넣는 것을 추천합니다.

- Gemini: 번역/요약 품질 개선
- Polygon: Yahoo rate limit 문제 완화, 실시간에 가까운 시장 데이터와 차트 데이터 확장

옵션과 주문 기능은 현재 범위에서 제외했기 때문에 거래 API 키는 필요 없습니다.
