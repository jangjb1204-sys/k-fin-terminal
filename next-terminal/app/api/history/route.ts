import { NextRequest, NextResponse } from "next/server";

const ALLOWED_RANGES = new Set(["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y"]);
const ALLOWED_INTERVALS = new Set(["1d", "1wk", "1mo"]);

export async function GET(request: NextRequest) {
  const symbol = (request.nextUrl.searchParams.get("symbol") || "AAPL").trim().toUpperCase();
  const range = request.nextUrl.searchParams.get("range") || "1y";
  const interval = request.nextUrl.searchParams.get("interval") || "1d";

  if (!ALLOWED_RANGES.has(range) || !ALLOWED_INTERVALS.has(interval)) {
    return NextResponse.json({ status: "데이터 없음", message: "Invalid range or interval", rows: [] }, { status: 400 });
  }

  try {
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?range=${range}&interval=${interval}`;
    const response = await fetch(url, {
      next: { revalidate: 180 },
      headers: { "User-Agent": "k-fin-terminal/0.1" }
    });
    if (!response.ok) {
      return NextResponse.json({ symbol, status: "데이터 없음", message: `HTTP ${response.status}`, rows: [] });
    }
    const data = await response.json();
    const result = data?.chart?.result?.[0];
    const quote = result?.indicators?.quote?.[0];
    const timestamps: number[] = result?.timestamp || [];
    if (!result || !quote || timestamps.length === 0) {
      return NextResponse.json({ symbol, status: "데이터 없음", rows: [] });
    }
    const rows = timestamps
      .map((time, index) => ({
        date: new Date(time * 1000).toISOString(),
        open: quote.open?.[index] ?? null,
        high: quote.high?.[index] ?? null,
        low: quote.low?.[index] ?? null,
        close: quote.close?.[index] ?? null,
        volume: quote.volume?.[index] ?? null
      }))
      .filter((row) => row.close != null);
    return NextResponse.json({ symbol, range, interval, status: rows.length ? "지연 데이터" : "데이터 없음", source: "Yahoo Finance chart API", rows });
  } catch (error) {
    return NextResponse.json({
      symbol,
      status: "데이터 없음",
      message: error instanceof Error ? error.message : "Unknown error",
      rows: []
    });
  }
}
