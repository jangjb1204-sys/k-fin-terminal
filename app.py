import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as components
from plotly.subplots import make_subplots


APP_NAME = "K-Fin Terminal"
APP_DIR = Path(".terminal_data")
OWNER_ID = "owner"
TOSS_BASE_URL = "https://openapi.tossinvest.com"
TOSS_SOURCE = "Toss Securities Open API"
STATUS_REAL = "실제 데이터"
STATUS_DELAYED = "지연 데이터"
STATUS_API = "API 필요"
STATUS_NONE = "데이터 없음"

US_MARKET_TICKERS = {
    "AAPL": "AAPL",
    "MSFT": "MSFT",
    "NVDA": "NVDA",
    "TSLA": "TSLA",
    "SPY": "SPY",
    "QQQ": "QQQ",
    "Samsung": "005930",
    "USD/KRW": "KRW=X",
}
WATCHLIST_DEFAULT = ["AAPL", "MSFT", "NVDA", "TSLA", "SPY", "QQQ", "005930"]
PERIOD_OPTIONS = ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y"]
INTERVAL_OPTIONS = ["1d", "1m"]
TOSS_CANDLE_COUNTS = {"1mo": 31, "3mo": 92, "6mo": 183, "1y": 200, "2y": 200, "5y": 200, "10y": 200}


@dataclass
class DataResult:
    frame: pd.DataFrame
    status: str
    source: str
    message: str = ""


def init_page() -> None:
    st.set_page_config(page_title=APP_NAME, page_icon="terminal", layout="wide", initial_sidebar_state="collapsed")
    APP_DIR.mkdir(exist_ok=True)
    inject_css()


