import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "다목적 산림경영 AI Agent — MOFOM",
  description:
    "한국 사유림 산주를 위한 Faustmann–Hartman 기반 산림경영 의사결정 지원 시스템",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="antialiased">{children}</body>
    </html>
  );
}
