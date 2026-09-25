"use client";

import Link from "next/link";

import StatusMessage from "@/components/StatusMessage";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";

export default function StockList() {
  const { data, error, loading } = useApi((signal) => api.stocks(signal), "stocks");

  if (loading || error || !data?.length) {
    return (
      <StatusMessage
        loading={loading}
        error={error}
        empty={!data?.length}
        emptyText="등록된 종목이 없습니다. 백엔드에서 scripts.seed_stocks 를 실행하세요."
      />
    );
  }

  return (
    <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {data.map((stock) => (
        <li key={stock.symbol}>
          <Link
            href={`/stocks/${encodeURIComponent(stock.symbol)}`}
            className="block rounded-xl border border-zinc-200 p-4 transition hover:border-zinc-400 hover:shadow-sm dark:border-zinc-800 dark:hover:border-zinc-600"
          >
            <div className="flex items-baseline justify-between gap-2">
              <span className="font-semibold">{stock.name}</span>
              <span className="font-mono text-xs text-zinc-500">{stock.symbol}</span>
            </div>
            <div className="mt-2 flex gap-2 text-xs text-zinc-500">
              <span className="rounded bg-zinc-100 px-1.5 py-0.5 dark:bg-zinc-800">{stock.market}</span>
              {stock.sector && <span className="rounded bg-zinc-100 px-1.5 py-0.5 dark:bg-zinc-800">{stock.sector}</span>}
            </div>
          </Link>
        </li>
      ))}
    </ul>
  );
}
