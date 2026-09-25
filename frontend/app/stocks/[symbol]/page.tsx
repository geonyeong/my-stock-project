import Link from "next/link";

import StockDetail from "@/components/StockDetail";

export default async function StockPage(props: PageProps<"/stocks/[symbol]">) {
  const { symbol } = await props.params;

  return (
    <main className="mx-auto w-full max-w-5xl px-6 py-10">
      <Link href="/" className="text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100">
        ← 종목 목록
      </Link>
      <div className="mt-4">
        <StockDetail symbol={decodeURIComponent(symbol)} />
      </div>
    </main>
  );
}
