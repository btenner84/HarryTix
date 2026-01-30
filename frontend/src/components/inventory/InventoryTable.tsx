import type { InventoryItem } from '../../types/inventory';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface InventoryTableProps {
  items: InventoryItem[] | undefined;
  isLoading: boolean;
}

export function InventoryTable({ items, isLoading }: InventoryTableProps) {
  const formatCurrency = (amount: number | null | undefined) => {
    if (amount === null || amount === undefined) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  if (isLoading) {
    return <LoadingSpinner text="Loading inventory..." />;
  }

  if (!items?.length) {
    return <div className="loading">No inventory items found.</div>;
  }

  // Calculate totals
  const totals = items.reduce(
    (acc, item) => ({
      quantity: acc.quantity + item.quantity,
      cost: acc.cost + item.total_cost,
      revenue: acc.revenue + (item.expected_revenue || 0),
      profit: acc.profit + (item.expected_profit || 0),
    }),
    { quantity: 0, cost: 0, revenue: 0, profit: 0 }
  );

  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th>Set</th>
            <th>Section</th>
            <th>Row</th>
            <th>Seats</th>
            <th>Qty</th>
            <th>Cost/Ticket</th>
            <th>Total Cost</th>
            <th>Market Price</th>
            <th>Expected Revenue</th>
            <th>Profit</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const profit = item.expected_profit;
            const profitClass = profit && profit > 0 ? 'positive' : profit && profit < 0 ? 'negative' : '';

            return (
              <tr key={item.id}>
                <td><strong>{item.notes}</strong></td>
                <td>{item.section}</td>
                <td>{item.row || '-'}</td>
                <td>{item.seat_numbers || '-'}</td>
                <td>{item.quantity}</td>
                <td className="price">{formatCurrency(item.cost_per_ticket)}</td>
                <td className="price">{formatCurrency(item.total_cost)}</td>
                <td>
                  <span className="price">{formatCurrency(item.avg_market_price)}</span>
                  {item.comparable_listings_count > 0 && (
                    <div className="price-range">
                      {formatCurrency(item.min_market_price)} - {formatCurrency(item.max_market_price)}
                      <br />
                      <small>({item.comparable_listings_count} listings)</small>
                    </div>
                  )}
                </td>
                <td className="price">{formatCurrency(item.expected_revenue)}</td>
                <td className={`price ${profitClass}`}>
                  {formatCurrency(profit)}
                </td>
              </tr>
            );
          })}
        </tbody>
        <tfoot>
          <tr style={{ fontWeight: 'bold', background: '#f0f0f0' }}>
            <td colSpan={4}>TOTAL</td>
            <td>{totals.quantity}</td>
            <td>-</td>
            <td className="price">{formatCurrency(totals.cost)}</td>
            <td>-</td>
            <td className="price">{formatCurrency(totals.revenue)}</td>
            <td className={`price ${totals.profit > 0 ? 'positive' : 'negative'}`}>
              {formatCurrency(totals.profit)}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
