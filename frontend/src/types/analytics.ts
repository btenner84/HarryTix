export interface RevenueAnalytics {
  total_tickets: number;
  total_cost_basis: number;
  expected_revenue_min: number | null;
  expected_revenue_max: number | null;
  expected_revenue_avg: number | null;
  projected_profit_min: number | null;
  projected_profit_max: number | null;
  projected_profit_avg: number | null;
  last_updated: string;
}

export interface PriceHistoryPoint {
  recorded_date: string;
  recorded_hour: number | null;
  min_price: number | null;
  max_price: number | null;
  avg_price: number | null;
  median_price: number | null;
  listing_count: number | null;
  platform_breakdown: Record<string, { avg: number; count: number }> | null;
}

export interface PriceHistoryResponse {
  event_id: number;
  section: string | null;
  history: PriceHistoryPoint[];
}

export interface PlatformComparison {
  platform: string;
  avg_price: number | null;
  min_price: number | null;
  max_price: number | null;
  listing_count: number;
}
