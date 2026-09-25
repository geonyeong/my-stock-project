"use client";

import { useEffect, useState } from "react";

interface ApiState<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
}

interface Settled<T> {
  key: string;
  data: T | null;
  error: string | null;
}

/** key 가 바뀌면 다시 불러온다. 응답이 도착하기 전까지는 loading 이다. */
export function useApi<T>(fetcher: (signal: AbortSignal) => Promise<T>, key: string): ApiState<T> {
  const [settled, setSettled] = useState<Settled<T> | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetcher(controller.signal)
      .then((data) => setSettled({ key, data, error: null }))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        const message = err instanceof Error ? err.message : "데이터를 불러오지 못했습니다.";
        setSettled({ key, data: null, error: message });
      });
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  if (!settled || settled.key !== key) return { data: null, error: null, loading: true };
  return { data: settled.data, error: settled.error, loading: false };
}
