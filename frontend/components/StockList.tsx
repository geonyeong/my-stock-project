"use client";

import Link from "next/link";

import StatusMessage from "@/components/StatusMessage";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { calendarDaysUntil } from "@/lib/calendar";
import { formatDate } from "@/lib/format";
import type { EarningsEvent } from "@/lib/types";

const SOON_DAYS = 14;

function nearestUpcoming(events: EarningsEvent[] | null): Map<string, EarningsEvent> {
  const nearest = new Map<string, EarningsEvent>();
  for (const event of events ?? []) {
    if (!nearest.has(event.symbol)) nearest.set(event.symbol, event);
  }
  return nearest;
}

function EarningsHint({ event }: { event: EarningsEvent }) {
  const days = calendarDaysUntil(event.time);
  const soon = days <= SOON_DAYS;
  const when = days === 0 ? "오늘" : `${days}일 후`;
  return (
    <p className={`mt-3 text-xs ${soon ? "font-medium text-amber-700 dark:text-amber-400" : "text-zinc-500"}`}>
      다음 실적 {formatDate(event.time)}
      {soon && ` · ${when}`}
    </p>
  );
}

export default function StockList() {
  const { data, error, loading } = useApi((signal) => api.stocks(signal), "stocks");
  const upcoming = useApi((signal) => api.upcomingEarnings(signal), "earnings:upcoming");
  const nextBySymbol = nearestUpcoming(upcoming.data);

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
      {data.map((stock) => {
        const next = nextBySymbol.get(stock.symbol);
        return (
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
              {next && <EarningsHint event={next} />}
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
