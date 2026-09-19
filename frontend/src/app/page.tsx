"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  Zap,
  DollarSign,
  Layers,
  ShieldCheck,
  Clock,
  ArrowUpRight,
  Sparkles,
  Terminal
} from "lucide-react";
import { MetricCard } from "@/components/MetricCard";
import { fetchOverviewMetrics, fetchLogs, fetchChartData } from "@/lib/api";
import { OverviewMetrics, LogItem, ChartDataResponse } from "@/lib/types";

export default function DashboardOverview() {
  const [metrics, setMetrics] = useState<OverviewMetrics | null>(null);
  const [recentLogs, setRecentLogs] = useState<LogItem[]>([]);
  const [chartData, setChartData] = useState<ChartDataResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      try {
        const [overviewRes, logsRes, chartRes] = await Promise.all([
          fetchOverviewMetrics(),
          fetchLogs(1, 8),
          fetchChartData(),
        ]);
        setMetrics(overviewRes);
        setRecentLogs(logsRes.items);
        setChartData(chartRes);
      } catch (e) {
        console.error("Dashboard failed to load live data", e);
      } finally {
        setLoading(false);
      }
    }

    loadDashboardData();
    const interval = setInterval(loadDashboardData, 4000); // 4s real-time poll
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-8">
      {/* Top Banner Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold tracking-tight text-white">System Observability</h2>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-blue-950 text-blue-400 border border-blue-800/60 flex items-center gap-1.5">
              <Sparkles className="w-3 h-3" /> Live Telemetry
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Real-time telemetry, semantic prompt hash cache hits, and PII protection across active LLM traffic.
          </p>
        </div>

        {/* Quick cURL Dropdown Info */}
        <div className="flex items-center gap-3">
          <div className="glass-panel px-4 py-2 rounded-lg border border-border flex items-center gap-2 text-xs font-mono text-slate-300">
            <Terminal className="w-4 h-4 text-blue-400" />
            <span>base_url: http://localhost:8000/v1</span>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <MetricCard
          title="Total Requests"
          value={metrics ? metrics.total_requests.toLocaleString() : "..."}
          icon={Activity}
          subtitle="Processed volume"
          iconColor="text-blue-400"
        />
        <MetricCard
          title="Cache Hit Ratio"
          value={metrics ? `${metrics.cache_hit_ratio}%` : "..."}
          icon={Zap}
          subtitle={`${metrics?.cache_hits || 0} hits`}
          iconColor="text-amber-400"
          change="+12.4%"
          isPositive={true}
        />
        <MetricCard
          title="Tokens Saved"
          value={metrics ? metrics.tokens_saved.toLocaleString() : "..."}
          icon={Layers}
          subtitle="Redis prompt hits"
          iconColor="text-emerald-400"
        />
        <MetricCard
          title="Dollars Saved"
          value={metrics ? `$${metrics.total_savings_usd.toFixed(2)}` : "..."}
          icon={DollarSign}
          subtitle="Avoided API costs"
          iconColor="text-emerald-400"
          change="+$4.20/hr"
          isPositive={true}
        />
        <MetricCard
          title="Avg Latency"
          value={metrics ? `${metrics.avg_latency_ms} ms` : "..."}
          icon={Clock}
          subtitle="Sub-10ms cache"
          iconColor="text-indigo-400"
        />
        <MetricCard
          title="PII Redacted"
          value={metrics ? metrics.pii_incidents_blocked : "..."}
          icon={ShieldCheck}
          subtitle="Data leaks blocked"
          iconColor="text-rose-400"
        />
      </div>

      {/* Observability Visualizations / Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Latency Performance Distribution */}
        <div className="lg:col-span-2 glass-panel rounded-xl p-6 border border-border">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-base font-semibold text-white">Latency & Throughput Trends</h3>
              <p className="text-xs text-slate-400">Response time vs. Cache acceleration timeline</p>
            </div>
            <div className="flex items-center gap-4 text-xs font-mono">
              <span className="flex items-center gap-1.5 text-slate-400">
                <span className="w-2.5 h-2.5 rounded-sm bg-blue-500"></span> Upstream (~1,200ms)
              </span>
              <span className="flex items-center gap-1.5 text-slate-400">
                <span className="w-2.5 h-2.5 rounded-sm bg-emerald-400"></span> Cache Hit (&lt;10ms)
              </span>
            </div>
          </div>

          {/* Simple Clean Bar Chart Representation */}
          <div className="h-44 flex items-end gap-3 pt-6 px-2 border-b border-border/60 pb-2">
            {[42, 6, 8, 1280, 5, 4, 1140, 7, 5, 9, 6, 1320, 5, 7, 4, 6].map((ms, i) => {
              const isHit = ms < 50;
              const heightPercent = isHit ? Math.max(8, (ms / 50) * 25) : 85;
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-2 group relative">
                  <div
                    className={`w-full rounded-t transition-all ${
                      isHit
                        ? "bg-emerald-500/80 group-hover:bg-emerald-400 shadow-sm shadow-emerald-500/30"
                        : "bg-blue-600/80 group-hover:bg-blue-500"
                    }`}
                    style={{ height: `${heightPercent}%` }}
                  ></div>
                  <span className="text-[9px] text-slate-400 font-mono opacity-0 group-hover:opacity-100 transition-opacity absolute -top-6">
                    {ms}ms
                  </span>
                </div>
              );
            })}
          </div>
          <div className="flex justify-between text-[10px] text-slate-400 font-mono mt-2 px-1">
            <span>10 mins ago</span>
            <span>5 mins ago</span>
            <span>Just now</span>
          </div>
        </div>

        {/* Model Distribution & Financial Summary */}
        <div className="glass-panel rounded-xl p-6 border border-border flex flex-col justify-between">
          <div>
            <h3 className="text-base font-semibold text-white mb-1">Model Distribution</h3>
            <p className="text-xs text-slate-400 mb-6">Traffic breakdown across routed LLM models</p>

            <div className="space-y-4">
              {[
                { name: "gpt-4o", share: 55, color: "bg-blue-500" },
                { name: "gpt-4o-mini", share: 30, color: "bg-indigo-500" },
                { name: "gemini-1.5-flash", share: 15, color: "bg-emerald-500" },
              ].map((m) => (
                <div key={m.name} className="space-y-1.5">
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-slate-300">{m.name}</span>
                    <span className="text-slate-400">{m.share}%</span>
                  </div>
                  <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${m.color} rounded-full`}
                      style={{ width: `${m.share}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-slate-900/60 p-4 rounded-lg border border-border mt-6">
            <div className="flex justify-between text-xs mb-2">
              <span className="text-slate-400">Total API Spend:</span>
              <span className="font-mono text-slate-200">${metrics?.total_spend_usd.toFixed(4) || "0.0000"}</span>
            </div>
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-emerald-400">Net Money Saved:</span>
              <span className="font-mono text-emerald-400">+${metrics?.total_savings_usd.toFixed(4) || "0.0000"}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent API Transactions Table */}
      <div className="glass-panel rounded-xl border border-border overflow-hidden">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-white">Live Request Stream</h3>
            <p className="text-xs text-slate-400">Real-time inspection of incoming /v1/chat/completions calls</p>
          </div>
          <span className="text-xs font-mono text-slate-400 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
            Streaming
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/80 text-slate-400 border-b border-border">
              <tr>
                <th className="px-6 py-3">Time</th>
                <th className="px-6 py-3">Model</th>
                <th className="px-6 py-3">Cache State</th>
                <th className="px-6 py-3">Latency</th>
                <th className="px-6 py-3">Tokens</th>
                <th className="px-6 py-3">Cost / Saved</th>
                <th className="px-6 py-3">PII Guard</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {recentLogs.length > 0 ? (
                recentLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-3 text-slate-400">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="px-6 py-3 text-slate-200 font-semibold">{log.model}</td>
                    <td className="px-6 py-3">
                      {log.cache_status === "HIT" ? (
                        <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/40 text-[10px]">
                          CACHE HIT
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800/40 text-[10px]">
                          CACHE MISS
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-3">
                      <span className={log.latency_ms < 20 ? "text-emerald-400 font-bold" : "text-slate-300"}>
                        {log.latency_ms} ms
                      </span>
                    </td>
                    <td className="px-6 py-3 text-slate-300">{log.total_tokens}</td>
                    <td className="px-6 py-3">
                      {log.cache_status === "HIT" ? (
                        <span className="text-emerald-400">+${log.cost_saved_usd.toFixed(5)}</span>
                      ) : (
                        <span className="text-slate-400">${log.cost_usd.toFixed(5)}</span>
                      )}
                    </td>
                    <td className="px-6 py-3">
                      {log.pii_detected ? (
                        <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-800/40 text-[10px]">
                          REDACTED ({log.pii_types_found.join(", ")})
                        </span>
                      ) : (
                        <span className="text-slate-500">Clean</span>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-slate-400 font-sans">
                    No requests processed yet. Point your LLM application to http://localhost:8000/v1 to see live data.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
