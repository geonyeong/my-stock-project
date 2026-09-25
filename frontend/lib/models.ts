import type { ForecastSeries } from "@/components/PriceChart";
import type { Prediction } from "./types";

interface ModelMeta {
  label: string;
  color: string;
}

const MODEL_META: Record<string, ModelMeta> = {
  lightgbm_dir_5d: { label: "LightGBM 5거래일 방향", color: "#8b5cf6" },
  lightgbm_dir_5d_sent: { label: "LightGBM 5거래일 방향(감성 포함)", color: "#a855f7" },
  prophet: { label: "Prophet 추세", color: "#f59e0b" },
  dlinear: { label: "DLinear 경로", color: "#10b981" },
};

export function modelMeta(modelName: string): ModelMeta {
  return MODEL_META[modelName] ?? { label: modelName, color: "#64748b" };
}

export function groupByModel(predictions: Prediction[]): Map<string, Prediction[]> {
  const groups = new Map<string, Prediction[]>();
  for (const p of predictions) {
    groups.set(p.model_name, [...(groups.get(p.model_name) ?? []), p]);
  }
  return groups;
}

/** 예측 종가가 있는 모델만 차트용 경로로 바꾼다. */
export function toForecastSeries(predictions: Prediction[]): ForecastSeries[] {
  const series: ForecastSeries[] = [];
  for (const [modelName, rows] of groupByModel(predictions)) {
    const points = rows
      .filter((r) => r.predicted_close !== null)
      .map((r) => ({
        time: `${r.target_date}T00:00:00+09:00`,
        value: Number(r.predicted_close),
        lower: r.lower_bound === null ? null : Number(r.lower_bound),
        upper: r.upper_bound === null ? null : Number(r.upper_bound),
      }));
    if (points.length > 0) {
      const meta = modelMeta(modelName);
      series.push({ label: meta.label, color: meta.color, points });
    }
  }
  return series;
}
