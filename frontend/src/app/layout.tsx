import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OncoScreen AI",
  description: "AI Agent hỗ trợ tầm soát ung thư — có bác sĩ phê duyệt",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
