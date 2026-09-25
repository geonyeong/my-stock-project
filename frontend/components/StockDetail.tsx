"use client";

import CandleTable from "@/components/CandleTable";
import NewsList from "@/components/NewsList";
import PredictionPanel from "@/components/PredictionPanel";
import PriceChart from "@/components/PriceChart";
import StatusMessage from "@/components/StatusMessage";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { formatPrice, formatRate, rateColor } from "@/lib/format";
import { toForecastSeries } from "@/lib/models";

const CHART_DAYS = 120;

export default function StockDetail({ symbol }: { symbol: string }) {
  const stock = useApi((signal) => api.stock(symbol, signal), `stock:${symbol}`);
  const candles = useApi((signal) => api.candles(symbol, 250, signal), `candles:${symbol}`);
  const predictions = useApi((signal) => api.predictions(symbol, signal), `predictions:${symbol}`);

  if (stock.loading || stock.error || !stock.data) {
    return <StatusMessage loading={stock.loading} error={stock.error} />;
  }

  const rows = candles.data ?? [];
  const latest = rows.at(-1);
  const predictionRows = predictions.data ?? [];

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="font-mono text-sm text-zinc-500">
            {stock.data.symbol} · {stock.data.market}
          </p>
          <h1 className="text-2xl font-bold">{stock.data.name}</h1>
        </div>
        {latest && (
          <div className="text-right tabular-nums">
            <p className="text-2xl font-semibold">{formatPrice(latest.close_price)}</p>
            <p className={`text-sm ${rateColor(latest.flctu_rate)}`}>{formatRate(latest.flctu_rate)}</p>
          </div>
        )}
      </header>

      <section className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
        <h2 className="mb-3 text-sm font-semibold text-zinc-500">일봉 종가와 모델 전망</h2>
        {candles.loading || candles.error || rows.length === 0 ? (
          <StatusMessage
            loading={candles.loading}
            error={candles.error}
            empty={rows.length === 0}
            emptyText="수집된 일봉이 없습니다. collectors.prices.run 을 실행하세요."
          />
        ) : (
          <>
            <PriceChart candles={rows.slice(-CHART_DAYS)} forecasts={toForecastSeries(predictionRows)} />
            <div className="mt-6">
              <CandleTable candles={rows} />
            </div>
          </>
        )}
      </section>

      <section className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
        <h2 className="mb-3 text-sm font-semibold text-zinc-500">모델 전망</h2>
        {predictions.loading || predictions.error || predictionRows.length === 0 ? (
          <StatusMessage
            loading={predictions.loading}
            error={predictions.error}
            empty={predictionRows.length === 0}
            emptyText="예측 결과가 없습니다. prediction.run_lightgbm 을 실행하세요."
          />
        ) : (
          <PredictionPanel predictions={predictionRows} />
        )}
      </section>

      <section className="rounded-xl border border-zinc-200 p-4 dark:border-zinc-800">
        <h2 className="mb-3 text-sm font-semibold text-zinc-500">뉴스 감성</h2>
        <NewsList symbol={symbol} />
      </section>
    </div>
  );
}
