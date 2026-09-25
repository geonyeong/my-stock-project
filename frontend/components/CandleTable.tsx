import { formatDate, formatPrice, formatRate, formatVolume, rateColor } from "@/lib/format";
import type { Candle } from "@/lib/types";

interface CandleTableProps {
  candles: Candle[];
  rows?: number;
}

export default function CandleTable({ candles, rows = 20 }: CandleTableProps) {
  const recent = candles.slice(-rows).reverse();

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-right text-sm tabular-nums">
        <thead className="border-b border-zinc-200 text-xs text-zinc-500 dark:border-zinc-800">
          <tr>
            <th className="py-2 text-left font-medium">날짜</th>
            <th className="py-2 font-medium">시가</th>
            <th className="py-2 font-medium">고가</th>
            <th className="py-2 font-medium">저가</th>
            <th className="py-2 font-medium">종가</th>
            <th className="py-2 font-medium">등락률</th>
            <th className="py-2 font-medium">거래량</th>
          </tr>
        </thead>
        <tbody>
          {recent.map((c) => (
            <tr key={c.time} className="border-b border-zinc-100 dark:border-zinc-900">
              <td className="py-1.5 text-left">{formatDate(c.time)}</td>
              <td>{formatPrice(c.open_price)}</td>
              <td>{formatPrice(c.high_price)}</td>
              <td>{formatPrice(c.low_price)}</td>
              <td className="font-medium">{formatPrice(c.close_price)}</td>
              <td className={rateColor(c.flctu_rate)}>{formatRate(c.flctu_rate)}</td>
              <td>{formatVolume(c.volume)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
