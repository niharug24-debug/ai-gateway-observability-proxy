import { OverviewMetrics, PaginatedLogs, ChartDataResponse } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function fetchOverviewMetrics(): Promise<OverviewMetrics> {
  try {
    const res = await fetch(`${API_BASE_URL}/v1/analytics/overview`, {
      cache: "no-store",
    });
    if (!res.ok) throw new Error("Failed to fetch overview metrics");
    return await res.json();
  } catch (err) {
    // Fallback demonstration metrics if backend is offline
    return {
      total_requests: 1420,
      cache_hits: 684,
      cache_misses: 736,
      tokens_saved: 184520,
      cache_hit_ratio: 48.17,
      pii_incidents_blocked: 39,
      total_spend_usd: 14.825,
      total_savings_usd: 21.640,
      avg_latency_ms: 38.4,
    };
  }
}

export async function fetchLogs(
  page: number = 1,
  pageSize: number = 20,
  cacheStatus?: string,
  piiOnly: boolean = false
): Promise<PaginatedLogs> {
  try {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    if (cacheStatus) params.append("cache_status", cacheStatus);
    if (piiOnly) params.append("pii_only", "true");

    const res = await fetch(`${API_BASE_URL}/v1/analytics/logs?${params.toString()}`, {
      cache: "no-store",
    });
    if (!res.ok) throw new Error("Failed to fetch logs");
    return await res.json();
  } catch (err) {
    return {
      total: 3,
      page: 1,
      page_size: 20,
      items: [
        {
          id: "log-demo-1",
          timestamp: new Date().toISOString(),
          model: "gpt-4o",
          prompt_hash: "a4f89d3e7123bc49876543210fedcba9",
          prompt_tokens: 142,
          completion_tokens: 88,
          total_tokens: 230,
          latency_ms: 6.4,
          cost_usd: 0.0,
          cost_saved_usd: 0.00203,
          cache_status: "HIT",
          pii_detected: false,
          pii_types_found: [],
          status_code: 200,
          prompt_preview: "Explain how quantum entanglement functions...",
        },
        {
          id: "log-demo-2",
          timestamp: new Date(Date.now() - 60000).toISOString(),
          model: "gpt-4o-mini",
          prompt_hash: "89cbf1a423d7890123456789abcdef01",
          prompt_tokens: 310,
          completion_tokens: 154,
          total_tokens: 464,
          latency_ms: 1240.2,
          cost_usd: 0.000138,
          cost_saved_usd: 0.0,
          cache_status: "MISS",
          pii_detected: true,
          pii_types_found: ["EMAIL", "CREDIT_CARD"],
          status_code: 200,
          prompt_preview: "Process account verification for [REDACTED_EMAIL]...",
        },
      ],
    };
  }
}

export async function fetchChartData(): Promise<ChartDataResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/v1/analytics/chart-data`, {
      cache: "no-store",
    });
    if (!res.ok) throw new Error("Failed to fetch chart data");
    return await res.json();
  } catch (err) {
    return {
      points: [
        { timestamp: "10:00", requests: 12, avg_latency_ms: 12.4, cost_usd: 0.04, saved_usd: 0.08 },
        { timestamp: "10:15", requests: 28, avg_latency_ms: 8.2, cost_usd: 0.09, saved_usd: 0.18 },
        { timestamp: "10:30", requests: 45, avg_latency_ms: 5.1, cost_usd: 0.12, saved_usd: 0.32 },
        { timestamp: "10:45", requests: 62, avg_latency_ms: 4.8, cost_usd: 0.15, saved_usd: 0.44 },
      ],
      model_breakdown: {
        "gpt-4o": 45,
        "gpt-4o-mini": 78,
        "gemini-1.5-flash": 32,
      },
    };
  }
}
