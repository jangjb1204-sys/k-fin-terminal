# API 키 정리

개인용 앱이라 로그인은 필요 없습니다. API 키는 배포 환경의 환경변수나 Vercel/Streamlit Secrets에 넣으면 됩니다.

## 바로 있으면 좋은 키

| 우선순위 | 키 | 용도 | 없을 때 |
|---|---|---|---|
| 1 | `GEMINI_API_KEY` | 뉴스 번역, 한국어 AI 요약/분석 | 규칙 기반 요약만 사용 |
| 2 | `POLYGON_API_KEY` | 미국 주식/ETF 근실시간 시세, 옵션 체인/플로우, 집계 캔들 | Yahoo 지연 데이터만 표시 |
| 3 | `DART_OPEN_API_KEY` | 한국 DART 공시 | DART는 `API 필요` 표시 |
| 4 | `SEC_USER_AGENT` | SEC submissions/companyfacts 호출 식별자 | SEC 공시는 제한 또는 미연동 |

## 브로커 연동할 때만 필요한 키

| 키 | 용도 |
|---|---|
| `ALPACA_API_KEY`, `ALPACA_SECRET_KEY` | Alpaca Paper Trading / 계좌 조회 |
| `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_ACCOUNT_NO` | 한국투자증권 Open API |
| IBKR Gateway/TWS 설정 | Interactive Brokers 연동 |

## 추천

지금 단계에서는 `GEMINI_API_KEY`와 `POLYGON_API_KEY`만 먼저 넣는 것을 추천합니다.

- Gemini: 번역/요약 품질 개선
- Polygon: Yahoo rate limit 문제 완화, 실시간에 가까운 시장/옵션 데이터 확장

브로커 키는 실제 주문과 연결될 수 있으니 나중에 Paper Trading 구조가 충분히 분리된 뒤 넣는 편이 안전합니다.
