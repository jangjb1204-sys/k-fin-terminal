import hashlib
import hmac
import json
import os
import uuid
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
import yfinance as yf
from plotly.subplots import make_subplots


APP_NAME = "K-Fin Terminal"
APP_DIR = Path(".terminal_data")
STATUS_REAL = "실제 데이터"
STATUS_DELAYED = "지연 데이터"
STATUS_API = "API 필요"
STATUS_NONE = "데이터 없음"

US_MARKET_TICKERS = {
    "SPX": "^GSPC",
    "NDX": "^IXIC",
    "DJI": "^DJI",
    "VIX": "^VIX",
    "US10Y": "^TNX",
    "WTI": "CL=F",
    "GOLD": "GC=F",
    "USD/KRW": "KRW=X",
    "BTC": "BTC-USD",
}
WATCHLIST_DEFAULT = ["AAPL", "MSFT", "NVDA", "TSLA", "SPY", "QQQ", "005930.KS"]
PERIOD_OPTIONS = ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y"]
INTERVAL_OPTIONS = ["1d", "1wk", "1mo"]


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
.news-item { border-bottom:1px solid #192332; padding:8px 0; }
.news-item b { display:block; font-size:12px; color:#edf5ff; }
.news-item p { margin:4px 0; color:#a8b6c8; font-size:11px; line-height:1.45; }
.news-meta { color:#7d8b9e; font:10px JetBrains Mono; display:flex; gap:8px; flex-wrap:wrap; }
.warning-box { border:1px solid #694c16; background:#191306; color:#e7c84b; padding:8px 10px; border-radius:4px; font-size:12px; margin-bottom:8px; }
.ok-box { border:1px solid #1d6545; background:#06170f; color:#8af1bd; padding:8px 10px; border-radius:4px; font-size:12px; }
.stTabs [data-baseweb="tab-list"] { gap:4px; border-bottom:1px solid var(--line); overflow-x:auto; }
.stTabs [data-baseweb="tab"] { height:31px; background:#0a1018; border:1px solid #1e2a39; border-bottom:none; border-radius:3px 3px 0 0; padding:0 12px; }
.stTabs [aria-selected="true"] { background:#132032!important; color:#fff!important; }
button,input,textarea,select { border-radius:3px!important; }
[data-testid="stMetric"] { background:#0b1118; border:1px solid #1e2a39; padding:8px; border-radius:4px; }
@media(max-width:1050px) {
  .terminal-topbar { grid-template-columns:1fr; height:auto; padding:8px; }
  .strip { grid-template-columns:repeat(9,120px); }
  .metric-grid { grid-template-columns:repeat(2,minmax(0,1fr)); }
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


@st.cache_data(ttl=45, show_spinner=False)
def fetch_quote_table(symbols: tuple[str, ...]) -> pd.DataFrame:
    rows = []
    for symbol in symbols:
        row = {
            "symbol": symbol,
            "price": np.nan,
            "change_pct": np.nan,
            "volume": np.nan,
            "asof": "",
            "status": STATUS_NONE,
            "source": "Yahoo Finance",
            "message": "",
        }
        try:
            hist = yf.Ticker(symbol).history(period="5d", interval="1d", auto_adjust=False)
            if hist.empty:
                rows.append(row)
                continue
            last = hist.iloc[-1]
            prev = hist["Close"].iloc[-2] if len(hist) > 1 else np.nan
            change_pct = (last["Close"] / prev - 1) * 100 if prev and not pd.isna(prev) else np.nan
            row.update(
                price=float(last["Close"]),
                change_pct=float(change_pct) if not pd.isna(change_pct) else np.nan,
                volume=float(last.get("Volume", np.nan)),
                asof=str(hist.index[-1]),
                status=STATUS_DELAYED,
            )
        except Exception as exc:
            row["message"] = str(exc)
        rows.append(row)
    return pd.DataFrame(rows)


@st.cache_data(ttl=180, show_spinner=False)
def fetch_price_history(symbol: str, period: str, interval: str) -> DataResult:
    try:
        frame = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=False)
        if frame.empty:
            return DataResult(pd.DataFrame(), STATUS_NONE, "Yahoo Finance", "No rows returned")
        frame = frame.reset_index()
        date_col = "Datetime" if "Datetime" in frame.columns else "Date"
        frame[date_col] = pd.to_datetime(frame[date_col]).dt.tz_localize(None)
        frame = frame.rename(columns={date_col: "Date"})
        return DataResult(add_indicators(frame), STATUS_DELAYED, "Yahoo Finance")
    except Exception as exc:
        return DataResult(pd.DataFrame(), STATUS_NONE, "Yahoo Finance", str(exc))


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


@st.cache_data(ttl=300, show_spinner=False)
def fetch_news(symbol: str, limit: int = 8) -> list[dict[str, Any]]:
    try:
        items = yf.Ticker(symbol).news or []
    except Exception:
        return []
    normalized = []
    for item in items[:limit]:
        content = item.get("content", item)
        title = content.get("title") or item.get("title") or STATUS_NONE
        summary = content.get("summary") or content.get("description") or item.get("summary") or ""
        link = content.get("canonicalUrl", {}).get("url") or item.get("link") or ""
        provider = content.get("provider", {}).get("displayName") or item.get("publisher") or "Yahoo Finance"
        text = f"{title} {summary}"
        normalized.append(
            {
                "title": title,
                "summary": summary,
                "link": link,
                "provider": provider,
                "sentiment": rule_sentiment(text),
                "importance": rule_importance(text),
                "tickers": extract_tickers(text, symbol),
                "ko": translate_or_mark(summary or title),
            }
        )
    return normalized


def rule_sentiment(text: str) -> str:
    lower = text.lower()
    positive = ["beats", "surge", "rally", "upgrade", "record", "growth", "strong", "bullish", "profit"]
    negative = ["miss", "drop", "fall", "downgrade", "probe", "lawsuit", "weak", "bearish", "loss"]
    score = sum(word in lower for word in positive) - sum(word in lower for word in negative)
    return "긍정" if score > 0 else "부정" if score < 0 else "중립"


def rule_importance(text: str) -> str:
    lower = text.lower()
    words = ["earnings", "sec", "guidance", "fomc", "inflation", "merger", "acquisition", "lawsuit"]
    return "높음" if any(word in lower for word in words) else "보통"


def extract_tickers(text: str, fallback: str) -> str:
    found = [token.strip(".,:;()[]") for token in text.split() if token.isupper() and 1 <= len(token) <= 5]
    clean = [token for token in found if token.isalpha()]
    return ", ".join(dict.fromkeys(clean[:5])) or fallback


def translate_or_mark(text: str) -> str:
    if not text:
        return STATUS_NONE
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return "번역 API 필요: Gemini API 키가 없어서 원문 요약만 표시합니다."
    prompt = f"다음 미국 금융 뉴스를 한국어로 2문장 이하로 번역/요약해줘:\n{text[:3000]}"
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        res = requests.post(f"{url}?key={api_key}", json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=12)
        res.raise_for_status()
        return res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception:
        return "번역 실패: 원문을 확인하세요."


def password_hash(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or uuid.uuid4().hex
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return salt, digest


def verify_password(password: str, salt: str, digest: str) -> bool:
    _, candidate = password_hash(password, salt)
    return hmac.compare_digest(candidate, digest)


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


def auth_panel() -> dict[str, Any] | None:
    users_path = APP_DIR / "users.json"
    users = load_json(users_path, {})
    if "user" not in st.session_state:
        st.session_state.user = None
    with st.expander("로그인 / 개인 설정 저장", expanded=st.session_state.user is None):
        cols = st.columns([1, 1, 1, 1])
        username = cols[0].text_input("사용자 ID", value="local_user")
        password = cols[1].text_input("비밀번호", type="password")
        action = cols[2].selectbox("작업", ["로그인", "계정 생성"])
        submitted = cols[3].button("실행", use_container_width=True)
        st.caption("로컬 데모 인증입니다. 운영 배포에서는 OIDC/Auth.js/Supabase Auth 같은 검증된 인증 계층을 붙이세요.")
        if submitted:
            if not username or not password:
                st.warning("사용자 ID와 비밀번호를 입력하세요.")
            elif action == "계정 생성":
                if username in users:
                    st.error("이미 존재하는 사용자입니다.")
                else:
                    salt, digest = password_hash(password)
                    users[username] = {"salt": salt, "digest": digest, "created_at": datetime.now().isoformat(timespec="seconds")}
                    save_json(users_path, users)
                    ensure_user_file(username)
                    st.session_state.user = username
                    st.success("계정을 만들고 로그인했습니다.")
            else:
                record = users.get(username)
                if record and verify_password(password, record["salt"], record["digest"]):
                    st.session_state.user = username
                    st.success("로그인했습니다.")
                else:
                    st.error("로그인 실패")
    if st.session_state.user:
        return load_json(ensure_user_file(st.session_state.user), {})
    return None


def persist_user(data: dict[str, Any]) -> None:
    username = st.session_state.get("user")
    if username:
        save_json(ensure_user_file(username), data)


def topbar() -> None:
    user_label = st.session_state.get("user") or "GUEST"
    st.markdown(
        f"""
<div class="terminal-topbar">
  <div class="brand">K-FIN TERMINAL ></div>
  <div class="menu"><span>Markets</span><span>Portfolio</span><span>Research</span><span>Tools</span><span>AI</span></div>
  <div class="cmd">LLM &lt;GO&gt; &nbsp; Ask anything or enter a command</div>
  <div class="ai-pill">AI COPILOT</div>
  <div class="session"><span>NEW YORK</span><span>{datetime.now().strftime('%H:%M:%S')}</span><span class="up">Connected</span><span>{user_label}</span></div>
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
    symbols = WATCHLIST_DEFAULT + ["^GSPC", "^IXIC", "GC=F", "CL=F", "KRW=X"]
    quotes = fetch_quote_table(tuple(symbols))
    rows = []
    for _, row in quotes.iterrows():
        volume = int(row.get("volume", 0)) if pd.notna(row.get("volume", np.nan)) else STATUS_NONE
        rows.append(
            f"<tr><td>{row.get('symbol')}</td><td>{money(row.get('price'))}</td><td class='{class_for_change(row.get('change_pct'))}'>{pct(row.get('change_pct'))}</td><td>{volume}</td><td>{row.get('status')}</td><td>{row.get('source')}</td></tr>"
        )
    st.markdown("<div class='terminal-card'><h3>Market Monitor <span>US/KR/ETF/FX/Rates/Commodities</span></h3><div class='body'>", unsafe_allow_html=True)
    st.markdown("<table class='dense-table'><thead><tr><th>Ticker</th><th>Last</th><th>Chg%</th><th>Volume</th><th>Status</th><th>Source</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table></div></div>", unsafe_allow_html=True)
    st.info("무료 공개 데이터는 대개 지연/제한 데이터입니다. 실시간 전문 시세는 Polygon, IEX Cloud, Nasdaq Data Link, broker market data 권한이 필요합니다.")


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


def news_tab(symbol: str) -> list[dict[str, Any]]:
    cols = st.columns([1, 4])
    selected = cols[0].text_input("뉴스 티커", value=symbol).upper().strip() or symbol
    cols[1].markdown(f"{status_chip(STATUS_DELAYED)} <span class='status-chip'>Yahoo Finance News</span> <span class='status-chip'>Gemini 번역 선택형</span>", unsafe_allow_html=True)
    news = fetch_news(selected)
    if not news:
        st.warning(f"{selected}: {STATUS_NONE} 또는 API 제한")
        return []
    st.markdown("<div class='terminal-card'><h3>Top News <span>Original + Korean</span></h3><div class='body'>", unsafe_allow_html=True)
    for item in news:
        st.markdown(
            f"""
<div class="news-item">
  <b>{item['title']}</b>
  <p>{item['summary'] or STATUS_NONE}</p>
  <p><b>한국어</b> {item['ko']}</p>
  <div class="news-meta"><span>{item['provider']}</span><span>감성 {item['sentiment']}</span><span>중요도 {item['importance']}</span><span>관련 {item['tickers']}</span></div>
</div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div></div>", unsafe_allow_html=True)
    return news


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
        st.warning("로그인하면 사용자별 포트폴리오, 관심종목, 설정을 저장할 수 있습니다. 비로그인 상태에서는 일반 시장 데이터와 뉴스만 조회합니다.")
        return
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
    c3.metric("배당 예상", STATUS_API, "브로커/배당 API 필요")
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
    st.markdown(
        f"""
<div class="metric-grid">
<div class="mini-metric"><label>SEC Filings</label><strong>{STATUS_API}</strong><small>SEC companyfacts/submissions CIK 매핑 필요</small></div>
<div class="mini-metric"><label>DART 공시</label><strong>{STATUS_API}</strong><small>DART_OPEN_API_KEY 필요</small></div>
<div class="mini-metric"><label>실적</label><strong>{STATUS_DELAYED}</strong><small>Yahoo Finance 일부 제공</small></div>
<div class="mini-metric"><label>옵션</label><strong>{STATUS_API}</strong><small>Polygon/Tradier/브로커 권장</small></div>
</div>
        """,
        unsafe_allow_html=True,
    )
    try:
        info = yf.Ticker(symbol).info or {}
        cols = st.columns(4)
        cols[0].metric("Market Cap", money(info.get("marketCap")))
        cols[1].metric("Forward PE", f"{info.get('forwardPE', STATUS_NONE)}")
        cols[2].metric("Dividend Yield", pct((info.get("dividendYield") or np.nan) * 100))
        cols[3].metric("Beta", f"{info.get('beta', STATUS_NONE)}")
    except Exception:
        st.warning("기본 재무 데이터 조회 실패")


def orders_tab() -> None:
    st.markdown("<div class='warning-box'>기본 모드는 Paper Trading입니다. 실제 주문은 설정에서 브로커와 LIVE 모드를 명시적으로 켠 뒤 별도 확인 절차를 거치도록 설계했습니다.</div>", unsafe_allow_html=True)
    mode = st.radio("주문 모드", ["PAPER", "LIVE 잠금"], horizontal=True)
    cols = st.columns(5)
    cols[0].text_input("Ticker", "AAPL")
    cols[1].selectbox("Side", ["Buy", "Sell"])
    cols[2].number_input("Quantity", min_value=0.0, value=1.0)
    cols[3].selectbox("Order Type", ["Market", "Limit", "Stop"])
    cols[4].number_input("Limit Price", min_value=0.0, value=0.0)
    if mode == "LIVE 잠금":
        st.error("실제 주문은 비활성화되어 있습니다. 브로커 API, 권한, 2단계 확인, 서버측 주문 감사 로그가 필요합니다.")
    elif st.button("Paper 주문 미리보기", use_container_width=True):
        st.success("Paper order preview only. 실제 주문은 전송되지 않았습니다.")
    st.table(
        pd.DataFrame(
            [
                {"broker": "Alpaca", "status": STATUS_API, "env": "ALPACA_API_KEY / ALPACA_SECRET_KEY"},
                {"broker": "Interactive Brokers", "status": STATUS_API, "env": "TWS/IB Gateway + ib_insync 권장"},
                {"broker": "한국투자증권", "status": STATUS_API, "env": "KIS_APP_KEY / KIS_APP_SECRET / account"},
            ]
        )
    )


def ai_summary(symbol: str, price_result: DataResult, news: list[dict[str, Any]], portfolio: pd.DataFrame) -> str:
    frame = price_result.frame
    if frame.empty:
        return f"{symbol}: {STATUS_NONE}. 분석할 가격 데이터가 없습니다."
    latest = frame.iloc[-1]
    change_20 = frame["Close"].pct_change(20).iloc[-1] * 100 if len(frame) > 20 else np.nan
    rsi = latest.get("RSI", np.nan)
    headline = news[0]["title"] if news else "뉴스 데이터 없음"
    holdings = portfolio[portfolio["ticker"].str.upper() == symbol.upper()] if not portfolio.empty else pd.DataFrame()
    position = "보유 없음" if holdings.empty else f"보유 {holdings['shares'].sum():,.4g}주"
    base = f"{symbol} 규칙 기반 요약: 최근 종가 {money(latest.get('Close'))}, 20거래일 수익률 {pct(change_20)}, RSI {rsi:.1f}입니다. 최근 뉴스: {headline}. 포트폴리오 상태: {position}. "
    if pd.notna(rsi) and rsi >= 70:
        return base + "RSI 기준 단기 과열 구간입니다."
    if pd.notna(rsi) and rsi <= 30:
        return base + "RSI 기준 단기 침체 구간입니다."
    return base + "기술적 모멘텀은 중립에 가깝습니다."


def ai_tab(symbol: str, price_result: DataResult, news: list[dict[str, Any]], user_data: dict[str, Any] | None) -> None:
    portfolio = portfolio_frame(user_data)
    provider = st.selectbox("AI Provider", ["rules", "gemini"], index=0)
    prompt = st.text_area("질문", value=f"{symbol}의 차트, 뉴스, 포트폴리오 관점 요약")
    if st.button("분석 실행", use_container_width=True):
        if provider == "gemini" and not os.getenv("GEMINI_API_KEY"):
            st.warning("GEMINI_API_KEY가 없어 규칙 기반 요약으로 대체합니다.")
        st.markdown(f"<div class='ok-box'>{ai_summary(symbol, price_result, news, portfolio)}</div>", unsafe_allow_html=True)
        st.caption(f"입력 질문: {prompt}")


def tools_tab(user_data: dict[str, Any] | None) -> None:
    st.subheader("사용자 설정")
    if user_data is None:
        st.info("로그인하면 설정을 저장할 수 있습니다.")
    else:
        settings = user_data.setdefault("settings", {})
        cols = st.columns(4)
        settings["default_symbol"] = cols[0].text_input("기본 종목", settings.get("default_symbol", "AAPL"))
        settings["ai_provider"] = cols[1].selectbox("AI 기본값", ["rules", "gemini"], index=0 if settings.get("ai_provider") != "gemini" else 1)
        settings["broker_mode"] = cols[2].selectbox("브로커 모드", ["paper", "live_locked"], index=0)
        settings["layout"] = cols[3].selectbox("레이아웃", ["terminal-grid", "compact"], index=0)
        if st.button("설정 저장", use_container_width=True):
            persist_user(user_data)
            st.success("설정을 저장했습니다.")
    envs = [
        ("GEMINI_API_KEY", "뉴스 번역/AI 분석"),
        ("POLYGON_API_KEY", "실시간/옵션/집계 시세"),
        ("DART_OPEN_API_KEY", "한국 DART 공시"),
        ("ALPACA_API_KEY", "Paper/Live 브로커"),
        ("ALPACA_SECRET_KEY", "Paper/Live 브로커"),
        ("KIS_APP_KEY", "한국투자증권 Open API"),
        ("KIS_APP_SECRET", "한국투자증권 Open API"),
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
  </style>
  <div class="workspace">
    <section class="panel"><h4>Market Pulse</h4><div class="grid" id="left"></div></section>
    <section class="panel"><h4>Charts / Research</h4><div class="grid" id="center"></div></section>
    <section class="panel"><h4>Order / AI / Risk</h4><div class="grid" id="right"></div></section>
  </div>
  <script>
    const defaults = [
      ["left","Regime","Risk-on<br><span class='green'>Liquidity abundant</span>",10,10,250,120],
      ["left","Cross Asset","SPX / US10Y / WTI / GOLD / USDKRW",10,150,250,150],
      ["center","Main Chart","Drag cards, resize boxes, and resize panel borders. Layout is saved in this browser.",10,10,430,250],
      ["center","News / Filings","SEC/DART cards show API-needed states until keys are configured.",455,10,300,250],
      ["center","Portfolio Graph","Use app Portfolio tab for large mode.",10,280,360,180],
      ["right","Paper Order","Mode: <span class='yellow'>PAPER</span><br>Live trading locked by design.",10,10,260,140],
      ["right","AI Assistant","Rules fallback works without API.<br>Gemini is optional.",10,170,260,130],
      ["right","Risk","Max weight, sector, currency and country concentration.",10,320,260,150]
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
    const note = document.createElement("div"); note.className="hint"; note.textContent="레이아웃 저장: browser localStorage. 로그인 사용자 서버 저장은 문서의 백엔드 어댑터로 확장.";
    document.body.appendChild(note);
  </script>
</div>
        """,
        height=720,
    )


def main() -> None:
    init_page()
    user_data = auth_panel()
    topbar()
    tabs = st.tabs(["시장", "모니터", "차트", "뉴스", "포트폴리오", "리서치/공시", "옵션", "주문", "AI", "설정", "레이아웃"])
    symbol = (user_data or {}).get("settings", {}).get("default_symbol", "AAPL")
    price_result = fetch_price_history(symbol, "1y", "1d")
    news: list[dict[str, Any]] = []
    with tabs[0]:
        market_tab()
    with tabs[1]:
        layout_tab()
    with tabs[2]:
        symbol, price_result = charts_tab(user_data)
    with tabs[3]:
        news = news_tab(symbol)
    with tabs[4]:
        portfolio_tab(user_data)
    with tabs[5]:
        research_tab(symbol)
    with tabs[6]:
        st.warning("옵션 체인/옵션 플로우는 실시간성 및 라이선스 제한 때문에 Polygon, Tradier, Cboe DataShop 또는 브로커 API 키가 필요합니다.")
        try:
            expirations = yf.Ticker(symbol).options
            if expirations:
                st.write(f"{symbol} 만기: {', '.join(expirations[:8])}")
                chain = yf.Ticker(symbol).option_chain(expirations[0])
                st.dataframe(chain.calls.head(20), use_container_width=True)
            else:
                st.info(f"{symbol}: {STATUS_NONE}")
        except Exception:
            st.info(f"{symbol}: {STATUS_API} 또는 데이터 제한")
    with tabs[7]:
        orders_tab()
    with tabs[8]:
        ai_tab(symbol, price_result, news, user_data)
    with tabs[9]:
        tools_tab(user_data)
    with tabs[10]:
        layout_tab()


if __name__ == "__main__":
    main()
