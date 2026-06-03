import { NextRequest, NextResponse } from "next/server";

type QuoteRow = {
  symbol: string;
  price: number | null;
  changePct: number | null;
  volume: number | null;
  status: "지연 데이터" | "데이터 없음";
  source: string;
  message?: string;
};

const SOURCE = "Yahoo Finance chart API";

async function fetchQuote(symbol: string): Promise<QuoteRow> {
  const base: QuoteRow = {
    symbol,
    price: null,
    changePct: null,
    volume: null,
    status: "데이터 없음",
    source: SOURCE
  };
  try {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?range=5d&interval=1d`;
    const response = await fetch(url, {
      next: { revalidate: 45 },
      headers: { "User-Agent": "k-fin-terminal/0.1" }
    });
    if (!response.ok) {
      return { ...base, message: `HTTP ${response.status}` };
    }
    const data = await response.json();
    const result = data?.chart?.result?.[0];
    const quote = result?.indicators?.quote?.[0];
    const closes = (quote?.close || []).filter((value: number | null) => value != null);
    const volumes = (quote?.volume || []).filter((value: number | null) => value != null);
    if (!result || closes.length === 0) {
      return base;
    }
    const last = closes[closes.length - 1];
    const previous = closes.length > 1 ? closes[closes.length - 2] : null;
    return {
      ...base,
      price: Number(last),
      changePct: previous ? ((Number(last) / Number(previous)) - 1) * 100 : null,
      volume: volumes.length ? Number(volumes[volumes.length - 1]) : null,
      status: "지연 데이터"
    };
  } catch (error) {
    return { ...base, message: error instanceof Error ? error.message : "Unknown error" };
  }
}

export async function GET(request: NextRequest) {
  const symbols = (request.nextUrl.searchParams.get("symbols") || "")
    .split(",")
    .map((symbol) => symbol.trim())
    .filter(Boolean)
    .slice(0, 24);

  if (symbols.length === 0) {
    return NextResponse.json({ rows: [] });
  }

  const rows = await Promise.all(symbols.map(fetchQuote));
  return NextResponse.json({ rows, generatedAt: new Date().toISOString() });
}
