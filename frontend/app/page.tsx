import StockList from "@/components/StockList";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-5xl px-6 py-10">
      <h1 className="text-2xl font-bold">종목 대시보드</h1>
      <p className="mt-1 text-sm text-zinc-500">관심 종목의 일봉, 뉴스 감성, 모델 전망을 확인합니다.</p>
      <div className="mt-8">
        <StockList />
      </div>
    </main>
  );
}
