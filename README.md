# K-Fin Terminal

한국어 기반 미국주식 금융 터미널입니다. 미국 주식, ETF, 지수, 금리, 원자재, 환율, 한국 주식, 뉴스, 차트, 포트폴리오, 주문 설계, AI 요약을 한 화면에서 다룹니다.

## 버전

- Streamlit 버전: `app.py`
- Next.js/React 버전: `next-terminal/`

Streamlit은 빠른 프로토타입용이고, Next.js/React 버전은 더 고밀도 금융 터미널 UI와 웹 배포에 적합합니다.

## 로컬 실행

Streamlit:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

브라우저에서 `http://localhost:8501`을 엽니다.

Next.js/React:

```bash
cd next-terminal
npm install
npm run dev
```

브라우저에서 `http://localhost:3000`을 엽니다.

## 기능

- 비로그인: 일반 시장 데이터, 차트, 뉴스, 리서치 상태, Paper 주문 화면 조회
- 로그인: 로컬 사용자별 포트폴리오, 관심 설정, 기본 종목, AI/브로커 설정 저장
- 차트: 캔들, 거래량, MA20/50/200, Bollinger Band, RSI, MACD
- 기간/인터벌: `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y` 및 `1d`, `1wk`, `1mo`
- 뉴스: 원문, 한국어 번역 상태, 규칙 기반 감성/중요도/관련 티커
- AI: Gemini API 선택 연결, API 키가 없으면 규칙 기반 한국어 요약
- 포트폴리오: 수동 입력/수정, 평가금액, 손익, 종목/섹터/국가 비중, 크게 보기
- UI: 상단 전역 메뉴, 명령창, AI 버튼, 지수 스트립, 실제 전환 탭, 드래그/리사이즈 레이아웃
- 주문: Paper Trading 기본값, Live 주문 잠금, 브로커 API 연동 구조 표시

## Docker 실행

```bash
cp .env.example .env
docker compose up --build
```

## 필요한 API 키

최소 실행에는 API 키가 필요 없습니다. 무료 공개 데이터는 Yahoo Finance를 통해 지연 데이터로 표시됩니다.

- `GEMINI_API_KEY`: 뉴스 번역과 AI 분석
- `POLYGON_API_KEY`: 미국 주식 실시간/옵션/집계 시세
- `DART_OPEN_API_KEY`: 한국 DART 공시
- `SEC_USER_AGENT`: SEC API 호출용 연락처
- `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`: Alpaca Paper/Live 브로커
- `KIS_APP_KEY`, `KIS_APP_SECRET`: 한국투자증권 Open API
- IBKR: TWS 또는 IB Gateway 실행 후 별도 어댑터 연결

## 데이터 정책

앱은 실제처럼 보이는 가짜 숫자를 만들지 않습니다.

- `실제 데이터`: 계약된 실시간 API 또는 검증 가능한 실시간 소스
- `지연 데이터`: Yahoo Finance 등 무료 공개 지연 데이터
- `API 필요`: 키, 권한, 유료 데이터 계약, 브로커 세션이 필요한 데이터
- `데이터 없음`: 소스가 빈 응답을 반환했거나 티커가 지원되지 않음

## Gemini 설정

`.env`에 다음을 설정합니다.

```bash
GEMINI_API_KEY=your_key
```

운영 환경에서는 브라우저에 키를 노출하지 말고 서버 프록시에서 호출하세요.

## 브로커 연동 설계

현재 UI는 Paper Trading 기본값이며 실제 주문은 잠겨 있습니다.

실제 주문을 켜려면 서버측 브로커 어댑터, 사용자별 암호화된 자격증명 저장, 주문 전 2단계 확인, Paper/Live 계좌 분리 표시, 주문 감사 로그, 종목/수량/가격/장시간/통화별 리스크 제한이 필요합니다.

## 배포

Streamlit Cloud:

```bash
cp .env.example .env
docker compose up -d --build
```

운영 서버에서는 Nginx/Caddy로 HTTPS를 종료하고, Streamlit은 내부 포트로만 노출하세요. 사용자/포트폴리오/레이아웃은 운영 DB로 이전하는 것이 좋습니다.

Vercel로 Next.js/React 버전 배포:

- Project import: `jangjb1204-sys/k-fin-terminal`
- Root Directory: `next-terminal`
- Framework Preset: `Next.js`
- Build Command: `npm run build`
- Output Directory: Next.js 기본값

Vercel 배포 후 생성되는 URL이 어디서든 접속 가능한 React 버전 주소입니다.

## 레이아웃 커스터마이징

`모니터` 또는 `레이아웃` 탭의 패널 경계와 박스는 브라우저에서 드래그/리사이즈할 수 있습니다. 현재 데모 레이아웃은 브라우저 `localStorage`에 저장됩니다. 로그인 사용자별 서버 저장으로 확장하려면 `user_data["settings"]["layout"]`에 좌표 배열을 저장하는 API를 연결하면 됩니다.
