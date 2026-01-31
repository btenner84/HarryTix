import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

export interface VividMarketData {
  listings_count: number;
  total_seats: number;
  min_price: number | null;
  max_price: number | null;
  avg_price: number | null;
  avg_lowest_2: number | null;  // Average of 2 lowest prices
}

export interface TicketSet {
  set_name: string;
  date: string;
  section: string;
  quantity: number;
  cost_per_ticket: number;
  total_cost: number;
  vivid_event_id: string;
  stubhub_event_id: string;
  vivid_buyer_price: number | null;
  vivid_you_receive: number | null;
  stubhub_buyer_price: number | null;
  stubhub_you_receive: number | null;
  avg_you_receive: number | null;
  profit_per_ticket: number | null;
  total_profit: number | null;
  best_platform: string | null;
  comparable_count: number;
  vivid_market: VividMarketData | null;
}

export interface ComparisonSummary {
  total_tickets: number;
  total_cost: number;
  total_vivid_revenue: number;
  total_vivid_profit: number;
  total_stubhub_revenue: number;
  total_stubhub_profit: number;
  best_overall: string;
}

export interface ComparisonData {
  sets: TicketSet[];
  summary: ComparisonSummary;
}

async function fetchComparison(): Promise<ComparisonData> {
  const response = await api.get('/comparison');
  return response.data;
}

export function useComparison() {
  return useQuery({
    queryKey: ['comparison'],
    queryFn: fetchComparison,
    refetchInterval: 5 * 60 * 1000, // Refresh every 5 minutes
    staleTime: 2 * 60 * 1000,
  });
}
