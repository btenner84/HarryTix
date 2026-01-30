export interface Listing {
  id: number;
  event_id: number;
  platform: 'stubhub' | 'seatgeek' | 'vividseats';
  section: string | null;
  row: string | null;
  quantity: number | null;
  price_per_ticket: number;
  total_price: number | null;
  listing_url: string | null;
  fetched_at: string;
}

export interface CurrentListingsResponse {
  event_id: number;
  last_updated: string;
  listings: Listing[];
  by_platform: Record<string, Listing[]>;
}

export interface ComparableListingsResponse {
  inventory_id: number;
  section: string;
  row: string | null;
  listings: Listing[];
  avg_price: number | null;
  min_price: number | null;
  max_price: number | null;
  listing_count: number;
}
