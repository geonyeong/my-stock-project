import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Stock Insight",
  description: "개인용 주가·뉴스 감성·전망 대시보드",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ko" className="h-full antialiased">
      <body className="flex min-h-full flex-col">
        <div className="flex-1">{children}</div>
        <footer className="border-t border-zinc-200 px-6 py-4 text-center text-xs text-zinc-500 dark:border-zinc-800">
          이 화면의 전망과 확률은 모델이 계산한 참고 자료이며 투자 권유가 아닙니다.
        </footer>
      </body>
    </html>
  );
}
