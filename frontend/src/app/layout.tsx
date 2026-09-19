import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "AI Gateway & Token Observability Dashboard",
  description: "Enterprise Token Observability, PII Scrubbing & Cache Hit Analytics",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-slate-100 flex min-h-screen antialiased">
        <Sidebar />
        <main className="flex-1 ml-64 min-h-screen p-8 bg-gradient-to-b from-background via-surface/30 to-background">
          <div className="max-w-7xl mx-auto space-y-8">{children}</div>
        </main>
      </body>
    </html>
  );
}
