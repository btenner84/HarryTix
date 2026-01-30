import type { Listing } from '../../types/listing';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface ListingsTableProps {
  listings: Listing[] | undefined;
  isLoading: boolean;
  title?: string;
}

export function ListingsTable({ listings, isLoading, title = 'Current Listings' }: ListingsTableProps) {
  const formatCurrency = (amount: number | null | undefined) => {
    if (amount === null || amount === undefined) return '-';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  const getPlatformClass = (platform: string) => {
    return `platform-badge ${platform}`;
  };

  if (isLoading) {
    return <LoadingSpinner text="Loading listings..." />;
  }

  if (!listings?.length) {
    return (
      <div className="loading">
        No listings found. Data will appear after the first price collection.
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">{title}</h3>
        <span className="price-range">{listings.length} listings</span>
      </div>
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Platform</th>
              <th>Section</th>
              <th>Row</th>
              <th>Qty</th>
              <th>Price/Ticket</th>
              <th>Total</th>
              <th>Fetched</th>
            </tr>
          </thead>
          <tbody>
            {listings.slice(0, 20).map((listing) => (
              <tr key={listing.id}>
                <td>
                  <span className={getPlatformClass(listing.platform)}>
                    {listing.platform}
                  </span>
                </td>
                <td>{listing.section || '-'}</td>
                <td>{listing.row || '-'}</td>
                <td>{listing.quantity || '-'}</td>
                <td className="price">{formatCurrency(listing.price_per_ticket)}</td>
                <td className="price">{formatCurrency(listing.total_price)}</td>
                <td className="price-range">{formatTime(listing.fetched_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {listings.length > 20 && (
          <div style={{ padding: '12px', textAlign: 'center', color: '#666' }}>
            Showing 20 of {listings.length} listings
          </div>
        )}
      </div>
    </div>
  );
}
