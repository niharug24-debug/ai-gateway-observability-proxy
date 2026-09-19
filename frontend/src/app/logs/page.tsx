"use client";

import { useEffect, useState } from "react";
import { Search, Filter, RefreshCw, Layers, Zap, ShieldAlert } from "lucide-react";
import { fetchLogs } from "@/lib/api";
import { LogItem } from "@/lib/types";

export default function RequestLogsPage() {
  const [logs, setLogs] = useState<LogItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [filterCache, setFilterCache] = useState<string>("");
  const [filterPii, setFilterPii] = useState<boolean>(false);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [loading, setLoading] = useState(false);

  async function loadData() {
    setLoading(true);
    try {
      const data = await fetchLogs(1, 50, filterCache || undefined, filterPii);
      setLogs(data.items);
      setTotalCount(data.total);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [filterCache, filterPii]);

  const filteredLogs = logs.filter((l) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      l.model.toLowerCase().includes(term) ||
      l.prompt_hash.toLowerCase().includes(term) ||
      (l.prompt_preview && l.prompt_preview.toLowerCase().includes(term))
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">API Transaction Logs</h2>
          <p className="text-sm text-slate-400 mt-1">
            Complete audit trail of all intercepted `/v1/chat/completions` requests, hashes, and latencies.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-sm font-medium text-slate-200 transition-colors border border-border self-start md:self-auto"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-blue-400" : ""}`} />
          Refresh Feed
        </button>
      </div>

      {/* Filter Bar */}
      <div className="glass-panel p-4 rounded-xl border border-border flex flex-col md:flex-row gap-4 justify-between items-center">
        {/* Search Input */}
        <div className="relative w-full md:w-96">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by model, prompt hash, or text..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-900/80 border border-border rounded-lg pl-9 pr-4 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Filter Controls */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          <select
            value={filterCache}
            onChange={(e) => setFilterCache(e.target.value)}
            className="bg-slate-900/80 border border-border rounded-lg px-3 py-2 text-xs text-slate-300 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Cache States</option>
            <option value="HIT">Cache HIT only</option>
            <option value="MISS">Cache MISS only</option>
          </select>

          <button
            onClick={() => setFilterPii(!filterPii)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border transition-colors ${
              filterPii
                ? "bg-rose-950 text-rose-300 border-rose-800"
                : "bg-slate-900/80 text-slate-400 border-border hover:text-slate-200"
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5" />
            PII Redacted Only
          </button>
        </div>
      </div>

      {/* Logs Table */}
      <div className="glass-panel rounded-xl border border-border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/80 text-slate-400 border-b border-border">
              <tr>
                <th className="px-5 py-3">Timestamp</th>
                <th className="px-5 py-3">Model</th>
                <th className="px-5 py-3">Prompt Hash (SHA-256)</th>
                <th className="px-5 py-3">Cache</th>
                <th className="px-5 py-3">Latency</th>
                <th className="px-5 py-3">Tokens (P/C/Total)</th>
                <th className="px-5 py-3">Cost / Savings</th>
                <th className="px-5 py-3">PII Interception</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {filteredLogs.length > 0 ? (
                filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-5 py-3 text-slate-400 whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="px-5 py-3 text-slate-200 font-semibold">{log.model}</td>
                    <td className="px-5 py-3 text-slate-400">
                      <span className="bg-slate-900 px-2 py-1 rounded text-[11px] border border-border">
                        {log.prompt_hash.substring(0, 12)}...
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      {log.cache_status === "HIT" ? (
                        <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800/40 text-[10px] flex items-center gap-1 w-fit">
                          <Zap className="w-3 h-3" /> HIT
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800/40 text-[10px] w-fit">
                          MISS
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3">
                      <span className={log.latency_ms < 20 ? "text-emerald-400 font-bold" : "text-slate-300"}>
                        {log.latency_ms} ms
                      </span>
                    </td>
                    <td className="px-5 py-3 text-slate-300">
                      {log.prompt_tokens} / {log.completion_tokens} (
                      <span className="text-white font-semibold">{log.total_tokens}</span>)
                    </td>
                    <td className="px-5 py-3">
                      {log.cache_status === "HIT" ? (
                        <span className="text-emerald-400 font-semibold">+${log.cost_saved_usd.toFixed(6)}</span>
                      ) : (
                        <span className="text-slate-400">${log.cost_usd.toFixed(6)}</span>
                      )}
                    </td>
                    <td className="px-5 py-3">
                      {log.pii_detected ? (
                        <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-400 border border-rose-800/40 text-[10px]">
                          {log.pii_types_found.join(", ")}
                        </span>
                      ) : (
                        <span className="text-slate-500">None</span>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-slate-400 font-sans">
                    No matching transaction logs found.
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
