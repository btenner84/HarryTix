import { Layout } from '../components/layout/Layout';
import { InventoryTable } from '../components/inventory/InventoryTable';
import { ListingsTable } from '../components/listings/ListingsTable';
import { useInventory } from '../hooks/useInventory';
import { useAllRecentListings } from '../hooks/useListings';

export function Inventory() {
  const { data: inventory, isLoading: inventoryLoading } = useInventory();
  const { data: listings, isLoading: listingsLoading } = useAllRecentListings(24);

  // Calculate totals
  const totalTickets = inventory?.reduce((sum, item) => sum + item.quantity, 0) || 0;
  const totalCost = inventory?.reduce((sum, item) => sum + item.total_cost, 0) || 0;

  return (
    <Layout>
      <div style={{ marginBottom: '24px' }}>
        <h2>Inventory Management</h2>
        <p style={{ color: '#666' }}>
          {totalTickets} tickets across {inventory?.length || 0} sets | Total investment: ${totalCost.toLocaleString()}
        </p>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Your Tickets</h3>
        </div>
        <InventoryTable items={inventory} isLoading={inventoryLoading} />
      </div>

      <ListingsTable
        listings={listings}
        isLoading={listingsLoading}
        title="Recent Market Listings (Last 24 Hours)"
      />
    </Layout>
  );
}
