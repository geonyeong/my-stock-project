// 백엔드는 Decimal 값을 문자열로 직렬화한다.
export type DecimalString = string;

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: string | null;
}

export interface Stock {
  symbol: string;
  name: string;
  market: string;
  sector: string | null;
  is_active: boolean;
}

export interface Candle {
  time: string;
  open_price: DecimalString;
  high_price: DecimalString;
  low_price: DecimalString;
  close_price: DecimalString;
  volume: number;
  trading_value: DecimalString | null;
  flctu_rate: DecimalString | null;
}

export type Direction = "up" | "down" | "flat";

export interface WalkForward {
  accuracy: number;
  baseline_accuracy: number;
  test_start: string;
  test_end: string;
}

export interface Prediction {
  time: string;
  target_date: string;
  model_name: string;
  direction_signal: Direction;
  win_probability: DecimalString | null;
  predicted_close: DecimalString | null;
  upper_bound: DecimalString | null;
  lower_bound: DecimalString | null;
  evaluation: WalkForward | null;
}

export type SentimentLabel = "positive" | "negative" | "neutral";

export interface EarningsEvent {
  time: string;
  symbol: string;
  eps_estimate: DecimalString | null;
  eps_reported: DecimalString | null;
  surprise_pct: DecimalString | null;
}

export interface NewsItem {
  time: string;
  symbol: string | null;
  source: string;
  title: string;
  url: string | null;
  sentiment_label: SentimentLabel;
  sentiment_score: DecimalString;
  impact_score: DecimalString | null;
}
