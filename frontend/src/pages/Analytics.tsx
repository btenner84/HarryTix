import { useState } from 'react';
import { Layout } from '../components/layout/Layout';
import { PriceChart } from '../components/analytics/PriceChart';
import { RevenueCard } from '../components/analytics/RevenueCard';
import { useInventory } from '../hooks/useInventory';
import { useRevenueAnalytics, usePriceHistory, usePlatformComparison } from '../hooks/useAnalytics';

export function Analytics() {
  const { data: inventory } = useInventory();
  const { data: analytics, isLoading: analyticsLoading } = useRevenueAnalytics();

  // Event selector for charts
  const events = [...new Set(inventory?.map((i) => i.event_id) || [])];
  const [selectedEventId, setSelectedEventId] = useState<number | undefined>(events[0]);

  const { data: priceHistory, isLoading: historyLoading } = usePriceHistory(selectedEventId);
  const { data: platformComparison } = usePlatformComparison(selectedEventId);

  return (
    <Layout>
      <div style={{ marginBottom: '24px' }}>
        <h2>Analytics</h2>
        <p style={{ color: '#666' }}>
          Price trends and revenue projections
        </p>
      </div>

      {/* Revenue Overview */}
      <div className="stats-grid">
        <RevenueCard
          title="Total Cost Basis"
          value={analytics?.total_cost_basis}
          isLoading={analyticsLoading}
        />
        <RevenueCard
          title="Expected Revenue (Min)"
          value={analytics?.expected_revenue_min}
          isLoading={analyticsLoading}
        />
        <RevenueCard
          title="Expected Revenue (Avg)"
          value={analytics?.expected_revenue_avg}
          isLoading={analyticsLoading}
        />
        <RevenueCard
          title="Expected Revenue (Max)"
          value={analytics?.expected_revenue_max}
          isLoading={analyticsLoading}
        />
      </div>

      {/* Event Selector */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <label style={{ fontWeight: '600' }}>Select Event:</label>
          <select
            value={selectedEventId || ''}
            onChange={(e) => setSelectedEventId(Number(e.target.value))}
            style={{
              padding: '8px 12px',
              borderRadius: '4px',
              border: '1px solid #ddd',
              fontSize: '14px',
            }}
          >
            {events.map((eventId) => {
              const eventInventory = inventory?.find((i) => i.event_id === eventId);
              return (
                <option key={eventId} value={eventId}>
                  Event {eventId} - {eventInventory?.section}
                </option>
              );
            })}
          </select>
        </div>
      </div>

      {/* Price History Chart */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <h3 className="card-title">Price History (30 Days)</h3>
        </div>
        <PriceChart data={priceHistory?.history} isLoading={historyLoading} />
      </div>

      {/* Platform Comparison */}
      {platformComparison && platformComparison.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Platform Comparison</h3>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Platform</th>
                  <th>Avg Price</th>
                  <th>Min Price</th>
                  <th>Max Price</th>
                  <th>Listings</th>
                </tr>
              </thead>
              <tbody>
                {platformComparison.map((platform) => (
                  <tr key={platform.platform}>
                    <td>
                      <span className={`platform-badge ${platform.platform}`}>
                        {platform.platform}
                      </span>
                    </td>
                    <td className="price">
                      {platform.avg_price ? `$${platform.avg_price.toLocaleString()}` : '-'}
                    </td>
                    <td className="price">
                      {platform.min_price ? `$${platform.min_price.toLocaleString()}` : '-'}
                    </td>
                    <td className="price">
                      {platform.max_price ? `$${platform.max_price.toLocaleString()}` : '-'}
                    </td>
                    <td>{platform.listing_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Profit Projections by Ticket Set */}
      <div className="card" style={{ marginTop: '24px' }}>
        <div className="card-header">
          <h3 className="card-title">Profit Projections by Set</h3>
        </div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Set</th>
                <th>Section</th>
                <th>Qty</th>
                <th>Cost Basis</th>
                <th>Market Price</th>
                <th>Expected Revenue</th>
                <th>Profit</th>
                <th>Margin</th>
              </tr>
            </thead>
            <tbody>
              {inventory?.map((item) => {
                const margin = item.expected_profit && item.total_cost
                  ? ((item.expected_profit / item.total_cost) * 100).toFixed(1)
                  : null;

                return (
                  <tr key={item.id}>
                    <td><strong>{item.notes}</strong></td>
                    <td>{item.section}</td>
                    <td>{item.quantity}</td>
                    <td className="price">${item.total_cost.toLocaleString()}</td>
                    <td className="price">
                      {item.avg_market_price ? `$${item.avg_market_price.toLocaleString()}` : '-'}
                    </td>
                    <td className="price">
                      {item.expected_revenue ? `$${item.expected_revenue.toLocaleString()}` : '-'}
                    </td>
                    <td className={`price ${item.expected_profit && item.expected_profit > 0 ? 'positive' : 'negative'}`}>
                      {item.expected_profit ? `$${item.expected_profit.toLocaleString()}` : '-'}
                    </td>
                    <td className={margin && parseFloat(margin) > 0 ? 'positive' : 'negative'}>
                      {margin ? `${margin}%` : '-'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
}
