import { useQuery } from '@tanstack/react-query';
import { fetchInventory, fetchInventoryItem } from '../api/inventory';

export function useInventory() {
  return useQuery({
    queryKey: ['inventory'],
    queryFn: fetchInventory,
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
    staleTime: 60 * 1000, // Consider stale after 1 minute
  });
}

export function useInventoryItem(id: number) {
  return useQuery({
    queryKey: ['inventory', id],
    queryFn: () => fetchInventoryItem(id),
    refetchInterval: 5 * 60 * 1000,
  });
}
