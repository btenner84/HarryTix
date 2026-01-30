import { useQuery } from '@tanstack/react-query';
import { fetchRevenueAnalytics, fetchPriceHistory, fetchPlatformComparison } from '../api/analytics';

export function useRevenueAnalytics() {
  return useQuery({
    queryKey: ['analytics', 'revenue'],
    queryFn: fetchRevenueAnalytics,
    refetchInterval: 5 * 60 * 1000,
    staleTime: 60 * 1000,
  });
}

export function usePriceHistory(eventId: number | undefined, section?: string, days: number = 30) {
  return useQuery({
    queryKey: ['analytics', 'price-history', eventId, section, days],
    queryFn: () => fetchPriceHistory(eventId!, section, days),
    enabled: !!eventId,
    refetchInterval: 5 * 60 * 1000,
  });
}

export function usePlatformComparison(eventId: number | undefined) {
  return useQuery({
    queryKey: ['analytics', 'platform-comparison', eventId],
    queryFn: () => fetchPlatformComparison(eventId!),
    enabled: !!eventId,
    refetchInterval: 5 * 60 * 1000,
  });
}
