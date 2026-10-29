import { formatDate, formatPercent, formatPrice } from "@/lib/format";
import { groupByModel, modelMeta } from "@/lib/models";
import type { Direction, Prediction } from "@/lib/types";

const DIRECTION_TEXT: Record<Direction, string> = { up: "상승 우세", down: "하락 우세", flat: "뚜렷하지 않음" };
const DIRECTION_STYLE: Record<Direction, string> = {
  up: "text-red-500",
  down: "text-blue-500",
  flat: "text-zinc-500",
};

function ModelCard({ modelName, rows }: { modelName: string; rows: Prediction[] }) {
  const meta = modelMeta(modelName);
  const last = rows[rows.length - 1];
  const hasPath = last.predicted_close !== null;

  return (
    <div className="rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
      <div className="flex items-center gap-2">
        <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: meta.color }} />
        <h3 className="text-sm font-semibold">{meta.label}</h3>
      </div>
      <p className="mt-1 text-xs text-zinc-500">
        기준 {formatDate(last.time)} · 목표 {last.target_date}
      </p>
      <p className={`mt-3 text-lg font-semibold ${DIRECTION_STYLE[last.direction_signal]}`}>
        {DIRECTION_TEXT[last.direction_signal]}
      </p>
      {last.win_probability !== null && (
        <p className="text-sm text-zinc-600 dark:text-zinc-400">상승 확률 {formatPercent(last.win_probability)}</p>
      )}
      {last.evaluation && (
        <p className="mt-2 text-xs text-zinc-500">
          최근 검증 정확도 {formatPercent(last.evaluation.accuracy)}, 기준선{" "}
          {formatPercent(last.evaluation.baseline_accuracy)} ({last.evaluation.test_start}~{last.evaluation.test_end})
        </p>
      )}
      {hasPath && (
        <p className="text-sm text-zinc-600 dark:text-zinc-400">
          추정 {formatPrice(last.predicted_close)}
          {last.lower_bound !== null && last.upper_bound !== null && (
            <span className="text-xs">
              {" "}
              (구간 {formatPrice(last.lower_bound)} ~ {formatPrice(last.upper_bound)})
            </span>
          )}
        </p>
      )}
    </div>
  );
}

export default function PredictionPanel({ predictions }: { predictions: Prediction[] }) {
  const groups = [...groupByModel(predictions)];

  return (
    <div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {groups.map(([modelName, rows]) => (
          <ModelCard key={modelName} modelName={modelName} rows={rows} />
        ))}
      </div>
      <p className="mt-3 text-xs text-zinc-500">
        모델 출력은 과거 데이터에 기반한 확률·구간 추정이며 실제 가격을 보장하지 않습니다. 투자 판단의 근거로 쓰지 마세요.
      </p>
    </div>
  );
}
