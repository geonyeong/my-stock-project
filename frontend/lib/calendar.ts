const SEOUL_DAY = new Intl.DateTimeFormat("en-CA", {
  timeZone: "Asia/Seoul",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
});

/** 한국 날짜 YYYY-MM-DD. */
export function seoulDay(value: string | Date): string {
  return SEOUL_DAY.format(typeof value === "string" ? new Date(value) : value);
}

export function calendarDaysUntil(eventTime: string, now: Date = new Date()): number {
  const event = Date.parse(seoulDay(eventTime));
  const today = Date.parse(seoulDay(now));
  return Math.round((event - today) / 86_400_000);
}

function addTradingDays(day: string, count: number, closed: ReadonlySet<string>): string {
  const [year, month, date] = day.split("-").map(Number);
  const cursor = new Date(Date.UTC(year, month - 1, date));
  let left = count;
  while (left > 0) {
    cursor.setUTCDate(cursor.getUTCDate() + 1);
    const iso = cursor.toISOString().slice(0, 10);
    const weekday = cursor.getUTCDay();
    if (weekday !== 0 && weekday !== 6 && !closed.has(iso)) left -= 1;
  }
  return cursor.toISOString().slice(0, 10);
}

/** 기준일 다음 거래일부터 horizon 거래일 안에 발표일이 있는지. 휴장일은 백엔드 목록과 같다. */
export function earningsInHorizon(
  baseTime: string,
  eventTime: string,
  closed: ReadonlySet<string>,
  horizon = 5,
): boolean {
  const base = seoulDay(baseTime);
  const event = seoulDay(eventTime);
  return event > base && event <= addTradingDays(base, horizon, closed);
}
