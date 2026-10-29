"use client";

import StatusMessage from "@/components/StatusMessage";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { calendarDaysUntil, earningsInHorizon, seoulDay } from "@/lib/calendar";
import { formatDate, formatPrice, formatSurprise } from "@/lib/format";
import type { EarningsEvent } from "@/lib/types";

function whenLabel(eventTime: string): string {
  const days = calendarDaysUntil(eventTime);
  if (days <= 0) return "오늘";
  if (days === 1) return "내일";
  return `${days}일 후`;
}

function NextEvent({ event, inHorizon }: { event: EarningsEvent; inHorizon: boolean }) {
  return (
    <div>
      <p className="text-sm text-zinc-500">다음 실적 발표</p>
      <p className="mt-1 text-lg font-semibold">
        {formatDate(event.time)}{" "}
        <span className="text-sm font-medium text-amber-700 dark:text-amber-400">{whenLabel(event.time)}</span>
      </p>
      {event.eps_estimate !== null && (
        <p className="text-sm text-zinc-600 dark:text-zinc-400">시장 예상 EPS {formatPrice(event.eps_estimate)}</p>
      )}
      {inHorizon && (
        <p className="mt-2 text-sm text-amber-700 dark:text-amber-400">
          최근 일봉 기준 5거래일 전망 구간에 이 발표가 포함됩니다.
        </p>
      )}
    </div>
  );
}

function PastEvents({ events }: { events: EarningsEvent[] }) {
  return (
    <div>
      <p className="mb-2 text-sm text-zinc-500">최근 발표</p>
      <ul className="flex flex-col gap-2 text-sm">
        {events.map((event) => (
          <li key={event.time} className="flex flex-wrap gap-x-4 gap-y-1">
            <span>{formatDate(event.time)}</span>
            <span className="text-zinc-600 dark:text-zinc-400">예상 {formatPrice(event.eps_estimate)}</span>
            <span className="text-zinc-600 dark:text-zinc-400">발표 {formatPrice(event.eps_reported)}</span>
            <span className="text-zinc-600 dark:text-zinc-400">예상 대비 {formatSurprise(event.surprise_pct)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Schedule({ symbol, baseTime }: { symbol: string; baseTime?: string }) {
  const { data, error, loading } = useApi((signal) => api.earnings(symbol, signal), `earnings:${symbol}`);
  if (loading || error || !data?.length) {
    return (
      <StatusMessage
        loading={loading}
        error={error}
        empty={!data?.length}
        emptyText="수집된 실적 일정이 없습니다. collectors.earnings.run 을 실행하세요."
      />
    );
  }

  const today = seoulDay(new Date());
  const upcoming = data
    .filter((event) => seoulDay(event.time) >= today)
    .sort((a, b) => a.time.localeCompare(b.time));
  const past = data.filter((event) => seoulDay(event.time) < today).slice(0, 4);
  const next = upcoming[0];
  const inHorizon = next !== undefined && baseTime !== undefined && earningsInHorizon(baseTime, next.time);

  return (
    <div className="flex flex-col gap-4">
      {next ? <NextEvent event={next} inHorizon={inHorizon} /> : <p className="text-sm text-zinc-500">예정된 실적 발표가 없습니다.</p>}
      {past.length > 0 && <PastEvents events={past} />}
      <p className="text-xs text-zinc-500">
        일정과 수치는 참고용이며 투자 권유가 아닙니다. 모델은 발표 수치가 아니라, 5거래일 전망 구간에 일정이 있는지만 사용합니다.
      </p>
    </div>
  );
}

export default function EarningsPanel({
  symbol,
  isEtf,
  baseTime,
}: {
  symbol: string;
  isEtf: boolean;
  baseTime?: string;
}) {
  if (isEtf) return <p className="text-sm text-zinc-500">ETF는 개별 실적 발표가 없습니다.</p>;
  return <Schedule symbol={symbol} baseTime={baseTime} />;
}
