export interface InventoryItem {
  id: number;
  event_id: number;
  section: string;
  row: string | null;
  seat_numbers: string | null;
  quantity: number;
  cost_per_ticket: number;
  total_cost: number;
  purchase_date: string | null;
  target_sell_min: number | null;
  target_sell_max: number | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
  // Market data
  current_market_price: number | null;
  expected_revenue: number | null;
  expected_profit: number | null;
  comparable_listings_count: number;
  min_market_price: number | null;
  max_market_price: number | null;
  avg_market_price: number | null;
}
