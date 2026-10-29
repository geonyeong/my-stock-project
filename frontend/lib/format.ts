const priceFormatter = new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 2 });
const volumeFormatter = new Intl.NumberFormat("ko-KR");
const dateFormatter = new Intl.DateTimeFormat("ko-KR", {
  timeZone: "Asia/Seoul",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

export function formatPrice(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return "-";
  return priceFormatter.format(Number(value));
}

export function formatVolume(value: number): string {
  return volumeFormatter.format(value);
}

export function formatDate(value: string): string {
  return dateFormatter.format(new Date(value));
}

export function formatRate(value: string | null): string {
  if (value === null) return "-";
  const n = Number(value);
  return `${n > 0 ? "+" : ""}${n.toFixed(2)}%`;
}

export function formatSurprise(value: string | null): string {
  if (value === null) return "-";
  const n = Number(value);
  return `${n > 0 ? "+" : ""}${n.toFixed(2)}%`;
}

export function formatPercent(value: string | number | null): string {
  if (value === null) return "-";
  return `${(Number(value) * 100).toFixed(1)}%`;
}

export function rateColor(value: string | null): string {
  if (value === null) return "text-zinc-500";
  const n = Number(value);
  if (n > 0) return "text-red-500";
  if (n < 0) return "text-blue-500";
  return "text-zinc-500";
}
