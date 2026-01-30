import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';

export interface ComparableListing {
  section: string;
  row: string;
  quantity: number;
  all_in_price: number;
}

export interface InventoryItem {
  inventory_id: number;
  set_name: string;
  event_id: number;
  event_date: string;
  venue: string;
  section: string;
  row: string | null;
  quantity: number;
  cost_per_ticket: number;
  total_cost: number;
  market: {
    min_price: number | null;
    max_price: number | null;
    avg_price: number | null;
    listing_count: number;
  };
  profit: {
    min: number | null;
    max: number | null;
    avg: number | null;
  };
  comparable_listings: ComparableListing[];
}

export interface LiveInventoryResponse {
  fetched_at: string;
  items: InventoryItem[];
  summary: {
    total_tickets: number;
    total_cost: number;
    total_min_value: number;
    total_max_value: number;
    total_min_profit: number | null;
    total_max_profit: number | null;
  };
}

export function useLiveInventory() {
  return useQuery({
    queryKey: ['live-inventory'],
    queryFn: async (): Promise<LiveInventoryResponse> => {
      const response = await apiClient.get('/listings/live-inventory');
      return response.data;
    },
    refetchInterval: 60 * 60 * 1000, // Refetch every hour
    staleTime: 5 * 60 * 1000, // Consider data stale after 5 minutes
    retry: 2,
  });
}
