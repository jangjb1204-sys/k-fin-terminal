# API 키 정리

개인용 앱이라 로그인은 필요 없습니다. API 키는 로컬 `.env`, Streamlit Secrets, Docker 환경변수, 또는 서버 Secret Manager에 넣습니다. 브라우저에 직접 노출하면 안 됩니다.

## 필수

| 키 | 용도 | 없을 때 |
|---|---|---|
| `TOSS_CLIENT_ID` | 토스증권 OAuth2 토큰 발급 | 시세/차트/환율/보유자산이 `API 필요` |
| `TOSS_CLIENT_SECRET` | 토스증권 OAuth2 토큰 발급 | 시세/차트/환율/보유자산이 `API 필요` |

## 선택

| 키 | 용도 | 없을 때 |
|---|---|---|
| `TOSS_ACCOUNT_SEQ` | 보유자산 조회 계좌 고정 | `/api/v1/accounts` 첫 계좌 사용 |
| `GEMINI_API_KEY` | 뉴스 번역, 한국어 AI 요약/분석 | 규칙 기반 요약만 사용 |
| `DART_OPEN_API_KEY` | 한국 DART 공시 | DART는 `API 필요` 표시 |
| `SEC_USER_AGENT` | SEC submissions/companyfacts 호출 식별자 | SEC 공시는 제한 또는 미연동 |

## 토스증권 사용 범위

- 사용: OAuth 토큰, 현재가, 캔들, USD/KRW 환율, 시장 캘린더 확장 가능, 계좌/보유자산 읽기 전용
- 제외: 주문 생성, 주문 정정, 주문 취소, 옵션

토스증권 OAuth는 client당 유효 토큰이 1개라서 앱 서버에서 토큰을 캐시합니다. 운영에서 서버 인스턴스를 여러 개 띄우면 외부 캐시나 단일 API 프록시를 두는 편이 안정적입니다.
