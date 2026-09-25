"use client";

import StatusMessage from "@/components/StatusMessage";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { NewsItem, SentimentLabel } from "@/lib/types";

const LABEL_TEXT: Record<SentimentLabel, string> = {
  positive: "긍정",
  negative: "부정",
  neutral: "중립",
};

const LABEL_STYLE: Record<SentimentLabel, string> = {
  positive: "bg-red-50 text-red-600 dark:bg-red-950 dark:text-red-400",
  negative: "bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400",
  neutral: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
};

function safeHref(url: string | null): string | null {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    return parsed.protocol === "https:" || parsed.protocol === "http:" ? parsed.href : null;
  } catch {
    return null;
  }
}

function averageScore(items: NewsItem[]): number {
  return items.reduce((sum, n) => sum + Number(n.sentiment_score), 0) / items.length;
}

export default function NewsList({ symbol }: { symbol: string }) {
  const { data, error, loading } = useApi((signal) => api.news(symbol, 30, signal), `news:${symbol}`);

  if (loading || error || !data?.length) {
    return (
      <StatusMessage
        loading={loading}
        error={error}
        empty={!data?.length}
        emptyText="수집된 뉴스가 없습니다. collectors.news.run 을 실행하세요."
      />
    );
  }

  const avg = averageScore(data);

  return (
    <div>
      <p className="mb-3 text-sm text-zinc-500">
        최근 {data.length}건 평균 감성 점수{" "}
        <span className={avg > 0 ? "text-red-500" : avg < 0 ? "text-blue-500" : ""}>{avg.toFixed(2)}</span>
        <span className="ml-1 text-xs">(-1 부정 ~ 1 긍정)</span>
      </p>
      <ul className="divide-y divide-zinc-100 dark:divide-zinc-900">
        {data.map((n) => {
          const href = safeHref(n.url);
          return (
            <li key={`${n.time}-${n.url}`} className="flex items-start gap-3 py-2.5">
              <span className={`mt-0.5 shrink-0 rounded px-1.5 py-0.5 text-xs ${LABEL_STYLE[n.sentiment_label]}`}>
                {LABEL_TEXT[n.sentiment_label]}
              </span>
              <div className="min-w-0">
                {href ? (
                  <a href={href} target="_blank" rel="noopener noreferrer" className="hover:underline">
                    {n.title}
                  </a>
                ) : (
                  <span>{n.title}</span>
                )}
                <p className="mt-0.5 text-xs text-zinc-500">
                  {n.source} · {formatDate(n.time)} · 점수 {Number(n.sentiment_score).toFixed(2)}
                  {n.impact_score !== null && ` · 영향도 ${Number(n.impact_score).toFixed(2)}`}
                </p>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
