export interface OverviewMetrics {
  total_requests: number;
  cache_hits: number;
  cache_misses: number;
  tokens_saved: number;
  cache_hit_ratio: number;
  pii_incidents_blocked: number;
  total_spend_usd: number;
  total_savings_usd: number;
  avg_latency_ms: number;
}

export interface LogItem {
  id: string;
  timestamp: string;
  model: string;
  prompt_hash: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  latency_ms: number;
  cost_usd: number;
  cost_saved_usd: number;
  cache_status: "HIT" | "MISS" | "BYPASS";
  pii_detected: boolean;
  pii_types_found: string[];
  status_code: number;
  prompt_preview?: string;
}

export interface PaginatedLogs {
  total: number;
  page: number;
  page_size: number;
  items: LogItem[];
}

export interface ChartDataPoint {
  timestamp: string;
  requests: number;
  avg_latency_ms: number;
  cost_usd: number;
  saved_usd: number;
}

export interface ChartDataResponse {
  points: ChartDataPoint[];
  model_breakdown: Record<string, number>;
}
