import { formatDate, formatPrice } from "@/lib/format";
import type { Candle } from "@/lib/types";

export interface ForecastPoint {
  time: string;
  value: number;
  lower: number | null;
  upper: number | null;
}

export interface ForecastSeries {
  label: string;
  color: string;
  points: ForecastPoint[];
}

interface PriceChartProps {
  candles: Candle[];
  forecasts?: ForecastSeries[];
}

const WIDTH = 800;
const HEIGHT = 280;
const PAD = { top: 16, right: 64, bottom: 28, left: 8 };

export default function PriceChart({ candles, forecasts = [] }: PriceChartProps) {
  const history = candles.map((c) => ({ t: new Date(c.time).getTime(), v: Number(c.close_price) }));
  if (history.length < 2) return null;

  const forecastValues = forecasts.flatMap((s) =>
    s.points.flatMap((p) => [p.value, p.lower ?? p.value, p.upper ?? p.value]),
  );
  const forecastTimes = forecasts.flatMap((s) => s.points.map((p) => new Date(p.time).getTime()));

  const values = [...history.map((h) => h.v), ...forecastValues];
  const times = [...history.map((h) => h.t), ...forecastTimes];
  const minV = Math.min(...values);
  const maxV = Math.max(...values);
  const minT = Math.min(...times);
  const maxT = Math.max(...times);
  const spanV = maxV - minV || 1;
  const spanT = maxT - minT || 1;

  const x = (t: number) => PAD.left + ((t - minT) / spanT) * (WIDTH - PAD.left - PAD.right);
  const y = (v: number) => PAD.top + (1 - (v - minV) / spanV) * (HEIGHT - PAD.top - PAD.bottom);
  const toPath = (pts: { t: number; v: number }[]) =>
    pts.map((p, i) => `${i === 0 ? "M" : "L"}${x(p.t).toFixed(1)},${y(p.v).toFixed(1)}`).join(" ");

  const last = history[history.length - 1];
  const ticks = [maxV, minV + spanV / 2, minV];

  return (
    <figure>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="h-auto w-full" role="img" aria-label="종가 차트">
        {ticks.map((v) => (
          <g key={v}>
            <line x1={PAD.left} x2={WIDTH - PAD.right} y1={y(v)} y2={y(v)} className="stroke-zinc-200 dark:stroke-zinc-800" />
            <text x={WIDTH - PAD.right + 6} y={y(v) + 4} className="fill-zinc-500 text-[11px]">
              {formatPrice(v)}
            </text>
          </g>
        ))}

        {forecasts.map((s) => {
          const band = s.points.filter((p) => p.lower !== null && p.upper !== null);
          const anchor = { t: last.t, v: last.v };
          const line = [anchor, ...s.points.map((p) => ({ t: new Date(p.time).getTime(), v: p.value }))];
          const bandPath =
            band.length > 0
              ? [
                  ...band.map((p, i) => `${i === 0 ? "M" : "L"}${x(new Date(p.time).getTime())},${y(p.upper as number)}`),
                  ...[...band].reverse().map((p) => `L${x(new Date(p.time).getTime())},${y(p.lower as number)}`),
                  "Z",
                ].join(" ")
              : null;
          return (
            <g key={s.label}>
              {bandPath && <path d={bandPath} fill={s.color} fillOpacity={0.12} />}
              <path d={toPath(line)} fill="none" stroke={s.color} strokeWidth={2} strokeDasharray="5 4" />
            </g>
          );
        })}

        <path d={toPath(history)} fill="none" className="stroke-zinc-900 dark:stroke-zinc-100" strokeWidth={1.8} />

        <text x={PAD.left} y={HEIGHT - 8} className="fill-zinc-500 text-[11px]">
          {formatDate(new Date(minT).toISOString())}
        </text>
        <text x={WIDTH - PAD.right} y={HEIGHT - 8} textAnchor="end" className="fill-zinc-500 text-[11px]">
          {formatDate(new Date(maxT).toISOString())}
        </text>
      </svg>
      {forecasts.length > 0 && (
        <figcaption className="mt-2 flex flex-wrap gap-4 text-xs text-zinc-500">
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-0.5 w-4 bg-zinc-900 dark:bg-zinc-100" />
            실제 종가
          </span>
          {forecasts.map((s) => (
            <span key={s.label} className="flex items-center gap-1.5">
              <span className="inline-block h-0.5 w-4" style={{ backgroundColor: s.color }} />
              {s.label} (점선: 추정, 음영: 구간)
            </span>
          ))}
        </figcaption>
      )}
    </figure>
  );
}
