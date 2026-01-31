import { useQuery } from '@tanstack/react-query';
import { Layout } from '../components/layout/Layout';
import { useComparison } from '../hooks/useComparison';
import { api } from '../api/client';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface PriceSnapshot {
  timestamp: string;
  set_name: string;
  min_price: number | null;
  avg_lowest_2: number | null;
  listings_count: number;
  total_seats: number;
}

interface HistoryResponse {
  snapshots: PriceSnapshot[];
  last_updated: string | null;
}

function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return '-';
  return `$${value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

function formatTime(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

async function fetchHistory(): Promise<HistoryResponse> {
  const response = await api.get('/history');
  return response.data;
}

async function takeSnapshot(): Promise<void> {
  await api.post('/history/snapshot');
}

export function Analytics() {
  const { data: comparison, isLoading: comparisonLoading } = useComparison();
  const {
    data: history,
    isLoading: historyLoading,
    refetch: refetchHistory,
  } = useQuery({
    queryKey: ['history'],
    queryFn: fetchHistory,
    refetchInterval: 5 * 60 * 1000,
  });

  const handleTakeSnapshot = async () => {
    await takeSnapshot();
    refetchHistory();
  };

  // Group snapshots by set for the chart
  const chartData = history?.snapshots
    ? (() => {
        const grouped: Record<string, PriceSnapshot[]> = {};
        history.snapshots.forEach((s) => {
          if (!grouped[s.set_name]) grouped[s.set_name] = [];
          grouped[s.set_name].push(s);
        });

        // Get all unique timestamps and create chart data
        const timestamps = [...new Set(history.snapshots.map((s) => s.timestamp))].sort();
        return timestamps.map((ts) => {
          const point: Record<string, any> = { time: formatTime(ts) };
          Object.keys(grouped).forEach((setName) => {
            const snapshot = grouped[setName].find((s) => s.timestamp === ts);
            if (snapshot) {
              point[setName] = snapshot.avg_lowest_2;
            }
          });
          return point;
        });
      })()
    : [];

  const setColors: Record<string, string> = {
    'Set A': '#2563eb',
    'Set B': '#059669',
    'Set C': '#d97706',
    'Set D': '#7c3aed',
    'Set E': '#dc2626',
  };

  return (
    <Layout>
      <div className="page-header">
        <div>
          <h1>Analytics</h1>
          <p className="subtitle">Price history and trends over time</p>
        </div>
        <button className="snapshot-btn" onClick={handleTakeSnapshot}>
          Take Snapshot Now
        </button>
      </div>

      {/* Current Prices Summary */}
      {!comparisonLoading && comparison && (
        <div className="current-prices">
          <h2>Current Prices</h2>
          <div className="price-cards">
            {comparison.sets.map((set) => (
              <div key={set.set_name} className="price-card" style={{ borderLeftColor: setColors[set.set_name] }}>
                <div className="price-card-header">
                  <span className="set-name">{set.set_name}</span>
                  <span className="section">{set.section}</span>
                </div>
                <div className="price-card-body">
                  <div className="price-row">
                    <span className="label">Buyer Pays:</span>
                    <span className="value">{formatCurrency(set.vivid_buyer_price)}</span>
                  </div>
                  <div className="price-row">
                    <span className="label">You Receive:</span>
                    <span className="value highlight">{formatCurrency(set.vivid_you_receive)}</span>
                  </div>
                  <div className="price-row">
                    <span className="label">Listings:</span>
                    <span className="value">{set.vivid_market?.listings_count || 0}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Price History Chart */}
      <div className="chart-section">
        <h2>Price History</h2>
        {historyLoading ? (
          <div className="loading">Loading history...</div>
        ) : chartData.length > 0 ? (
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="time" tick={{ fontSize: 12 }} />
                <YAxis
                  tickFormatter={(value) => `$${value}`}
                  tick={{ fontSize: 12 }}
                  domain={['auto', 'auto']}
                />
                <Tooltip
                  formatter={(value: number) => [`$${value?.toFixed(0)}`, '']}
                  labelStyle={{ fontWeight: 600 }}
                />
                <Legend />
                {Object.keys(setColors).map((setName) => (
                  <Line
                    key={setName}
                    type="monotone"
                    dataKey={setName}
                    stroke={setColors[setName]}
                    strokeWidth={2}
                    dot={{ r: 4 }}
                    connectNulls
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="no-data">
            <p>No price history yet.</p>
            <p>Click "Take Snapshot Now" to start tracking, or wait for the hourly automatic snapshot.</p>
          </div>
        )}
      </div>

      {/* History Table */}
      {history && history.snapshots.length > 0 && (
        <div className="history-table-section">
          <h2>Recent Snapshots</h2>
          <div className="table-container">
            <table className="history-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Set</th>
                  <th>Avg Price</th>
                  <th>Min Price</th>
                  <th>Listings</th>
                  <th>Seats</th>
                </tr>
              </thead>
              <tbody>
                {history.snapshots.slice(0, 25).map((snapshot, idx) => (
                  <tr key={idx}>
                    <td>{formatTime(snapshot.timestamp)}</td>
                    <td>
                      <span
                        className="set-badge"
                        style={{ background: setColors[snapshot.set_name] + '20', color: setColors[snapshot.set_name] }}
                      >
                        {snapshot.set_name}
                      </span>
                    </td>
                    <td className="price">{formatCurrency(snapshot.avg_lowest_2)}</td>
                    <td className="price">{formatCurrency(snapshot.min_price)}</td>
                    <td>{snapshot.listings_count}</td>
                    <td>{snapshot.total_seats}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <style>{`
        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 32px;
        }
        .page-header h1 {
          margin: 0;
          font-size: 28px;
          font-weight: 700;
        }
        .subtitle {
          color: #666;
          margin: 4px 0 0;
        }
        .snapshot-btn {
          background: #2563eb;
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 8px;
          font-weight: 500;
          cursor: pointer;
        }
        .snapshot-btn:hover {
          background: #1d4ed8;
        }

        .current-prices {
          margin-bottom: 32px;
        }
        .current-prices h2 {
          font-size: 18px;
          margin: 0 0 16px;
        }
        .price-cards {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
          gap: 16px;
        }
        .price-card {
          background: white;
          border-radius: 8px;
          padding: 16px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
          border-left: 4px solid #2563eb;
        }
        .price-card-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 12px;
        }
        .set-name {
          font-weight: 700;
          font-size: 16px;
        }
        .section {
          font-size: 12px;
          color: #666;
        }
        .price-row {
          display: flex;
          justify-content: space-between;
          margin-bottom: 6px;
          font-size: 14px;
        }
        .price-row .label {
          color: #666;
        }
        .price-row .value {
          font-weight: 600;
        }
        .price-row .highlight {
          color: #2563eb;
        }

        .chart-section {
          background: white;
          border-radius: 12px;
          padding: 24px;
          margin-bottom: 32px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .chart-section h2 {
          font-size: 18px;
          margin: 0 0 20px;
        }
        .chart-container {
          width: 100%;
          height: 400px;
        }
        .loading, .no-data {
          text-align: center;
          padding: 60px;
          color: #666;
        }
        .no-data p {
          margin: 8px 0;
        }

        .history-table-section {
          background: white;
          border-radius: 12px;
          padding: 24px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .history-table-section h2 {
          font-size: 18px;
          margin: 0 0 16px;
        }
        .table-container {
          overflow-x: auto;
        }
        .history-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 14px;
        }
        .history-table th,
        .history-table td {
          padding: 10px 12px;
          text-align: left;
          border-bottom: 1px solid #e5e7eb;
        }
        .history-table th {
          background: #f9fafb;
          font-weight: 600;
        }
        .set-badge {
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 600;
        }
        .history-table .price {
          font-weight: 600;
        }
      `}</style>
    </Layout>
  );
}
