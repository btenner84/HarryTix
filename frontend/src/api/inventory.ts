import { apiClient } from './client';
import type { InventoryItem } from '../types/inventory';

export async function fetchInventory(): Promise<InventoryItem[]> {
  const response = await apiClient.get<InventoryItem[]>('/inventory');
  return response.data;
}

export async function fetchInventoryItem(id: number): Promise<InventoryItem> {
  const response = await apiClient.get<InventoryItem>(`/inventory/${id}`);
  return response.data;
}