def inject_css() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
:root {
  --bg:#06090d; --panel:#0b1118; --panel2:#0f1722; --line:#223041;
  --text:#dce7f3; --muted:#7e8a99; --green:#20d982; --red:#ff5a6d;
  --yellow:#e7c84b; --blue:#4ba3ff; --purple:#9b7cff;
}
html, body, .stApp { background:var(--bg)!important; color:var(--text)!important; font-family:Inter,sans-serif!important; }
#MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display:none!important; }
.block-container { padding:.35rem .65rem 1rem!important; max-width:100%!important; }
[data-testid="stSidebar"] { display:none; }
.terminal-topbar {
  display:grid; grid-template-columns:168px 1fr 390px 128px 255px; gap:8px; align-items:center;
  min-height:38px; border-bottom:1px solid var(--line); background:#030507; position:sticky; top:0; z-index:5;
  margin:-.35rem -.65rem .35rem; padding:0 10px;
}
.brand { font-weight:800; color:#fff; font-size:13px; white-space:nowrap; }
.menu { display:flex; gap:18px; font-size:11px; font-weight:700; color:#c7d1df; text-transform:uppercase; white-space:nowrap; }
.cmd { height:25px; border:1px solid #29384b; background:#060a10; border-radius:3px; color:#8b98aa; display:flex; align-items:center; padding:0 10px; font:11px JetBrains Mono,monospace; overflow:hidden; }
.ai-pill { height:25px; background:#402aa5; color:#fff; border:1px solid #715dff; border-radius:3px; display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:800; white-space:nowrap; }
.session { display:flex; justify-content:flex-end; gap:8px; color:#8b98aa; font-size:11px; align-items:center; white-space:nowrap; }
.strip { display:grid; grid-template-columns:repeat(9,minmax(92px,1fr)); border-bottom:1px solid var(--line); margin:0 -.65rem .45rem; background:#070b10; overflow-x:auto; }
.strip-cell { min-height:49px; border-right:1px solid #1d2837; padding:6px 9px; }
.strip-cell b { display:block; color:#eff6ff; font:700 11px Inter; }
.strip-cell span { display:block; color:#dce7f3; font:600 12px JetBrains Mono; margin-top:3px; }
.strip-cell small { font:500 10px JetBrains Mono; }
.up { color:var(--green)!important; } .down { color:var(--red)!important; } .flat { color:var(--muted)!important; }
.status-chip { display:inline-flex; align-items:center; padding:2px 7px; border:1px solid #314158; border-radius:999px; color:#9fb0c4; background:#0a111b; font-size:10px; font-weight:700; margin-right:5px; }
.status-real { color:var(--green); border-color:rgba(32,217,130,.35); }
.status-delay { color:var(--yellow); border-color:rgba(231,200,75,.35); }
.status-api { color:#ff9f43; border-color:rgba(255,159,67,.35); }
.status-none { color:#8d98a8; }
.terminal-card { border:1px solid var(--line); background:var(--panel); border-radius:4px; min-height:128px; overflow:hidden; margin-bottom:8px; }
.terminal-card h3 { margin:0; padding:7px 9px; border-bottom:1px solid var(--line); background:#080d13; color:#dce7f3; font-size:11px; font-weight:800; text-transform:uppercase; display:flex; justify-content:space-between; align-items:center; }
.terminal-card .body { padding:8px 9px; }
.metric-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:6px; }
.mini-metric { border:1px solid #1e2a39; background:#0d141d; padding:7px; border-radius:3px; min-height:62px; }
.mini-metric label { color:#7f8da0; font-size:10px; display:block; }
.mini-metric strong { font:600 17px JetBrains Mono; color:#edf5ff; display:block; margin-top:4px; }
.mini-metric small { font:500 10px JetBrains Mono; color:#8794a6; }
.dense-table { width:100%; border-collapse:collapse; font-size:11px; }
.dense-table th,.dense-table td { padding:5px 6px; border-bottom:1px solid #192332; text-align:right; white-space:nowrap; }
.dense-table th:first-child,.dense-table td:first-child { text-align:left; }
.dense-table th { color:#91a0b4; font-weight:700; background:#0a1018; }
.dense-table td { color:#dbe5f1; font-family:JetBrains Mono,monospace; }
.warning-box { border:1px solid #694c16; background:#191306; color:#e7c84b; padding:8px 10px; border-radius:4px; font-size:12px; margin-bottom:8px; }
.ok-box { border:1px solid #1d6545; background:#06170f; color:#8af1bd; padding:8px 10px; border-radius:4px; font-size:12px; }
.terminal-grid {
  display:grid; grid-template-columns:minmax(230px, 20%) minmax(420px, 1fr) minmax(260px, 27%);
  gap:6px; align-items:start;
}
.stack { display:grid; gap:6px; }
.terminal-panel {
  border:1px solid var(--line); background:linear-gradient(180deg,#0b1118,#080d13);
  border-radius:3px; overflow:hidden; min-height:100px;
}
.terminal-panel .head {
  height:28px; display:flex; align-items:center; justify-content:space-between; gap:8px;
  padding:0 8px; border-bottom:1px solid var(--line); background:#070b10;
  color:#dce7f3; font-size:10px; font-weight:800; text-transform:uppercase;
}
.terminal-panel .body { padding:8px; }
.term-row { display:flex; align-items:center; justify-content:space-between; gap:10px; padding:4px 0; border-bottom:1px solid #16202d; font-size:11px; }
.term-row:last-child { border-bottom:none; }
.term-label { color:#8d9aae; }
.term-value { color:#eef6ff; font-family:JetBrains Mono,monospace; white-space:nowrap; }
.regime-meter { display:grid; grid-template-columns:74px 1fr; gap:10px; align-items:center; }
.donut {
  width:70px; height:70px; border-radius:50%; display:grid; place-items:center;
  background:conic-gradient(var(--green) var(--meter), #1a2634 0); border:1px solid #26384f;
  box-shadow:inset 0 0 0 9px #0b1118;
}
.donut span { font:700 10px JetBrains Mono,monospace; color:#dce7f3; }
.bar-row { display:grid; grid-template-columns:78px 1fr 52px; gap:7px; align-items:center; padding:4px 0; font-size:10px; }
.bar-track { height:8px; background:#182332; border:1px solid #26384f; border-radius:99px; overflow:hidden; }
.bar-fill { height:100%; background:linear-gradient(90deg,#20d982,#e7c84b); width:var(--w); }
.bar-fill.neg { background:linear-gradient(90deg,#ff5a6d,#7c3340); }
.terminal-chart {
  min-height:270px; border:1px solid #1e2a39; background:
    linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px),
    #081019; background-size:32px 28px; position:relative; overflow:hidden;
}
.chart-line {
  position:absolute; left:12px; right:12px; top:42px; height:120px;
  background:linear-gradient(135deg, transparent 0 10%, rgba(32,217,130,.28) 10% 12%, transparent 12% 28%, rgba(75,163,255,.32) 28% 30%, transparent 30% 48%, rgba(231,200,75,.28) 48% 50%, transparent 50% 72%, rgba(32,217,130,.28) 72% 74%, transparent 74%);
  clip-path:polygon(0 72%, 12% 57%, 24% 63%, 35% 42%, 49% 48%, 62% 28%, 76% 38%, 88% 20%, 100% 26%, 100% 100%, 0 100%);
  opacity:.85;
}
.chart-placeholder {
  position:absolute; left:12px; right:12px; top:62px; bottom:72px; display:grid; place-items:center;
  border:1px dashed #2c3f57; background:rgba(6,9,13,.38); color:#8391a5;
  font-size:11px; text-align:center; line-height:1.5;
}
.chart-status { position:absolute; left:12px; top:12px; display:flex; gap:5px; flex-wrap:wrap; }
.chart-legend { position:absolute; left:12px; right:12px; bottom:10px; display:grid; grid-template-columns:repeat(4,1fr); gap:6px; }
.legend-box { border:1px solid #223041; background:#0a111b; padding:6px; min-height:42px; }
.legend-box label { display:block; color:#8190a4; font-size:9px; }
.legend-box strong { display:block; color:#edf5ff; font:700 12px JetBrains Mono,monospace; margin-top:3px; }
.heat-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:4px; }
.heat-cell { min-height:43px; border:1px solid #233247; background:#101926; padding:6px; }
.heat-cell b { display:block; font-size:10px; color:#dce7f3; }
.heat-cell span { display:block; margin-top:4px; font:700 11px JetBrains Mono,monospace; }
.action-split { display:grid; grid-template-columns:1fr 1fr; gap:5px; }
.paper-btn { text-align:center; padding:7px 0; border:1px solid #28415d; background:#111c2a; font-size:11px; font-weight:800; }
.paper-btn.buy { color:#03140b; background:#20d982; border-color:#20d982; }
.paper-btn.sell { color:#ffb1ba; }
.terminal-note { color:#7d8b9e; font-size:10px; line-height:1.45; }
.stTabs [data-baseweb="tab-list"] { gap:4px; border-bottom:1px solid var(--line); overflow-x:auto; }
.stTabs [data-baseweb="tab"] { height:31px; background:#0a1018; border:1px solid #1e2a39; border-bottom:none; border-radius:3px 3px 0 0; padding:0 12px; }
.stTabs [aria-selected="true"] { background:#132032!important; color:#fff!important; }
.stRadio [role="radiogroup"] {
  display:flex; gap:4px; overflow-x:auto; padding:2px 0 7px; border-bottom:1px solid var(--line);
  scrollbar-width:thin; -webkit-overflow-scrolling:touch;
}
.stRadio [role="radio"] {
  flex:0 0 auto; min-height:31px; padding:0 10px; border:1px solid #1e2a39; border-radius:3px;
  background:#0a1018; align-items:center;
}
.stRadio [role="radio"][aria-checked="true"] { background:#132032; border-color:#38506d; }
.stRadio [role="radio"] p { white-space:nowrap; font-size:12px; }
button,input,textarea,select { border-radius:3px!important; }
[data-testid="stMetric"] { background:#0b1118; border:1px solid #1e2a39; padding:8px; border-radius:4px; }
.js-plotly-plot, .plot-container, .svg-container { max-width:100%!important; }
@media(max-width:1050px) {
  .terminal-topbar { grid-template-columns:1fr; height:auto; padding:8px; }
  .strip { grid-template-columns:repeat(9,120px); }
  .metric-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
}
@media(max-width:760px) {
  .block-container { padding:.25rem .42rem .8rem!important; }
  .terminal-topbar {
    position:relative; margin:-.25rem -.42rem .25rem; gap:6px; padding:8px;
    border-bottom-color:#2a3a50;
  }
  .brand { font-size:12px; }
  .menu {
    gap:8px; overflow-x:auto; padding-bottom:3px; -webkit-overflow-scrolling:touch;
  }
  .menu span {
    flex:0 0 auto; border:1px solid #1e2a39; background:#0a1018; padding:5px 8px; border-radius:3px;
  }
  .cmd { height:32px; font-size:10px; width:100%; }
  .ai-pill { height:32px; }
  .session { justify-content:flex-start; flex-wrap:wrap; font-size:10px; }
  .strip {
    grid-template-columns:none; grid-auto-flow:column; grid-auto-columns:118px;
    margin:0 -.42rem .38rem; scroll-snap-type:x proximity;
  }
  .strip-cell { min-height:54px; padding:7px 8px; scroll-snap-align:start; }
  .strip-cell b { font-size:10px; }
  .strip-cell span { font-size:12px; }
  .strip-cell small { font-size:9px; }
  .stRadio [role="radiogroup"] {
    margin:0 -.1rem .35rem; padding-bottom:8px;
  }
  .stRadio [role="radio"] {
    min-width:max-content; min-height:34px; padding:0 11px;
  }
  .terminal-card { min-height:auto; }
  .terminal-card h3 {
    gap:8px; align-items:flex-start; font-size:10px; flex-direction:column;
  }
  .terminal-card .body {
    overflow-x:auto; -webkit-overflow-scrolling:touch;
  }
  .dense-table { min-width:620px; font-size:10px; }
  .dense-table th, .dense-table td { padding:6px 7px; }
  .metric-grid { grid-template-columns:1fr; }
  .mini-metric { min-height:58px; }
  [data-testid="stHorizontalBlock"] { gap:.35rem; }
  [data-testid="stMetric"] { padding:7px; }
  [data-testid="stMetricValue"] { font-size:1.05rem; }
  iframe { max-width:100%!important; }
  .terminal-grid { grid-template-columns:1fr; }
  .terminal-chart { min-height:240px; }
  .chart-legend { grid-template-columns:repeat(2,1fr); }
  .heat-grid { grid-template-columns:repeat(2,1fr); }
  .regime-meter { grid-template-columns:64px 1fr; }
  .donut { width:60px; height:60px; }
}
</style>
        """,
        unsafe_allow_html=True,
    )


def money(value: Any, prefix: str = "$") -> str:
    if value is None or pd.isna(value):
        return STATUS_NONE
    return f"{prefix}{float(value):,.2f}"


def pct(value: Any) -> str:
    if value is None or pd.isna(value):
        return STATUS_NONE
    return f"{float(value):+.2f}%"


def class_for_change(value: Any) -> str:
    if value is None or pd.isna(value):
        return "flat"
    return "up" if value > 0 else "down" if value < 0 else "flat"


def status_chip(status: str) -> str:
    cls = {
        STATUS_REAL: "status-real",
        STATUS_DELAYED: "status-delay",
        STATUS_API: "status-api",
        STATUS_NONE: "status-none",
    }.get(status, "status-none")
    return f'<span class="status-chip {cls}">{status}</span>'


def toss_credentials_available() -> bool:
    return bool(os.getenv("TOSS_CLIENT_ID", "").strip() and os.getenv("TOSS_CLIENT_SECRET", "").strip())


def normalize_toss_symbol(symbol: str) -> str:
    normalized = str(symbol).strip().upper()
    if normalized.endswith(".KS") or normalized.endswith(".KQ"):
        return normalized[:6]
    return normalized


def is_toss_symbol(symbol: str) -> bool:
    return bool(symbol) and all(ch.isalnum() or ch in ".-" for ch in symbol)


def decimal_or_nan(value: Any) -> float:
    try:
        if value is None or value == "":
            return np.nan
        return float(value)
    except Exception:
        return np.nan


@st.cache_data(ttl=23 * 60 * 60, show_spinner=False)
def issue_toss_token(client_id: str, client_secret: str) -> str:
    response = requests.post(
        f"{TOSS_BASE_URL}/oauth2/token",
        data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=12,
    )
    response.raise_for_status()
    token = response.json().get("access_token")
    if not token:
        raise RuntimeError("토스 OAuth 응답에 access_token이 없습니다.")
    return str(token)


def toss_token() -> str:
    client_id = os.getenv("TOSS_CLIENT_ID", "").strip()
    client_secret = os.getenv("TOSS_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise RuntimeError("TOSS_CLIENT_ID/TOSS_CLIENT_SECRET 환경변수가 필요합니다.")
    return issue_toss_token(client_id, client_secret)


def toss_get(path: str, extra_headers: dict[str, str] | None = None) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {toss_token()}", "User-Agent": "k-fin-terminal/0.1"}
    if extra_headers:
        headers.update(extra_headers)
    response = requests.get(f"{TOSS_BASE_URL}{path}", headers=headers, timeout=12)
    if response.status_code == 401:
        issue_toss_token.clear()
    response.raise_for_status()
    return response.json()


def blank_quote_row(symbol: str, status: str, message: str = "") -> dict[str, Any]:
    return {
        "symbol": symbol,
        "price": np.nan,
        "change_pct": np.nan,
        "volume": np.nan,
        "asof": "",
        "currency": "",
        "status": status,
        "source": TOSS_SOURCE,
        "message": message,
    }


@st.cache_data(ttl=45, show_spinner=False)
def fetch_quote_table(symbols: tuple[str, ...]) -> pd.DataFrame:
    rows = {symbol: blank_quote_row(symbol, STATUS_NONE, "토스증권 시세 응답이 없습니다.") for symbol in symbols}
    if not symbols:
        return pd.DataFrame(rows.values())
    if not toss_credentials_available():
        return pd.DataFrame([blank_quote_row(symbol, STATUS_API, "TOSS_CLIENT_ID/TOSS_CLIENT_SECRET 환경변수가 필요합니다.") for symbol in symbols])

    try:
        fx_symbols = [symbol for symbol in symbols if symbol == "KRW=X"]
        requested = [(symbol, normalize_toss_symbol(symbol)) for symbol in symbols if symbol != "KRW=X"]
        api_symbols = sorted({normalized for _, normalized in requested if is_toss_symbol(normalized)})
        if api_symbols:
            data = toss_get(f"/api/v1/prices?symbols={','.join(api_symbols)}")
            price_map = {str(item.get("symbol", "")).upper(): item for item in data.get("result", [])}
            for original, normalized in requested:
                item = price_map.get(normalized)
                if not item:
                    continue
                price = decimal_or_nan(item.get("lastPrice"))
                rows[original].update(
                    price=price,
                    asof=item.get("timestamp") or "",
                    currency=item.get("currency") or "",
                    status=STATUS_DELAYED if pd.notna(price) else STATUS_NONE,
                    message="현재가만 제공됩니다. 변동률/거래량은 임의 계산하지 않습니다.",
                )
        if fx_symbols:
            data = toss_get("/api/v1/exchange-rate?baseCurrency=USD&quoteCurrency=KRW")
            result = data.get("result", {})
            price = decimal_or_nan(result.get("rate"))
            rows["KRW=X"].update(
                price=price,
                asof=result.get("validFrom") or "",
                currency="KRW",
                status=STATUS_DELAYED if pd.notna(price) else STATUS_NONE,
                message="토스증권 참고용 USD/KRW 환율입니다.",
            )
    except Exception as exc:
        for symbol in symbols:
            rows[symbol]["message"] = str(exc)
    return pd.DataFrame(rows.values())


@st.cache_data(ttl=180, show_spinner=False)
def fetch_single_quote(symbol: str) -> dict[str, Any]:
    table = fetch_quote_table((symbol,))
    if table.empty:
        return blank_quote_row(symbol, STATUS_NONE)
    return table.iloc[0].to_dict()


@st.cache_data(ttl=180, show_spinner=False)
def fetch_price_history(symbol: str, period: str, interval: str) -> DataResult:
    if interval not in ("1d", "1m"):
        return DataResult(pd.DataFrame(), STATUS_NONE, TOSS_SOURCE, "토스증권 캔들은 1d/1m 인터벌만 지원합니다.")
    if not toss_credentials_available():
        return DataResult(pd.DataFrame(), STATUS_API, TOSS_SOURCE, "TOSS_CLIENT_ID/TOSS_CLIENT_SECRET 환경변수가 필요합니다.")
    try:
        normalized = normalize_toss_symbol(symbol)
        if not is_toss_symbol(normalized):
            return DataResult(pd.DataFrame(), STATUS_NONE, TOSS_SOURCE, "토스증권이 지원하지 않는 심볼 형식입니다.")
        count = 200 if interval == "1m" else TOSS_CANDLE_COUNTS.get(period, 200)
        data = toss_get(f"/api/v1/candles?symbol={normalized}&interval={interval}&count={count}&adjusted=true")
        candles = data.get("result", {}).get("candles", [])
        if not candles:
            return DataResult(pd.DataFrame(), STATUS_NONE, TOSS_SOURCE, "No rows returned")
        frame = pd.DataFrame(candles).rename(
            columns={
                "timestamp": "Date",
                "openPrice": "Open",
                "highPrice": "High",
                "lowPrice": "Low",
                "closePrice": "Close",
                "volume": "Volume",
            }
        )
        frame["Date"] = pd.to_datetime(frame["Date"]).dt.tz_localize(None)
        for col in ["Open", "High", "Low", "Close", "Volume"]:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
        frame = frame.sort_values("Date")
        message = "토스증권 캔들은 요청당 최대 200개 봉을 반환합니다." if len(frame) >= 200 else ""
        return DataResult(add_indicators(frame), STATUS_DELAYED, TOSS_SOURCE, message)
    except Exception as exc:
        return DataResult(pd.DataFrame(), STATUS_NONE, TOSS_SOURCE, str(exc))


@st.cache_data(ttl=24 * 60 * 60, show_spinner=False)
def fetch_stock_info(symbols: tuple[str, ...]) -> DataResult:
    if not toss_credentials_available():
        return DataResult(pd.DataFrame(), STATUS_API, TOSS_SOURCE, "TOSS_CLIENT_ID/TOSS_CLIENT_SECRET 환경변수가 필요합니다.")
    normalized = [normalize_toss_symbol(symbol) for symbol in symbols if is_toss_symbol(normalize_toss_symbol(symbol))]
    if not normalized:
        return DataResult(pd.DataFrame(), STATUS_NONE, TOSS_SOURCE, "조회할 수 있는 심볼이 없습니다.")
    try:
        data = toss_get(f"/api/v1/stocks?symbols={','.join(dict.fromkeys(normalized))}")
        rows = data.get("result", [])
        return DataResult(pd.DataFrame(rows), STATUS_DELAYED if rows else STATUS_NONE, TOSS_SOURCE)
    except Exception as exc:
        return DataResult(pd.DataFrame(), STATUS_NONE, TOSS_SOURCE, str(exc))


@st.cache_data(ttl=5 * 60, show_spinner=False)
def fetch_stock_warnings(symbol: str) -> DataResult:
    if not toss_credentials_available():
        return DataResult(pd.DataFrame(), STATUS_API, TOSS_SOURCE, "TOSS_CLIENT_ID/TOSS_CLIENT_SECRET 환경변수가 필요합니다.")
    normalized = normalize_toss_symbol(symbol)
    if not is_toss_symbol(normalized):
        return DataResult(pd.DataFrame(), STATUS_NONE, TOSS_SOURCE, "토스증권이 지원하지 않는 심볼 형식입니다.")
    try:
        data = toss_get(f"/api/v1/stocks/{normalized}/warnings")
        rows = data.get("result", [])
        return DataResult(pd.DataFrame(rows), STATUS_DELAYED if rows else STATUS_NONE, TOSS_SOURCE)
    except Exception as exc:
        return DataResult(pd.DataFrame(), STATUS_NONE, TOSS_SOURCE, str(exc))


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col not in out.columns:
            out[col] = np.nan
    out["MA20"] = out["Close"].rolling(20).mean()
    out["MA50"] = out["Close"].rolling(50).mean()
    out["MA200"] = out["Close"].rolling(200).mean()
    mid = out["Close"].rolling(20).mean()
    std = out["Close"].rolling(20).std()
    out["BB_UPPER"] = mid + 2 * std
    out["BB_LOWER"] = mid - 2 * std
    delta = out["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    out["RSI"] = 100 - (100 / (1 + rs))
    ema12 = out["Close"].ewm(span=12, adjust=False).mean()
    ema26 = out["Close"].ewm(span=26, adjust=False).mean()
    out["MACD"] = ema12 - ema26
    out["MACD_SIGNAL"] = out["MACD"].ewm(span=9, adjust=False).mean()
    return out


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_user_file(username: str) -> Path:
    safe = "".join(ch for ch in username.lower() if ch.isalnum() or ch in ("_", "-"))[:48] or "guest"
    path = APP_DIR / f"{safe}.json"
    if not path.exists():
        save_json(
            path,
            {
                "user_id": safe,
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "watchlist": WATCHLIST_DEFAULT,
                "settings": {"default_symbol": "AAPL", "ai_provider": "rules", "broker_mode": "paper", "layout": "terminal-grid"},
                "portfolio": [
                    {"ticker": "AAPL", "shares": 3.0, "cost_basis": 165.0, "currency": "USD", "sector": "Technology", "country": "US"},
                    {"ticker": "SPY", "shares": 1.0, "cost_basis": 480.0, "currency": "USD", "sector": "ETF", "country": "US"},
                ],
            },
        )
    return path


def load_owner_profile() -> dict[str, Any]:
    st.session_state.user = "OWNER"
    return load_json(ensure_user_file(OWNER_ID), {})


def persist_user(data: dict[str, Any]) -> None:
    save_json(ensure_user_file(OWNER_ID), data)


def topbar() -> None:
    user_label = "OWNER"
    st.markdown(
        f"""
<div class="terminal-topbar">
  <div class="brand">K-FIN TERMINAL ></div>
  <div class="menu"><span>Markets</span><span>Portfolio</span><span>Toss Info</span><span>Tools</span><span>AI</span></div>
  <div class="cmd">LLM &lt;GO&gt; &nbsp; Ask anything or enter a command</div>
  <div class="ai-pill">AI COPILOT</div>
  <div class="session"><span>TOSS</span><span>{datetime.now().strftime('%H:%M:%S')}</span><span class="up">Read-only</span><span>{user_label}</span></div>
</div>
        """,
        unsafe_allow_html=True,
    )
    strip = fetch_quote_table(tuple(US_MARKET_TICKERS.values()))
    cells = []
    for label, symbol in US_MARKET_TICKERS.items():
        row = strip[strip["symbol"] == symbol]
        if row.empty:
            cells.append(f"<div class='strip-cell'><b>{label}</b><span>{STATUS_NONE}</span><small class='flat'>{STATUS_NONE}</small></div>")
            continue
        item = row.iloc[0]
        price = item.get("price", np.nan)
        price_text = f"{price:,.2f}" if pd.notna(price) else STATUS_NONE
        cls = class_for_change(item.get("change_pct"))
        cells.append(f"<div class='strip-cell'><b>{label}</b><span>{price_text}</span><small class='{cls}'>{pct(item.get('change_pct'))} · {item.get('status')}</small></div>")
    st.markdown(f"<div class='strip'>{''.join(cells)}</div>", unsafe_allow_html=True)


def quote_record(quotes: pd.DataFrame, symbol: str) -> dict[str, Any]:
    row = quotes[quotes["symbol"] == symbol]
    if row.empty:
        return {"symbol": symbol, "price": np.nan, "change_pct": np.nan, "status": STATUS_NONE}
    return row.iloc[0].to_dict()


def quote_price_text(record: dict[str, Any], prefix: str = "$") -> str:
    value = record.get("price", np.nan)
    if pd.isna(value):
        return STATUS_NONE
    if prefix:
        return money(value, prefix)
    return f"{float(value):,.2f}"


def quote_pct_text(record: dict[str, Any]) -> str:
    return pct(record.get("change_pct", np.nan))


def quote_status_text(record: dict[str, Any]) -> str:
    return str(record.get("status") or STATUS_NONE)


def render_bar(label: str, value: Any) -> str:
    if value is None or pd.isna(value):
        return f"<div class='bar-row'><span class='term-label'>{label}</span><div class='bar-track'></div><span class='term-value'>{STATUS_NONE}</span></div>"
    width = max(6, min(100, abs(float(value)) * 18))
    cls = "neg" if float(value) < 0 else ""
    return (
        f"<div class='bar-row'><span class='term-label'>{label}</span>"
        f"<div class='bar-track'><div class='bar-fill {cls}' style='--w:{width:.0f}%'></div></div>"
        f"<span class='{class_for_change(value)} term-value'>{pct(value)}</span></div>"
    )


def render_price_row(label: str, record: dict[str, Any], prefix: str = "$") -> str:
    value = record.get("price", np.nan)
    width = 64 if pd.notna(value) else 0
    return (
        f"<div class='bar-row'><span class='term-label'>{label}</span>"
        f"<div class='bar-track'><div class='bar-fill' style='--w:{width:.0f}%'></div></div>"
        f"<span class='term-value'>{quote_price_text(record, prefix)}</span></div>"
    )


def render_heat_cell(label: str, record: dict[str, Any]) -> str:
    prefix = "₩" if record.get("currency") == "KRW" else "$"
    return f"<div class='heat-cell'><b>{label}</b><span class='flat'>{quote_price_text(record, prefix)}</span></div>"


def render_terminal_dashboard(quotes: pd.DataFrame) -> None:
    aapl = quote_record(quotes, "AAPL")
    msft = quote_record(quotes, "MSFT")
    nvda = quote_record(quotes, "NVDA")
    tsla = quote_record(quotes, "TSLA")
    spy = quote_record(quotes, "SPY")
    qqq = quote_record(quotes, "QQQ")
    samsung = quote_record(quotes, "005930")
    usdkrw = quote_record(quotes, "KRW=X")

    if pd.isna(spy.get("price", np.nan)) or pd.isna(qqq.get("price", np.nan)):
        regime = STATUS_NONE
        regime_detail = "토스 API 키가 없거나 응답이 제한되었습니다."
        meter = 18
    else:
        regime = "WATCHLIST"
        regime_detail = "토스 현재가 기반 감시 모드. 변동률은 임의 계산하지 않습니다."
        meter = 62

    bars = "\n".join(
        [
            render_price_row("AAPL", aapl),
            render_price_row("NVDA", nvda),
            render_price_row("SPY", spy),
            render_price_row("QQQ", qqq),
            render_price_row("Samsung", samsung, "₩"),
        ]
    )
    html = f"""
<div class="terminal-grid">
  <div class="stack">
    <section class="terminal-panel">
      <div class="head"><span>Toss Market Pulse</span>{status_chip(quote_status_text(spy))}</div>
      <div class="body">
        <div class="regime-meter">
          <div class="donut" style="--meter:{meter}%;"><span>{regime}</span></div>
          <div>
            <div class="term-row"><span class="term-label">SPY</span><span class="term-value">{quote_price_text(spy)}</span></div>
            <div class="term-row"><span class="term-label">QQQ</span><span class="term-value">{quote_price_text(qqq)}</span></div>
            <div class="term-row"><span class="term-label">USD/KRW</span><span class="term-value">{quote_price_text(usdkrw, '₩')}</span></div>
            <div class="terminal-note">{regime_detail}</div>
          </div>
        </div>
      </div>
    </section>
    <section class="terminal-panel">
      <div class="head"><span>Momentum Board</span><span class="status-chip">Watchlist</span></div>
      <div class="body">{bars}</div>
    </section>
    <section class="terminal-panel">
      <div class="head"><span>Data Coverage</span><span class="status-chip status-api">Provider</span></div>
      <div class="body">
        <div class="term-row"><span class="term-label">US/KR Quotes</span><span class="term-value">Toss</span></div>
        <div class="term-row"><span class="term-label">Stock Info</span><span class="term-value">Toss</span></div>
        <div class="term-row"><span class="term-label">Warnings</span><span class="term-value">Toss</span></div>
        <div class="term-row"><span class="term-label">Index/Commodity</span><span class="term-value">제외됨</span></div>
      </div>
    </section>
  </div>
  <div class="stack">
    <section class="terminal-panel">
      <div class="head"><span>Cross-Asset Monitor</span><span class="status-chip">Actual when available</span></div>
      <div class="body">
        <div class="terminal-chart">
          <div class="chart-status">
            {status_chip(quote_status_text(spy))}
            <span class="status-chip">No synthetic prices</span>
            <span class="status-chip">Toss read-only</span>
          </div>
          <div class="chart-placeholder">실제 캔들/거래량/RSI/MACD는 차트 탭에서 선택한 기간과 인터벌로 로드됩니다.<br>첫 화면은 빠른 시장 상태만 표시합니다.</div>
          <div class="chart-legend">
            <div class="legend-box"><label>AAPL</label><strong>{quote_price_text(aapl)}</strong></div>
            <div class="legend-box"><label>NVDA</label><strong>{quote_price_text(nvda)}</strong></div>
            <div class="legend-box"><label>005930</label><strong>{quote_price_text(samsung, '₩')}</strong></div>
            <div class="legend-box"><label>USD/KRW</label><strong>{quote_price_text(usdkrw, '₩')}</strong></div>
          </div>
        </div>
      </div>
    </section>
    <section class="terminal-panel">
      <div class="head"><span>Price Board</span><span class="status-chip">Current</span></div>
      <div class="body">
        <div class="heat-grid">
          {render_heat_cell("AAPL", aapl)}
          {render_heat_cell("MSFT", msft)}
          {render_heat_cell("NVDA", nvda)}
          {render_heat_cell("TSLA", tsla)}
          {render_heat_cell("SPY", spy)}
          {render_heat_cell("QQQ", qqq)}
          {render_heat_cell("Samsung", samsung)}
          {render_heat_cell("USD/KRW", usdkrw)}
        </div>
      </div>
    </section>
  </div>
  <div class="stack">
    <section class="terminal-panel">
      <div class="head"><span>AI Assistant</span><span class="status-chip">Local Rules</span></div>
      <div class="body">
        <div class="term-row"><span class="term-label">Fallback</span><span class="term-value">Rules</span></div>
        <div class="term-row"><span class="term-label">External AI</span><span class="term-value">제거됨</span></div>
        <div class="terminal-note">토스 차트와 로컬 포트폴리오를 바탕으로 규칙 기반 한국어 요약만 사용합니다.</div>
      </div>
    </section>
    <section class="terminal-panel">
      <div class="head"><span>Portfolio Risk</span><span class="status-chip">Local</span></div>
      <div class="body">
        <div class="term-row"><span class="term-label">Holdings</span><span class="term-value">자동 저장</span></div>
        <div class="term-row"><span class="term-label">Sector/Currency</span><span class="term-value">저장 가능</span></div>
        <div class="term-row"><span class="term-label">External Sync</span><span class="term-value">토스 읽기 전용 확장</span></div>
      </div>
    </section>
  </div>
</div>
    """
    st.markdown(html, unsafe_allow_html=True)


def chart_figure(frame: pd.DataFrame, symbol: str) -> go.Figure:
    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.55, 0.15, 0.15, 0.15],
    )
    fig.add_trace(go.Candlestick(x=frame["Date"], open=frame["Open"], high=frame["High"], low=frame["Low"], close=frame["Close"], name=symbol), row=1, col=1)
    for col, color in [("MA20", "#4ba3ff"), ("MA50", "#e7c84b"), ("MA200", "#ff5a6d"), ("BB_UPPER", "#5d6f85"), ("BB_LOWER", "#5d6f85")]:
        fig.add_trace(go.Scatter(x=frame["Date"], y=frame[col], mode="lines", line=dict(width=1, color=color), name=col), row=1, col=1)
    fig.add_trace(go.Bar(x=frame["Date"], y=frame["Volume"], marker_color="#334155", name="Volume"), row=2, col=1)
    fig.add_trace(go.Scatter(x=frame["Date"], y=frame["RSI"], mode="lines", line=dict(color="#9b7cff", width=1), name="RSI"), row=3, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="#ff5a6d", row=3, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="#20d982", row=3, col=1)
    fig.add_trace(go.Scatter(x=frame["Date"], y=frame["MACD"], mode="lines", line=dict(color="#4ba3ff", width=1), name="MACD"), row=4, col=1)
    fig.add_trace(go.Scatter(x=frame["Date"], y=frame["MACD_SIGNAL"], mode="lines", line=dict(color="#e7c84b", width=1), name="Signal"), row=4, col=1)
    fig.update_layout(
        height=620,
        margin=dict(l=8, r=8, t=28, b=8),
        template="plotly_dark",
        paper_bgcolor="#0b1118",
        plot_bgcolor="#0b1118",
        font=dict(color="#dce7f3", family="Inter"),
        title=f"{symbol} Candles · Volume · RSI · MACD",
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, x=0),
    )
    return fig


def market_tab() -> None:
    symbols = list(dict.fromkeys(WATCHLIST_DEFAULT + list(US_MARKET_TICKERS.values())))
    quotes = fetch_quote_table(tuple(symbols))
    render_terminal_dashboard(quotes)
    rows = []
    for _, row in quotes.iterrows():
        volume = int(row.get("volume", 0)) if pd.notna(row.get("volume", np.nan)) else STATUS_NONE
        rows.append(
            f"<tr><td>{row.get('symbol')}</td><td>{money(row.get('price'))}</td><td class='{class_for_change(row.get('change_pct'))}'>{pct(row.get('change_pct'))}</td><td>{volume}</td><td>{row.get('status')}</td><td>{row.get('source')}</td></tr>"
        )
    st.markdown("<div class='terminal-card'><h3>Raw Market Monitor <span>Toss stocks/ETF/FX</span></h3><div class='body'>", unsafe_allow_html=True)
    st.markdown("<table class='dense-table'><thead><tr><th>Ticker</th><th>Last</th><th>Chg%</th><th>Volume</th><th>Status</th><th>Source</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table></div></div>", unsafe_allow_html=True)
    st.info("토스 현재가 응답에 없는 변동률/거래량은 임의 계산하지 않습니다. 지수, 원자재, 금리, 뉴스, 공시는 현재 범위에서 제외했습니다.")


def charts_tab(user_data: dict[str, Any] | None) -> tuple[str, DataResult]:
    settings = (user_data or {}).get("settings", {})
    cols = st.columns([1, 1, 1, 6])
    symbol = cols[0].text_input("티커", settings.get("default_symbol", "AAPL")).upper().strip() or "AAPL"
    period = cols[1].selectbox("기간", PERIOD_OPTIONS, index=PERIOD_OPTIONS.index("1y"))
    interval = cols[2].selectbox("인터벌", INTERVAL_OPTIONS)
    result = fetch_price_history(symbol, period, interval)
    cols[3].markdown(f"{status_chip(result.status)} <span class='status-chip'>{result.source}</span>", unsafe_allow_html=True)
    if result.frame.empty:
        st.error(f"{symbol}: {STATUS_NONE}. {result.message}")
    else:
        st.plotly_chart(chart_figure(result.frame, symbol), use_container_width=True)
    return symbol, result


def portfolio_frame(user_data: dict[str, Any] | None) -> pd.DataFrame:
    records = (user_data or {}).get("portfolio", [])
    return pd.DataFrame(records, columns=["ticker", "shares", "cost_basis", "currency", "sector", "country"])


def enrich_portfolio(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    quotes = fetch_quote_table(tuple(df["ticker"].dropna().astype(str).unique()))
    for col in ["symbol", "price", "status"]:
        if col not in quotes.columns:
            quotes[col] = np.nan
    merged = df.merge(quotes[["symbol", "price", "status"]], left_on="ticker", right_on="symbol", how="left")
    merged["market_value"] = merged["shares"].astype(float) * merged["price"].astype(float)
    merged["cost_value"] = merged["shares"].astype(float) * merged["cost_basis"].astype(float)
    merged["pnl"] = merged["market_value"] - merged["cost_value"]
    merged["pnl_pct"] = merged["pnl"] / merged["cost_value"] * 100
    total = merged["market_value"].sum()
    merged["weight"] = merged["market_value"] / total * 100 if total else np.nan
    return merged


def portfolio_tab(user_data: dict[str, Any] | None) -> None:
    if user_data is None:
        user_data = load_owner_profile()
    raw = portfolio_frame(user_data)
    edited = st.data_editor(
        raw,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "ticker": st.column_config.TextColumn("Ticker"),
            "shares": st.column_config.NumberColumn("Shares", min_value=0.0, step=0.01),
            "cost_basis": st.column_config.NumberColumn("Cost Basis", min_value=0.0, step=0.01),
            "currency": st.column_config.SelectboxColumn("Currency", options=["USD", "KRW", "JPY", "EUR"]),
            "sector": st.column_config.TextColumn("Sector"),
            "country": st.column_config.SelectboxColumn("Country", options=["US", "KR", "JP", "EU", "Other"]),
        },
        key="portfolio_editor",
    )
    if st.button("포트폴리오 저장", use_container_width=True):
        user_data["portfolio"] = edited.to_dict("records")
        persist_user(user_data)
        st.success("저장했습니다.")
    enriched = enrich_portfolio(edited)
    if enriched.empty:
        st.info("수동 입력으로 보유 종목을 추가하세요.")
        return
    total_value = enriched["market_value"].sum()
    pnl = enriched["pnl"].sum()
    cost_sum = enriched["cost_value"].sum()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("평가금액", money(total_value))
    c2.metric("손익", money(pnl), pct(pnl / cost_sum * 100 if cost_sum else np.nan))
    c3.metric("배당 예상", STATUS_API, "배당 데이터 API 필요")
    c4.metric("리밸런싱", "확인 필요" if pd.notna(enriched["weight"].max()) and enriched["weight"].max() > 45 else "정상")
    fig = make_subplots(rows=1, cols=3, specs=[[{"type": "domain"}, {"type": "domain"}, {"type": "domain"}]], subplot_titles=["종목 비중", "섹터 비중", "국가 비중"])
    fig.add_trace(go.Pie(labels=enriched["ticker"], values=enriched["market_value"], hole=0.45), row=1, col=1)
    fig.add_trace(go.Pie(labels=enriched["sector"], values=enriched["market_value"], hole=0.45), row=1, col=2)
    fig.add_trace(go.Pie(labels=enriched["country"], values=enriched["market_value"], hole=0.45), row=1, col=3)
    fig.update_layout(height=380, template="plotly_dark", paper_bgcolor="#0b1118", font=dict(color="#dce7f3"), margin=dict(l=8, r=8, t=45, b=8))
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("포트폴리오 그래프 크게 보기", expanded=False):
        fig.update_layout(height=720)
        st.plotly_chart(fig, use_container_width=True)


def research_tab(symbol: str) -> None:
    selected = st.text_input("토스 종목 심볼", value=normalize_toss_symbol(symbol)).upper().strip() or normalize_toss_symbol(symbol)
    info_result = fetch_stock_info((selected,))
    warning_result = fetch_stock_warnings(selected)
    st.markdown(f"{status_chip(info_result.status)} <span class='status-chip'>{info_result.source}</span>", unsafe_allow_html=True)
    if info_result.frame.empty:
        st.warning(f"{selected}: {info_result.message or STATUS_NONE}")
        return

    info = info_result.frame.iloc[0].to_dict()
    st.markdown(
        f"""
<div class="metric-grid">
<div class="mini-metric"><label>Name</label><strong>{info.get('name', STATUS_NONE)}</strong><small>{info.get('englishName', '')}</small></div>
<div class="mini-metric"><label>Market</label><strong>{info.get('market', STATUS_NONE)}</strong><small>{info.get('securityType', '')}</small></div>
<div class="mini-metric"><label>Status</label><strong>{info.get('status', STATUS_NONE)}</strong><small>{info.get('currency', '')}</small></div>
<div class="mini-metric"><label>Shares</label><strong>{fmt_compact(info.get('sharesOutstanding'))}</strong><small>Outstanding</small></div>
</div>
        """,
        unsafe_allow_html=True,
    )
    detail_rows = [
        ("Symbol", info.get("symbol", STATUS_NONE)),
        ("ISIN", info.get("isinCode", STATUS_NONE)),
        ("List Date", info.get("listDate", STATUS_NONE)),
        ("Delist Date", info.get("delistDate") or "-"),
        ("Common Share", str(info.get("isCommonShare", STATUS_NONE))),
        ("Leverage Factor", info.get("leverageFactor") or "-"),
    ]
    st.table(pd.DataFrame(detail_rows, columns=["항목", "값"]))

    st.markdown(f"{status_chip(warning_result.status)} <span class='status-chip'>Warnings</span>", unsafe_allow_html=True)
    if warning_result.frame.empty:
        st.info(warning_result.message or "활성 매수 유의사항이 없습니다.")
    else:
        st.dataframe(warning_result.frame, use_container_width=True)


def fmt_compact(value: Any) -> str:
    number = decimal_or_nan(value)
    if pd.isna(number):
        return STATUS_NONE
    if abs(number) >= 1_000_000_000:
        return f"{number / 1_000_000_000:.2f}B"
    if abs(number) >= 1_000_000:
        return f"{number / 1_000_000:.2f}M"
    return f"{number:,.0f}"


def ai_summary(symbol: str, price_result: DataResult, portfolio: pd.DataFrame) -> str:
    frame = price_result.frame
    if frame.empty:
        return f"{symbol}: {STATUS_NONE}. 분석할 가격 데이터가 없습니다."
    latest = frame.iloc[-1]
    change_20 = frame["Close"].pct_change(20).iloc[-1] * 100 if len(frame) > 20 else np.nan
    rsi = latest.get("RSI", np.nan)
    holdings = portfolio[portfolio["ticker"].str.upper() == symbol.upper()] if not portfolio.empty else pd.DataFrame()
    position = "보유 없음" if holdings.empty else f"보유 {holdings['shares'].sum():,.4g}주"
    base = f"{symbol} 규칙 기반 요약: 최근 종가 {money(latest.get('Close'))}, 20거래일 수익률 {pct(change_20)}, RSI {rsi:.1f}입니다. 포트폴리오 상태: {position}. "
    if pd.notna(rsi) and rsi >= 70:
        return base + "RSI 기준 단기 과열 구간입니다."
    if pd.notna(rsi) and rsi <= 30:
        return base + "RSI 기준 단기 침체 구간입니다."
    return base + "기술적 모멘텀은 중립에 가깝습니다."


def ai_tab(symbol: str, price_result: DataResult, user_data: dict[str, Any] | None) -> None:
    portfolio = portfolio_frame(user_data)
    prompt = st.text_area("질문", value=f"{symbol}의 차트와 포트폴리오 관점 요약")
    if st.button("분석 실행", use_container_width=True):
        st.markdown(f"<div class='ok-box'>{ai_summary(symbol, price_result, portfolio)}</div>", unsafe_allow_html=True)
        st.caption(f"입력 질문: {prompt}")


def tools_tab(user_data: dict[str, Any] | None) -> None:
    st.subheader("사용자 설정")
    if user_data is None:
        user_data = load_owner_profile()
    settings = user_data.setdefault("settings", {})
    cols = st.columns(4)
    settings["default_symbol"] = cols[0].text_input("기본 종목", settings.get("default_symbol", "AAPL"))
    settings["ai_provider"] = cols[1].selectbox("AI 기본값", ["rules"], index=0)
    settings["data_provider"] = cols[2].selectbox("데이터 제공자", ["toss"], index=0)
    settings["layout"] = cols[3].selectbox("레이아웃", ["terminal-grid", "compact"], index=0)
    if st.button("설정 저장", use_container_width=True):
        persist_user(user_data)
        st.success("저장했습니다.")
    envs = [
        ("TOSS_CLIENT_ID", "토스 OAuth client id"),
        ("TOSS_CLIENT_SECRET", "토스 OAuth client secret"),
    ]
    st.table(pd.DataFrame([{"env": name, "purpose": purpose, "status": "설정됨" if os.getenv(name) else STATUS_API} for name, purpose in envs]))


def layout_tab() -> None:
    components.html(
        """
<div class="terminal-html">
  <style>
    body { margin:0; background:#06090d; color:#dce7f3; font-family:Inter, Arial, sans-serif; }
    .workspace { height:680px; display:grid; grid-template-columns:22% 1fr 28%; gap:5px; background:#06090d; overflow:hidden; }
    .panel { min-width:180px; overflow:auto; resize:horizontal; border:1px solid #223041; background:#0b1118; position:relative; }
    .panel h4 { margin:0; padding:7px 8px; font-size:11px; text-transform:uppercase; border-bottom:1px solid #223041; background:#080d13; }
    .grid { position:relative; min-height:620px; }
    .box { position:absolute; width:280px; min-width:160px; min-height:90px; resize:both; overflow:auto; border:1px solid #2a3a50; background:#0f1722; border-radius:3px; box-shadow:0 8px 20px rgba(0,0,0,.25); }
    .box header { cursor:move; user-select:none; padding:7px 8px; background:#111c2a; border-bottom:1px solid #2a3a50; font-size:11px; font-weight:800; display:flex; justify-content:space-between; }
    .box p { margin:8px; font-size:11px; color:#aebcce; line-height:1.4; }
    .green { color:#20d982; } .yellow { color:#e7c84b; }
    .hint { position:absolute; bottom:7px; left:8px; right:8px; color:#65758a; font-size:10px; }
    @media(max-width: 760px) {
      .workspace { height:920px; display:block; overflow:auto; }
      .panel { width:100% !important; min-width:0; height:300px; margin-bottom:6px; resize:vertical; }
      .grid { min-height:250px; }
      .box { left:10px !important; width:calc(100% - 20px) !important; min-width:0; resize:vertical; }
      .box header { min-height:34px; align-items:center; }
      .hint { position:static; padding:8px; }
    }
  </style>
  <div class="workspace">
    <section class="panel"><h4>Market Pulse</h4><div class="grid" id="left"></div></section>
    <section class="panel"><h4>Charts / Toss Info</h4><div class="grid" id="center"></div></section>
    <section class="panel"><h4>AI / Risk</h4><div class="grid" id="right"></div></section>
  </div>
  <script>
    const defaults = [
      ["left","Toss Pulse","Watchlist<br><span class='green'>Read-only market data</span>",10,10,250,120],
      ["left","Toss Prices","AAPL / NVDA / SPY / QQQ / Samsung / USDKRW",10,150,250,150],
      ["center","Main Chart","Drag cards, resize boxes, and resize panel borders. Layout is saved in this browser.",10,10,430,250],
      ["center","Toss Stock Info","Name, market, currency, listing status, warnings.",455,10,300,250],
      ["center","Portfolio Graph","Use app Portfolio tab for large mode.",10,280,360,180],
      ["right","AI Assistant","Local rule summary only.<br>No external AI API.",10,10,260,130],
      ["right","Risk","Max weight, sector, currency and country concentration.",10,170,260,150]
    ];
    const saved = JSON.parse(localStorage.getItem("kfin-layout-v1") || "null") || defaults;
    function makeBox(item) {
      const [panel,title,html,x,y,w,h] = item;
      const b = document.createElement("div");
      b.className = "box"; b.dataset.title = title; b.dataset.panel = panel;
      b.style.left=x+"px"; b.style.top=y+"px"; b.style.width=w+"px"; b.style.height=h+"px";
      b.innerHTML = `<header><span>${title}</span><span>::</span></header><p>${html}</p>`;
      document.getElementById(panel).appendChild(b);
      drag(b);
    }
    saved.forEach(makeBox);
    function persist() {
      const all = [...document.querySelectorAll(".box")].map(b => [b.dataset.panel,b.dataset.title,b.querySelector("p").innerHTML,parseInt(b.style.left),parseInt(b.style.top),b.offsetWidth,b.offsetHeight]);
      localStorage.setItem("kfin-layout-v1", JSON.stringify(all));
    }
    function drag(el) {
      const head = el.querySelector("header");
      let sx=0, sy=0, ox=0, oy=0, active=false;
      head.addEventListener("mousedown", e => { active=true; sx=e.clientX; sy=e.clientY; ox=parseInt(el.style.left); oy=parseInt(el.style.top); e.preventDefault(); });
      window.addEventListener("mousemove", e => { if(!active) return; el.style.left=Math.max(0, ox+e.clientX-sx)+"px"; el.style.top=Math.max(0, oy+e.clientY-sy)+"px"; });
      window.addEventListener("mouseup", () => { if(active){ active=false; persist(); } });
      new ResizeObserver(persist).observe(el);
    }
    const note = document.createElement("div"); note.className="hint"; note.textContent="레이아웃 저장: browser localStorage. 단일 사용자용 커스텀 터미널.";
    document.body.appendChild(note);
  </script>
</div>
        """,
        height=720,
    )


def main() -> None:
    init_page()
    user_data = load_owner_profile()
    topbar()
    nav_items = ["시장", "모니터", "차트", "포트폴리오", "토스 종목정보", "AI", "설정", "레이아웃"]
    active_tab = st.radio("탭", nav_items, horizontal=True, label_visibility="collapsed", key="active_terminal_tab")
    symbol = (user_data or {}).get("settings", {}).get("default_symbol", "AAPL")
    price_result = DataResult(pd.DataFrame(), STATUS_NONE, "Not loaded")

    if active_tab == "시장":
        market_tab()
    elif active_tab == "모니터":
        layout_tab()
    elif active_tab == "차트":
        symbol, price_result = charts_tab(user_data)
    elif active_tab == "포트폴리오":
        portfolio_tab(user_data)
    elif active_tab == "토스 종목정보":
        research_tab(symbol)
    elif active_tab == "AI":
        price_result = fetch_price_history(symbol, "1y", "1d")
        ai_tab(symbol, price_result, user_data)
    elif active_tab == "설정":
        tools_tab(user_data)
    elif active_tab == "레이아웃":
        layout_tab()


if __name__ == "__main__":
    main()
