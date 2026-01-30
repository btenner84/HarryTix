import { useQuery } from '@tanstack/react-query';
import { fetchCurrentListings, fetchComparableListings, fetchAllRecentListings } from '../api/listings';

export function useCurrentListings(eventId: number | undefined) {
  return useQuery({
    queryKey: ['listings', 'current', eventId],
    queryFn: () => fetchCurrentListings(eventId!),
    enabled: !!eventId,
    refetchInterval: 5 * 60 * 1000,
    staleTime: 60 * 1000,
  });
}

export function useComparableListings(inventoryId: number | undefined) {
  return useQuery({
    queryKey: ['listings', 'comparable', inventoryId],
    queryFn: () => fetchComparableListings(inventoryId!),
    enabled: !!inventoryId,
    refetchInterval: 5 * 60 * 1000,
  });
}

export function useAllRecentListings(hours: number = 24) {
  return useQuery({
    queryKey: ['listings', 'recent', hours],
    queryFn: () => fetchAllRecentListings(hours),
    refetchInterval: 5 * 60 * 1000,
  });
}
