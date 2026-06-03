"use client";

import type { CSSProperties, ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";

type QuoteStatus = "지연 데이터" | "데이터 없음";
type QuoteRow = {
  symbol: string;
  price: number | null;
  changePct: number | null;
  volume: number | null;
  status: QuoteStatus;
  source: string;
  message?: string;
};
type HistoryRow = {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
};
type Holding = {
  ticker: string;
  shares: number;
  cost: number;
  sector: string;
  country: string;
  currency: string;
};

const marketSymbols = ["^GSPC", "^IXIC", "^DJI", "^VIX", "^TNX", "CL=F", "GC=F", "KRW=X", "BTC-USD"];
const watchSymbols = ["AAPL", "MSFT", "NVDA", "TSLA", "SPY", "QQQ", "005930.KS"];
const symbolLabels: Record<string, string> = {
  "^GSPC": "SPX",
  "^IXIC": "NDX",
  "^DJI": "DJI",
  "^VIX": "VIX",
  "^TNX": "US10Y",
  "CL=F": "WTI",
  "GC=F": "GOLD",
  "KRW=X": "USD/KRW",
  "BTC-USD": "BTC",
  "005930.KS": "Samsung"
};
const nav = ["Markets", "Charts", "News", "Portfolio", "Research", "AI", "Settings"];
const ranges = ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y"];
const intervals = ["1d", "1wk", "1mo"];

function fmtMoney(value: number | null | undefined, prefix = "$") {
  if (value == null || Number.isNaN(value)) return "데이터 없음";
  return `${prefix}${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function fmtNumber(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return "데이터 없음";
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function fmtPct(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return "데이터 없음";
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function tone(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return "flat";
  return value > 0 ? "up" : value < 0 ? "down" : "flat";
}

function statusClass(status: string) {
  if (status === "지연 데이터") return "delay";
  if (status === "API 필요") return "api";
  if (status === "실제 데이터") return "real";
  return "none";
}

function movingAverage(values: number[], window: number) {
  return values.map((_, index) => {
    if (index + 1 < window) return null;
    const slice = values.slice(index + 1 - window, index + 1);
    return slice.reduce((sum, value) => sum + value, 0) / window;
  });
}

function pathFrom(values: Array<number | null>, width: number, height: number) {
  const clean = values.filter((value): value is number => value != null && !Number.isNaN(value));
  if (clean.length < 2) return "";
  const min = Math.min(...clean);
  const max = Math.max(...clean);
  const spread = max - min || 1;
  const points = values
    .map((value, index) => {
      if (value == null || Number.isNaN(value)) return null;
      const x = (index / Math.max(values.length - 1, 1)) * width;
      const y = height - ((value - min) / spread) * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .filter(Boolean);
  return points.length ? `M ${points.join(" L ")}` : "";
}

function useQuotes() {
  const [rows, setRows] = useState<QuoteRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    const symbols = Array.from(new Set([...marketSymbols, ...watchSymbols])).join(",");
    setLoading(true);
    fetch(`/api/quotes?symbols=${encodeURIComponent(symbols)}`, { signal: controller.signal })
      .then((response) => response.json())
      .then((data) => {
        setRows(data.rows || []);
        setError("");
      })
      .catch((err) => {
        if (err.name !== "AbortError") setError("시장 데이터 응답 지연 또는 제한");
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, []);
  const map = useMemo(() => new Map(rows.map((row) => [row.symbol, row])), [rows]);
  return { rows, map, loading, error };
}

function StatusPill({ status }: { status: string }) {
  return <span className={`status ${statusClass(status)}`}>{status}</span>;
}

function QuoteStrip({ quotes }: { quotes: Map<string, QuoteRow> }) {
  return (
    <div className="quote-strip">
      {marketSymbols.map((symbol) => {
        const row = quotes.get(symbol);
        return (
          <div className="quote-cell" key={symbol}>
            <b>{symbolLabels[symbol] || symbol}</b>
            <strong>{fmtNumber(row?.price)}</strong>
            <span className={tone(row?.changePct)}>{fmtPct(row?.changePct)} · {row?.status || "데이터 없음"}</span>
          </div>
        );
      })}
    </div>
  );
}

function TerminalCard({
  id,
  title,
  meta,
  children,
  onDragStart,
  onDrop
}: {
  id: string;
  title: string;
  meta?: React.ReactNode;
  children: ReactNode;
  onDragStart?: (id: string) => void;
  onDrop?: (id: string) => void;
}) {
  return (
    <section
      className="panel"
      draggable
      onDragStart={() => onDragStart?.(id)}
      onDragOver={(event) => event.preventDefault()}
      onDrop={() => onDrop?.(id)}
    >
      <header>
        <span>{title}</span>
        <span className="panel-meta">{meta || "::"}</span>
      </header>
      <div className="panel-body">{children}</div>
    </section>
  );
}

function MarketHome({ quotes, loading }: { quotes: Map<string, QuoteRow>; loading: boolean }) {
  const [order, setOrder] = useState(["regime", "chart", "heat", "momentum", "coverage", "ai", "portfolio"]);
  const [dragging, setDragging] = useState<string | null>(null);
  const spx = quotes.get("^GSPC");
  const vix = quotes.get("^VIX");
  const regime =
    spx?.changePct == null || vix?.price == null
      ? "데이터 없음"
      : spx.changePct >= 0 && vix.price < 20
        ? "RISK-ON"
        : vix.price >= 25
          ? "RISK-OFF"
          : "NEUTRAL";
  const meter = regime === "RISK-ON" ? 78 : regime === "RISK-OFF" ? 34 : regime === "NEUTRAL" ? 55 : 16;
  const moveCard = (target: string) => {
    if (!dragging || dragging === target) return;
    setOrder((current) => {
      const next = current.filter((id) => id !== dragging);
      next.splice(next.indexOf(target), 0, dragging);
      return next;
    });
    setDragging(null);
  };
  const cards: Record<string, React.ReactNode> = {
    regime: (
      <TerminalCard id="regime" title="Market Regime" meta={<StatusPill status={spx?.status || "데이터 없음"} />} onDragStart={setDragging} onDrop={moveCard}>
        <div className="regime">
          <div className="donut" style={{ "--meter": `${meter}%` } as CSSProperties}><span>{regime}</span></div>
          <div className="rows">
            <Row label="SPX" value={fmtPct(spx?.changePct)} tone={tone(spx?.changePct)} />
            <Row label="VIX" value={fmtNumber(vix?.price)} />
            <p className="muted">{loading ? "초기 시장 데이터를 불러오는 중" : "실패한 응답은 숫자로 대체하지 않습니다."}</p>
          </div>
        </div>
      </TerminalCard>
    ),
    chart: (
      <TerminalCard id="chart" title="Cross-Asset Monitor" meta={<span className="status api">Realtime API optional</span>} onDragStart={setDragging} onDrop={moveCard}>
        <div className="chart-board">
          <div className="board-grid" />
          <p>차트 탭에서 선택한 기간과 인터벌로 실제 히스토리 데이터를 로드합니다.</p>
          <div className="legend-grid">
            <Mini label="SPX" value={fmtNumber(spx?.price)} />
            <Mini label="NDX" value={fmtNumber(quotes.get("^IXIC")?.price)} />
            <Mini label="US10Y" value={fmtNumber(quotes.get("^TNX")?.price)} />
            <Mini label="USD/KRW" value={fmtNumber(quotes.get("KRW=X")?.price)} />
          </div>
        </div>
      </TerminalCard>
    ),
    heat: (
      <TerminalCard id="heat" title="Asset Heatmap" meta="Change %" onDragStart={setDragging} onDrop={moveCard}>
        <div className="heat">
          {[...marketSymbols, "AAPL", "NVDA", "SPY", "QQQ"].map((symbol) => {
            const row = quotes.get(symbol);
            return (
              <div className="heat-cell" key={symbol}>
                <b>{symbolLabels[symbol] || symbol}</b>
                <span className={tone(row?.changePct)}>{fmtPct(row?.changePct)}</span>
              </div>
            );
          })}
        </div>
      </TerminalCard>
    ),
    momentum: (
      <TerminalCard id="momentum" title="Momentum Board" meta="Watchlist" onDragStart={setDragging} onDrop={moveCard}>
        {watchSymbols.map((symbol) => <Bar key={symbol} symbol={symbolLabels[symbol] || symbol} value={quotes.get(symbol)?.changePct} />)}
      </TerminalCard>
    ),
    coverage: (
      <TerminalCard id="coverage" title="Data Coverage" meta={<StatusPill status="API 필요" />} onDragStart={setDragging} onDrop={moveCard}>
        <Row label="US/KR Quotes" value="지연 데이터" />
        <Row label="SEC Filings" value="API 필요" />
        <Row label="DART Filings" value="API 필요" />
        <Row label="Macro/FX/Commodities" value="지연 데이터" />
        <Row label="ETF/Dividend" value="API 필요" />
      </TerminalCard>
    ),
    ai: (
      <TerminalCard id="ai" title="AI Assistant" meta="KR" onDragStart={setDragging} onDrop={moveCard}>
        <Row label="Fallback" value="Rules" />
        <Row label="Gemini" value="API 필요" />
        <p className="muted">뉴스, 공시, 차트, 포트폴리오 기반 한국어 요약 구조.</p>
      </TerminalCard>
    ),
    portfolio: (
      <TerminalCard id="portfolio" title="Portfolio Risk" meta="Local" onDragStart={setDragging} onDrop={moveCard}>
        <Row label="Holdings" value="내 로컬 저장" />
        <Row label="Sector/Country" value="지원" />
        <Row label="External Sync" value="사용 안 함" />
      </TerminalCard>
    )
  };
  return <div className="terminal-layout">{order.map((id) => <div key={id}>{cards[id]}</div>)}</div>;
}

function Row({ label, value, tone: valueTone }: { label: string; value: string; tone?: string }) {
  return (
    <div className="term-row">
      <span>{label}</span>
      <strong className={valueTone}>{value}</strong>
    </div>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="mini">
      <span>{label}</span>
      <b>{value}</b>
    </div>
  );
}

function Bar({ symbol, value }: { symbol: string; value: number | null | undefined }) {
  const width = value == null || Number.isNaN(value) ? 0 : Math.max(8, Math.min(100, Math.abs(value) * 18));
  return (
    <div className="bar-row">
      <span>{symbol}</span>
      <div className="bar-track"><div className={`bar-fill ${tone(value)}`} style={{ width: `${width}%` }} /></div>
      <strong className={tone(value)}>{fmtPct(value)}</strong>
    </div>
  );
}

function ChartTab() {
  const [symbol, setSymbol] = useState("AAPL");
  const [range, setRange] = useState("1y");
  const [interval, setInterval] = useState("1d");
  const [rows, setRows] = useState<HistoryRow[]>([]);
  const [status, setStatus] = useState("데이터 없음");
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    fetch(`/api/history?symbol=${encodeURIComponent(symbol)}&range=${range}&interval=${interval}`, { signal: controller.signal })
      .then((response) => response.json())
      .then((data) => {
        setRows(data.rows || []);
        setStatus(data.status || "데이터 없음");
      })
      .catch(() => {
        setRows([]);
        setStatus("데이터 없음");
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [symbol, range, interval]);

  const closes = rows.map((row) => row.close).filter((value): value is number => value != null);
  const ma20 = movingAverage(closes, 20);
  const latest = closes.at(-1) ?? null;
  const maLatest = ma20.at(-1) ?? null;
  return (
    <div className="screen">
      <div className="toolbar">
        <input value={symbol} onChange={(event) => setSymbol(event.target.value.toUpperCase())} />
        <Segment values={ranges} value={range} onChange={setRange} />
        <Segment values={intervals} value={interval} onChange={setInterval} />
        <StatusPill status={loading ? "지연 데이터" : status} />
      </div>
      <section className="panel tall">
        <header><span>{symbol} Chart</span><span className="panel-meta">Candle-ready history</span></header>
        <div className="chart-svg-wrap">
          {rows.length ? (
            <svg viewBox="0 0 920 360" className="chart-svg" role="img">
              <path d={pathFrom(closes, 920, 260)} className="price-line" />
              <path d={pathFrom(ma20, 920, 260)} className="ma-line" />
              <g transform="translate(0 290)">
                {rows.slice(-80).map((row, index) => {
                  const maxVolume = Math.max(...rows.map((item) => item.volume || 0), 1);
                  const height = ((row.volume || 0) / maxVolume) * 62;
                  return <rect key={row.date} x={index * 11.5} y={70 - height} width="7" height={height} className="volume-bar" />;
                })}
              </g>
            </svg>
          ) : (
            <div className="empty">데이터 없음. API 제한 또는 티커 미지원입니다.</div>
          )}
        </div>
      </section>
      <div className="summary-grid">
        <Mini label="Last" value={fmtMoney(latest)} />
        <Mini label="MA20" value={fmtMoney(maLatest)} />
        <Mini label="RSI" value="계산 예정" />
        <Mini label="MACD" value="계산 예정" />
      </div>
    </div>
  );
}

function Segment({ values, value, onChange }: { values: string[]; value: string; onChange: (value: string) => void }) {
  return (
    <div className="segment">
      {values.map((item) => (
        <button key={item} className={item === value ? "active" : ""} onClick={() => onChange(item)}>{item}</button>
      ))}
    </div>
  );
}

function PortfolioTab({ quotes }: { quotes: Map<string, QuoteRow> }) {
  const [holdings, setHoldings] = useState<Holding[]>([
    { ticker: "AAPL", shares: 3, cost: 165, sector: "Technology", country: "US", currency: "USD" },
    { ticker: "SPY", shares: 1, cost: 480, sector: "ETF", country: "US", currency: "USD" }
  ]);
  useEffect(() => {
    const saved = localStorage.getItem("kfin-next-portfolio");
    if (saved) setHoldings(JSON.parse(saved));
  }, []);
  const save = () => localStorage.setItem("kfin-next-portfolio", JSON.stringify(holdings));
  const enriched = holdings.map((holding) => {
    const quote = quotes.get(holding.ticker);
    const value = quote?.price == null ? null : quote.price * holding.shares;
    const costValue = holding.cost * holding.shares;
    return { ...holding, value, pnl: value == null ? null : value - costValue };
  });
  const total = enriched.reduce((sum, item) => sum + (item.value || 0), 0);
  return (
    <div className="screen">
      <div className="summary-grid">
        <Mini label="Total" value={total ? fmtMoney(total) : "데이터 없음"} />
        <Mini label="Dividend" value="API 필요" />
        <Mini label="Data Sync" value="수동/로컬" />
        <Mini label="Rebalance" value="확인 가능" />
      </div>
      <section className="panel">
        <header><span>Manual Portfolio</span><button onClick={save}>저장</button></header>
        <div className="table-wrap">
          <table>
            <thead><tr><th>Ticker</th><th>Shares</th><th>Cost</th><th>Value</th><th>P/L</th><th>Sector</th></tr></thead>
            <tbody>
              {enriched.map((row, index) => (
                <tr key={`${row.ticker}-${index}`}>
                  <td><input value={row.ticker} onChange={(event) => setHoldings((items) => items.map((item, i) => i === index ? { ...item, ticker: event.target.value.toUpperCase() } : item))} /></td>
                  <td><input type="number" value={row.shares} onChange={(event) => setHoldings((items) => items.map((item, i) => i === index ? { ...item, shares: Number(event.target.value) } : item))} /></td>
                  <td><input type="number" value={row.cost} onChange={(event) => setHoldings((items) => items.map((item, i) => i === index ? { ...item, cost: Number(event.target.value) } : item))} /></td>
                  <td>{row.value == null ? "데이터 없음" : fmtMoney(row.value)}</td>
                  <td className={tone(row.pnl)}>{row.pnl == null ? "데이터 없음" : fmtMoney(row.pnl)}</td>
                  <td>{row.sector}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function InfoTab({ type }: { type: string }) {
  const rows = {
    News: [["US News", "API 필요 또는 provider 연결"], ["Korean Translation", "Gemini 선택 연결"], ["Sentiment", "규칙 기반 가능"], ["Related Tickers", "제목/본문 추출"]],
    Research: [["SEC", "SEC_USER_AGENT / CIK 매핑 필요"], ["DART", "DART_OPEN_API_KEY 필요"], ["Earnings", "provider API 필요"], ["ETF Holdings", "issuer/provider API 필요"]],
    AI: [["Fallback", "Rules"], ["Gemini", "GEMINI_API_KEY 필요"], ["Inputs", "뉴스/공시/차트/포트폴리오"], ["Language", "Korean"]],
    Settings: [["Mode", "Single-user custom"], ["Secrets", "Vercel env / Secret Manager"], ["Layout", "localStorage"], ["Security", "HTTPS required"]]
  }[type] || [];
  return (
    <section className="panel">
      <header><span>{type}</span><span className="panel-meta">No fake data policy</span></header>
      <div className="table-wrap">
        <table>
          <tbody>{rows.map(([key, value]) => <tr key={key}><td>{key}</td><td>{value}</td></tr>)}</tbody>
        </table>
      </div>
    </section>
  );
}

export default function Page() {
  const [active, setActive] = useState("Markets");
  const { map, loading, error } = useQuotes();
  return (
    <main>
      <div className="topbar">
        <div className="brand">K-FIN TERMINAL</div>
        <nav>{["Markets", "Portfolio", "Research", "Tools", "AI"].map((item) => <span key={item}>{item}</span>)}</nav>
        <div className="command">LLM &lt;GO&gt; Ask anything or enter a command</div>
        <button className="copilot">AI COPILOT</button>
        <div className="session">NEW YORK · Connected</div>
      </div>
      <QuoteStrip quotes={map} />
      <div className="nav-tabs">{nav.map((item) => <button key={item} className={active === item ? "active" : ""} onClick={() => setActive(item)}>{item}</button>)}</div>
      {error ? <div className="notice">{error}</div> : null}
      {active === "Markets" && <MarketHome quotes={map} loading={loading} />}
      {active === "Charts" && <ChartTab />}
      {active === "Portfolio" && <PortfolioTab quotes={map} />}
      {!["Markets", "Charts", "Portfolio"].includes(active) && <InfoTab type={active} />}
    </main>
  );
}
