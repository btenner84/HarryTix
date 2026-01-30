import { apiClient } from './client';
import type { CurrentListingsResponse, ComparableListingsResponse, Listing } from '../types/listing';

export async function fetchCurrentListings(eventId: number): Promise<CurrentListingsResponse> {
  const response = await apiClient.get<CurrentListingsResponse>('/listings/current', {
    params: { event_id: eventId },
  });
  return response.data;
}

export async function fetchComparableListings(inventoryId: number): Promise<ComparableListingsResponse> {
  const response = await apiClient.get<ComparableListingsResponse>(`/listings/comparable/${inventoryId}`);
  return response.data;
}

export async function fetchAllRecentListings(hours: number = 24): Promise<Listing[]> {
  const response = await apiClient.get<Listing[]>('/listings/all', {
    params: { hours },
  });
  return response.data;
}
