import type { Metadata } from "next";
import "./globals.css";
import { Nav } from "@/components/nav";

export const metadata: Metadata = {
  title: "EGX Scanner — ماسح البورصة المصرية",
  description: "ماسح فنى لأسهم البورصة المصرية يكشف الفرص اليومية",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ar" dir="rtl">
      <head>
        <link
          rel="preconnect"
          href="https://fonts.googleapis.com"
        />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-screen bg-bg text-text">
        <Nav />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">{children}</main>
        <footer className="max-w-7xl mx-auto px-4 sm:px-6 py-10 text-center text-xs text-muted">
          هذه الأداة للأغراض التعليمية فقط ولا تُعدّ توصية بشراء أو بيع. تداول على مسؤوليتك.
        </footer>
      </body>
    </html>
  );
}
