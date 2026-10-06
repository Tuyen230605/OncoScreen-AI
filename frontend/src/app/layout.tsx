import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "OncoScreen AI — Tầm soát ung thư thông minh",
  description:
    "AI Agent hỗ trợ đánh giá nguy cơ và tầm soát ung thư, có bác sĩ phê duyệt kết quả. Không chẩn đoán bệnh.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" className={inter.variable}>
      <body className="min-h-screen font-sans">{children}</body>
    </html>
  );
}
