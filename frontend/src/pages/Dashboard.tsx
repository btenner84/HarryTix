import { Layout } from '../components/layout/Layout';
import { useComparison } from '../hooks/useComparison';

function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return '-';
  return `$${value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

export function Dashboard() {
  const { data, isLoading, error, dataUpdatedAt, refetch, isFetching } = useComparison();

  const lastUpdated = dataUpdatedAt ? new Date(dataUpdatedAt) : null;

  return (
    <Layout>
      <div className="dashboard-header">
        <div>
          <h1>HarryTix Dashboard</h1>
          <p className="subtitle">Live Vivid Seats prices for your {data?.summary.total_tickets || ''} Harry Styles tickets</p>
        </div>
        <div className="refresh-section">
          {lastUpdated && (
            <span className="last-updated">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <button
            className={`refresh-btn ${isFetching ? 'refreshing' : ''}`}
            onClick={() => refetch()}
            disabled={isFetching}
          >
            {isFetching ? 'Refreshing...' : 'Refresh Prices'}
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          Error loading prices. Make sure the backend is running.
        </div>
      )}

      {isLoading ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Fetching live prices from Vivid Seats...</p>
        </div>
      ) : data ? (
        <>
          {/* Summary Cards */}
          <div className="summary-grid">
            <div className="summary-card">
              <span className="summary-card-label">Total Tickets</span>
              <span className="summary-card-value">{data.summary.total_tickets}</span>
            </div>
            <div className="summary-card">
              <span className="summary-card-label">Total Cost</span>
              <span className="summary-card-value">{formatCurrency(data.summary.total_cost)}</span>
            </div>
            <div className="summary-card">
              <span className="summary-card-label">Total Revenue</span>
              <span className="summary-card-value">{formatCurrency(data.summary.total_vivid_revenue)}</span>
            </div>
            <div className="summary-card summary-card-profit">
              <span className="summary-card-label">Total Profit</span>
              <span className="summary-card-value" style={{ color: data.summary.total_vivid_profit >= 0 ? '#059669' : '#dc2626' }}>
                {data.summary.total_vivid_profit >= 0 ? '+' : ''}{formatCurrency(data.summary.total_vivid_profit)}
              </span>
            </div>
          </div>

          {/* Fee Info */}
          <div className="fee-info">
            <span className="fee-badge">Vivid Seats: 10% seller fee</span>
          </div>

          {/* Comparison Table */}
          <h2 className="section-title">Price Breakdown by Set</h2>
          <div className="table-container">
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>Set</th>
                  <th>Date</th>
                  <th>Section</th>
                  <th>Qty</th>
                  <th>Your Cost</th>
                  <th>Buyer Pays</th>
                  <th>You Receive</th>
                  <th>Profit/Ticket</th>
                  <th>Total Profit</th>
                  <th>Market</th>
                </tr>
              </thead>
              <tbody>
                {data.sets.map((set) => {
                  const profitPerTicket = set.vivid_you_receive
                    ? set.vivid_you_receive - set.cost_per_ticket
                    : null;
                  const totalProfit = profitPerTicket
                    ? profitPerTicket * set.quantity
                    : null;

                  return (
                    <tr key={set.set_name}>
                      <td className="cell-set">{set.set_name}</td>
                      <td>{set.date}</td>
                      <td className="cell-section">{set.section}</td>
                      <td className="cell-center">{set.quantity}</td>
                      <td>{formatCurrency(set.cost_per_ticket)}</td>
                      <td className="cell-highlight">{formatCurrency(set.vivid_buyer_price)}</td>
                      <td className="cell-highlight">{formatCurrency(set.vivid_you_receive)}</td>
                      <td className={profitPerTicket !== null ? (profitPerTicket >= 0 ? 'cell-positive' : 'cell-negative') : ''}>
                        {profitPerTicket !== null ? `${profitPerTicket >= 0 ? '+' : ''}${formatCurrency(profitPerTicket)}` : '-'}
                      </td>
                      <td className={`cell-total-profit ${totalProfit !== null ? (totalProfit >= 0 ? 'cell-positive' : 'cell-negative') : ''}`}>
                        {totalProfit !== null ? `${totalProfit >= 0 ? '+' : ''}${formatCurrency(totalProfit)}` : '-'}
                      </td>
                      <td className="cell-market">
                        {set.vivid_market && set.vivid_market.listings_count > 0 ? (
                          <a
                            href={`https://www.vividseats.com/production/${set.vivid_event_id}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="market-link"
                          >
                            <span className="market-count">{set.vivid_market.listings_count} listings</span>
                            <span className="market-seats">{set.vivid_market.total_seats} seats</span>
                            <span className="market-arrow">↗</span>
                          </a>
                        ) : '-'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr className="totals-row">
                  <td colSpan={3}><strong>TOTAL</strong></td>
                  <td className="cell-center"><strong>{data.summary.total_tickets}</strong></td>
                  <td><strong>{formatCurrency(data.summary.total_cost)}</strong></td>
                  <td colSpan={3}></td>
                  <td className={`cell-total-profit ${data.summary.total_vivid_profit >= 0 ? 'cell-positive' : 'cell-negative'}`}>
                    <strong>{data.summary.total_vivid_profit >= 0 ? '+' : ''}{formatCurrency(data.summary.total_vivid_profit)}</strong>
                  </td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>

          {/* Grouped by Product Type */}
          <h2 className="section-title">By Product Type</h2>
          {(() => {
            // Group sets by product type
            const groups: Record<string, typeof data.sets> = {
              'GA / Pit': [],
              'Lower Bowl (100s)': [],
              'Upper Bowl (200s)': [],
            };

            // Date sort helper
            const dateOrder: Record<string, number> = {
              'Aug 28': 1, 'Sept 2': 2, 'Sept 18': 3, 'Sept 19': 4, 'Sept 25': 5,
              'Oct 9': 6, 'Oct 17': 7, 'Oct 31': 8
            };

            data.sets.forEach(set => {
              const section = set.section.toUpperCase();
              if (section.includes('GA') || section.includes('PIT')) {
                groups['GA / Pit'].push(set);
              } else if (section.includes('200') || section.includes('SECTION 2')) {
                groups['Upper Bowl (200s)'].push(set);
              } else {
                groups['Lower Bowl (100s)'].push(set);
              }
            });

            // Sort each group by date
            Object.values(groups).forEach(group => {
              group.sort((a, b) => (dateOrder[a.date] || 99) - (dateOrder[b.date] || 99));
            });

            return (
              <div className="product-groups">
                {Object.entries(groups).map(([groupName, sets]) => {
                  if (sets.length === 0) return null;

                  const groupQty = sets.reduce((sum, s) => sum + s.quantity, 0);
                  const groupCost = sets.reduce((sum, s) => sum + s.cost_per_ticket * s.quantity, 0);
                  const groupProfit = sets.reduce((sum, s) => {
                    const profit = s.vivid_you_receive ? (s.vivid_you_receive - s.cost_per_ticket) * s.quantity : 0;
                    return sum + profit;
                  }, 0);

                  return (
                    <div key={groupName} className="product-group">
                      <div className="group-header">
                        <span className="group-name">{groupName}</span>
                        <span className="group-stats">
                          {groupQty} tickets · {formatCurrency(groupCost)} cost ·
                          <span className={groupProfit >= 0 ? 'cell-positive' : 'cell-negative'}>
                            {' '}{groupProfit >= 0 ? '+' : ''}{formatCurrency(groupProfit)} profit
                          </span>
                        </span>
                      </div>
                      <table className="group-table">
                        <thead>
                          <tr>
                            <th>Set</th>
                            <th>Date</th>
                            <th>Section</th>
                            <th>Qty</th>
                            <th>Cost</th>
                            <th>Price</th>
                            <th>You Get</th>
                            <th>Profit</th>
                          </tr>
                        </thead>
                        <tbody>
                          {sets.map(set => {
                            const profitPerTicket = set.vivid_you_receive
                              ? set.vivid_you_receive - set.cost_per_ticket
                              : null;
                            const totalProfit = profitPerTicket ? profitPerTicket * set.quantity : null;

                            return (
                              <tr key={set.set_name}>
                                <td className="cell-set">{set.set_name}</td>
                                <td>{set.date}</td>
                                <td>{set.section}</td>
                                <td className="cell-center">{set.quantity}</td>
                                <td>{formatCurrency(set.cost_per_ticket)}</td>
                                <td className="cell-highlight">{formatCurrency(set.vivid_buyer_price)}</td>
                                <td className="cell-highlight">{formatCurrency(set.vivid_you_receive)}</td>
                                <td className={totalProfit !== null ? (totalProfit >= 0 ? 'cell-positive' : 'cell-negative') : ''}>
                                  {totalProfit !== null ? `${totalProfit >= 0 ? '+' : ''}${formatCurrency(totalProfit)}` : '-'}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  );
                })}
              </div>
            );
          })()}

          {/* Source Info */}
          <div className="source-info">
            <p><strong>Data Source:</strong> Vivid Seats Live API - filtered to your exact sections</p>
          </div>
        </>
      ) : (
        <div className="empty-state">
          <p>No data available. Make sure the backend is running.</p>
        </div>
      )}

      <style>{`
        .dashboard-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 32px;
        }

        .dashboard-header h1 {
          margin: 0;
          font-size: 28px;
          font-weight: 700;
        }

        .subtitle {
          color: #666;
          margin: 4px 0 0;
        }

        .refresh-section {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .last-updated {
          color: #888;
          font-size: 13px;
        }

        .refresh-btn {
          background: #2563eb;
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 8px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
        }

        .refresh-btn:hover:not(:disabled) {
          background: #1d4ed8;
        }

        .refresh-btn:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        .refresh-btn.refreshing {
          animation: pulse 1s infinite;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }

        .error-banner {
          background: #fef2f2;
          border: 1px solid #fecaca;
          color: #dc2626;
          padding: 12px 16px;
          border-radius: 8px;
          margin-bottom: 24px;
        }

        .loading-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 80px 20px;
        }

        .loading-spinner {
          width: 48px;
          height: 48px;
          border: 4px solid #e5e7eb;
          border-top-color: #2563eb;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .summary-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 16px;
          margin-bottom: 24px;
        }

        @media (max-width: 900px) {
          .summary-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        .summary-card {
          background: white;
          border-radius: 12px;
          padding: 20px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .summary-card-label {
          display: block;
          font-size: 13px;
          color: #666;
          margin-bottom: 8px;
        }

        .summary-card-value {
          display: block;
          font-size: 24px;
          font-weight: 700;
        }

        .summary-card-profit {
          background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
          border-left: 4px solid #059669;
        }

        .fee-info {
          display: flex;
          gap: 16px;
          margin-bottom: 24px;
        }

        .fee-badge {
          padding: 6px 12px;
          border-radius: 6px;
          font-size: 13px;
          font-weight: 500;
          background: #dbeafe;
          color: #1d4ed8;
        }

        .section-title {
          font-size: 20px;
          font-weight: 600;
          margin: 32px 0 16px;
        }

        .table-container {
          overflow-x: auto;
          background: white;
          border-radius: 12px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .comparison-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 14px;
        }

        .comparison-table th,
        .comparison-table td {
          padding: 12px 16px;
          text-align: left;
          border-bottom: 1px solid #e5e7eb;
          white-space: nowrap;
        }

        .comparison-table th {
          background: #f9fafb;
          font-weight: 600;
          color: #374151;
        }

        .comparison-table tbody tr:hover {
          background: #f9fafb;
        }

        .cell-set {
          font-weight: 600;
        }

        .cell-section {
          font-weight: 500;
        }

        .cell-center {
          text-align: center;
        }

        .cell-highlight {
          font-weight: 600;
          color: #2563eb;
        }

        .cell-positive {
          color: #059669;
          font-weight: 600;
        }

        .cell-negative {
          color: #dc2626;
          font-weight: 600;
        }

        .cell-total-profit {
          font-weight: 700;
          font-size: 15px;
        }

        .cell-market {
          font-size: 12px;
        }

        .market-link {
          display: flex;
          flex-direction: column;
          gap: 2px;
          text-decoration: none;
          padding: 4px 8px;
          border-radius: 6px;
          transition: background 0.2s;
        }

        .market-link:hover {
          background: #dbeafe;
        }

        .market-count {
          font-weight: 600;
          color: #2563eb;
        }

        .market-seats {
          color: #666;
        }

        .market-arrow {
          font-size: 10px;
          color: #2563eb;
        }

        .totals-row {
          background: #f9fafb;
        }

        .totals-row td {
          border-bottom: none;
          padding-top: 16px;
          padding-bottom: 16px;
        }

        .source-info {
          margin-top: 24px;
          padding: 16px;
          background: #f9fafb;
          border-radius: 8px;
          font-size: 13px;
          color: #666;
        }

        .empty-state {
          text-align: center;
          padding: 60px 20px;
          color: #666;
        }

        .product-groups {
          display: flex;
          flex-direction: column;
          gap: 24px;
        }

        .product-group {
          background: white;
          border-radius: 12px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
          overflow: hidden;
        }

        .group-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 20px;
          background: #f9fafb;
          border-bottom: 1px solid #e5e7eb;
        }

        .group-name {
          font-weight: 700;
          font-size: 16px;
        }

        .group-stats {
          font-size: 13px;
          color: #666;
        }

        .group-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 14px;
        }

        .group-table th,
        .group-table td {
          padding: 10px 16px;
          text-align: left;
          border-bottom: 1px solid #e5e7eb;
        }

        .group-table th {
          background: #fafafa;
          font-weight: 600;
          color: #374151;
          font-size: 12px;
          text-transform: uppercase;
        }

        .group-table tbody tr:last-child td {
          border-bottom: none;
        }

        .group-table tbody tr:hover {
          background: #f9fafb;
        }
      `}</style>
    </Layout>
  );
}
