import { Layout } from '../components/layout/Layout';
import { useComparison, TicketSet, VividMarketData } from '../hooks/useComparison';

function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return '-';
  return `$${value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

function ProfitCell({ value }: { value: number | null }) {
  if (value === null) return <td className="cell-neutral">-</td>;
  const isPositive = value >= 0;
  return (
    <td className={isPositive ? 'cell-positive' : 'cell-negative'}>
      {isPositive ? '+' : ''}{formatCurrency(value)}
    </td>
  );
}

function BestPlatformBadge({ platform, vividReceive, stubhubReceive }: {
  platform: string | null;
  vividReceive: number | null;
  stubhubReceive: number | null;
}) {
  if (!platform) return <span className="badge badge-neutral">-</span>;

  const isVivid = platform === 'Vivid';
  const diff = vividReceive && stubhubReceive ? Math.abs(vividReceive - stubhubReceive) : 0;

  return (
    <span className={`badge ${isVivid ? 'badge-vivid' : 'badge-stubhub'}`}>
      {platform} {diff > 0 && `(+$${diff.toFixed(0)})`}
    </span>
  );
}

function MarketDataCell({ market }: { market: VividMarketData | null }) {
  if (!market || market.listings_count === 0) {
    return <td className="cell-market">-</td>;
  }

  return (
    <td className="cell-market">
      <div className="market-info">
        <span className="market-count">{market.listings_count} listings</span>
        <span className="market-seats">{market.total_seats} seats</span>
        {market.min_price && market.max_price && (
          <span className="market-range">
            ${market.min_price.toLocaleString()}-${market.max_price.toLocaleString()}
          </span>
        )}
      </div>
    </td>
  );
}

function ComparisonTable({ sets }: { sets: TicketSet[] }) {
  return (
    <div className="table-container">
      <table className="comparison-table">
        <thead>
          <tr>
            <th>Set</th>
            <th>Date</th>
            <th>Section</th>
            <th>Qty</th>
            <th>Your Cost</th>
            <th className="col-vivid">Vivid Buyer</th>
            <th className="col-vivid">Vivid You Get</th>
            <th className="col-stubhub">StubHub Buyer</th>
            <th className="col-stubhub">StubHub You Get</th>
            <th>Avg You Get</th>
            <th>Profit/Tix</th>
            <th>Best</th>
            <th>Market (Vivid)</th>
          </tr>
        </thead>
        <tbody>
          {sets.map((set) => (
            <tr key={set.set_name}>
              <td className="cell-set">{set.set_name}</td>
              <td>{set.date}</td>
              <td className="cell-section">{set.section}</td>
              <td className="cell-center">{set.quantity}</td>
              <td>{formatCurrency(set.cost_per_ticket)}</td>
              <td className="col-vivid">{formatCurrency(set.vivid_buyer_price)}</td>
              <td className="col-vivid cell-highlight">{formatCurrency(set.vivid_you_receive)}</td>
              <td className="col-stubhub">{formatCurrency(set.stubhub_buyer_price)}</td>
              <td className="col-stubhub cell-highlight">{formatCurrency(set.stubhub_you_receive)}</td>
              <td className="cell-avg">{formatCurrency(set.avg_you_receive)}</td>
              <ProfitCell value={set.profit_per_ticket} />
              <td>
                <BestPlatformBadge
                  platform={set.best_platform}
                  vividReceive={set.vivid_you_receive}
                  stubhubReceive={set.stubhub_you_receive}
                />
              </td>
              <MarketDataCell market={set.vivid_market} />
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Dashboard() {
  const { data, isLoading, error, dataUpdatedAt, refetch, isFetching } = useComparison();

  const lastUpdated = dataUpdatedAt ? new Date(dataUpdatedAt) : null;

  return (
    <Layout>
      <div className="dashboard-header">
        <div>
          <h1>HarryTix Dashboard</h1>
          <p className="subtitle">Live price tracking for your 27 Harry Styles tickets</p>
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
          <p>Fetching live prices from Vivid Seats & StubHub...</p>
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
            <div className="summary-card summary-card-vivid">
              <span className="summary-card-label">Vivid Seats Profit</span>
              <span className="summary-card-value">{formatCurrency(data.summary.total_vivid_profit)}</span>
            </div>
            <div className="summary-card summary-card-stubhub">
              <span className="summary-card-label">StubHub Profit</span>
              <span className="summary-card-value">{formatCurrency(data.summary.total_stubhub_profit)}</span>
            </div>
          </div>

          {/* Fee Info */}
          <div className="fee-info">
            <span className="fee-badge fee-vivid">Vivid: 10% seller fee</span>
            <span className="fee-badge fee-stubhub">StubHub: 15% seller fee</span>
          </div>

          {/* Comparison Table */}
          <h2 className="section-title">Price Comparison by Set</h2>
          <ComparisonTable sets={data.sets} />

          {/* Legend */}
          <div className="legend">
            <div className="legend-item">
              <span className="legend-color legend-vivid"></span>
              <span>Vivid Seats (10% fee)</span>
            </div>
            <div className="legend-item">
              <span className="legend-color legend-stubhub"></span>
              <span>StubHub (15% fee)</span>
            </div>
            <div className="legend-item">
              <span className="legend-note">All prices are ALL-IN (buyer pays, incl. fees)</span>
            </div>
          </div>

          {/* Source Info */}
          <div className="source-info">
            <h3>Data Sources</h3>
            <ul>
              <li><strong>Vivid Seats:</strong> Live API - filtered to your exact sections</li>
              <li><strong>StubHub:</strong> Verified from venue map screenshots</li>
            </ul>
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

        .summary-card-vivid {
          background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
          border-left: 4px solid #2563eb;
        }

        .summary-card-vivid .summary-card-value {
          color: #1d4ed8;
        }

        .summary-card-stubhub {
          background: linear-gradient(135deg, #fdf4ff 0%, #f3e8ff 100%);
          border-left: 4px solid #9333ea;
        }

        .summary-card-stubhub .summary-card-value {
          color: #7c3aed;
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
        }

        .fee-vivid {
          background: #dbeafe;
          color: #1d4ed8;
        }

        .fee-stubhub {
          background: #f3e8ff;
          color: #7c3aed;
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
          position: sticky;
          top: 0;
        }

        .comparison-table tbody tr:hover {
          background: #f9fafb;
        }

        .col-vivid {
          background: #eff6ff !important;
        }

        .col-stubhub {
          background: #fdf4ff !important;
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
        }

        .cell-avg {
          font-weight: 700;
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

        .cell-neutral {
          color: #666;
        }

        .badge {
          display: inline-block;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 600;
        }

        .badge-vivid {
          background: #dbeafe;
          color: #1d4ed8;
        }

        .badge-stubhub {
          background: #f3e8ff;
          color: #7c3aed;
        }

        .badge-neutral {
          background: #f3f4f6;
          color: #666;
        }

        .legend {
          display: flex;
          gap: 24px;
          margin-top: 16px;
          padding: 12px 16px;
          background: #f9fafb;
          border-radius: 8px;
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 13px;
        }

        .legend-color {
          width: 16px;
          height: 16px;
          border-radius: 4px;
        }

        .legend-vivid {
          background: #dbeafe;
        }

        .legend-stubhub {
          background: #f3e8ff;
        }

        .legend-note {
          color: #666;
          font-style: italic;
        }

        .source-info {
          margin-top: 32px;
          padding: 20px;
          background: #f9fafb;
          border-radius: 12px;
        }

        .source-info h3 {
          margin: 0 0 12px;
          font-size: 16px;
        }

        .source-info ul {
          margin: 0;
          padding-left: 20px;
        }

        .source-info li {
          margin-bottom: 8px;
          color: #666;
        }

        .source-info strong {
          color: #374151;
        }

        .empty-state {
          text-align: center;
          padding: 60px 20px;
          color: #666;
        }

        .cell-market {
          font-size: 12px;
        }

        .market-info {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .market-count {
          font-weight: 600;
          color: #2563eb;
        }

        .market-seats {
          color: #666;
        }

        .market-range {
          color: #888;
          font-size: 11px;
        }
      `}</style>
    </Layout>
  );
}
