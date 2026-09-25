interface StatusMessageProps {
  loading?: boolean;
  error?: string | null;
  empty?: boolean;
  emptyText?: string;
}

export default function StatusMessage({ loading, error, empty, emptyText = "데이터가 없습니다." }: StatusMessageProps) {
  if (loading) return <p className="py-6 text-sm text-zinc-500">불러오는 중...</p>;
  if (error) return <p className="py-6 text-sm text-red-500">{error}</p>;
  if (empty) return <p className="py-6 text-sm text-zinc-500">{emptyText}</p>;
  return null;
}
