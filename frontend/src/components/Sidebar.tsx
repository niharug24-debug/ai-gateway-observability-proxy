"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, FileText, ShieldAlert, Cpu, Activity, Database } from "lucide-react";

export function Sidebar() {
  const pathname = usePathname();

  const navigation = [
    { name: "Overview", href: "/", icon: LayoutDashboard },
    { name: "Request Logs", href: "/logs", icon: FileText },
    { name: "PII Security Audit", href: "/security", icon: ShieldAlert },
  ];

  return (
    <aside className="w-64 bg-surface border-r border-border min-h-screen flex flex-col justify-between fixed top-0 left-0 z-40">
      <div>
        {/* Brand Header */}
        <div className="h-16 flex items-center px-6 border-b border-border gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Cpu className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-wide text-slate-100">AI GATEWAY</h1>
            <p className="text-[10px] text-slate-400 font-mono">OBSERVABILITY v1.0</p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-4 space-y-1.5">
          <p className="px-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Monitoring
          </p>
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-blue-600/15 text-blue-400 border border-blue-500/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-blue-400" : "text-slate-400"}`} />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Footer System Status Badge */}
      <div className="p-4 border-t border-border">
        <div className="bg-slate-900/60 rounded-lg p-3 border border-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-slate-300 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Proxy Status
            </span>
            <span className="text-[10px] bg-emerald-950 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-800/50">
              Active
            </span>
          </div>
          <div className="text-[11px] text-slate-400 space-y-1 font-mono">
            <div className="flex justify-between">
              <span>Port:</span>
              <span className="text-slate-200">8000</span>
            </div>
            <div className="flex justify-between">
              <span>Cache:</span>
              <span className="text-emerald-400">Redis (Sub-10ms)</span>
            </div>
            <div className="flex justify-between">
              <span>PII Guard:</span>
              <span className="text-blue-400">Enabled</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
