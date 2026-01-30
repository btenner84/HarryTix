import { apiClient } from './client';
import type { RevenueAnalytics, PriceHistoryResponse, PlatformComparison } from '../types/analytics';

export async function fetchRevenueAnalytics(): Promise<RevenueAnalytics> {
  const response = await apiClient.get<RevenueAnalytics>('/analytics/revenue');
  return response.data;
}

export async function fetchPriceHistory(
  eventId: number,
  section?: string,
  days: number = 30
): Promise<PriceHistoryResponse> {
  const response = await apiClient.get<PriceHistoryResponse>('/analytics/price-history', {
    params: { event_id: eventId, section, days },
  });
  return response.data;
}

export async function fetchPlatformComparison(eventId: number): Promise<PlatformComparison[]> {
  const response = await apiClient.get<PlatformComparison[]>('/analytics/platform-comparison', {
    params: { event_id: eventId },
  });
  return response.data;
}
