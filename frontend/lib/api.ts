import type { ApiResponse, Candle, NewsItem, Prediction, Stock } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {}

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, { signal, cache: "no-store" });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("API 서버에 연결할 수 없습니다.");
  }

  const body = (await res.json().catch(() => null)) as ApiResponse<T> | null;
  if (!body || !body.success || body.data === null) {
    throw new ApiError(body?.error ?? "데이터를 불러오지 못했습니다.");
  }
  return body.data;
}

export const api = {
  stocks: (signal?: AbortSignal) => request<Stock[]>("/stocks", signal),
  stock: (symbol: string, signal?: AbortSignal) =>
    request<Stock>(`/stocks/${encodeURIComponent(symbol)}`, signal),
  candles: (symbol: string, limit = 120, signal?: AbortSignal) =>
    request<Candle[]>(`/stocks/${encodeURIComponent(symbol)}/candles?limit=${limit}`, signal),
  news: (symbol: string, limit = 30, signal?: AbortSignal) =>
    request<NewsItem[]>(`/news?symbol=${encodeURIComponent(symbol)}&limit=${limit}`, signal),
  predictions: (symbol: string, signal?: AbortSignal) =>
    request<Prediction[]>(`/predictions/${encodeURIComponent(symbol)}`, signal),
};
