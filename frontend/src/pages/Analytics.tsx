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
  AreaChart,
  Area,
} from 'recharts';

interface PriceSnapshot {
  timestamp: string;
  set_name: string;
  min_price: number | null;
  avg_lowest_2: number | null;
  listings_count: number;
  total_seats: number;
  you_receive: number | null;
  profit_per_ticket: number | null;
  total_profit: number | null;
  quantity: number;
  cost_per_ticket: number;
}

interface HistoryResponse {
  snapshots: PriceSnapshot[];
  last_updated: string | null;
}

interface ProfitDataPoint {
  timestamp: string;
  total_profit: number;
  sets: Record<string, { profit: number | null; price: number | null }>;
}

interface ProfitResponse {
  data: ProfitDataPoint[];
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

async function fetchProfitOverTime(): Promise<ProfitResponse> {
  const response = await api.get('/history/profit-over-time');
  return response.data;
}

async function takeSnapshot(): Promise<void> {
  await api.post('/history/snapshot');
}

export function Analytics() {
  const { data: comparison, isLoading: comparisonLoading } = useComparison();
  const {
    data: history,
    refetch: refetchHistory,
  } = useQuery({
    queryKey: ['history'],
    queryFn: fetchHistory,
    refetchInterval: 5 * 60 * 1000,
  });

  const {
    data: profitData,
    refetch: refetchProfit,
  } = useQuery({
    queryKey: ['profit-over-time'],
    queryFn: fetchProfitOverTime,
    refetchInterval: 5 * 60 * 1000,
  });

  const handleTakeSnapshot = async () => {
    await takeSnapshot();
    refetchHistory();
    refetchProfit();
  };

  // Profit chart data
  const profitChartData = profitData?.data.map((d) => ({
    time: formatTime(d.timestamp),
    'Total Profit': Math.round(d.total_profit),
  })) || [];

  // Price chart data - group by timestamp
  const priceChartData = history?.snapshots
    ? (() => {
        const grouped: Record<string, PriceSnapshot[]> = {};
        history.snapshots.forEach((s) => {
          if (!grouped[s.set_name]) grouped[s.set_name] = [];
          grouped[s.set_name].push(s);
        });

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

  // Calculate current total profit
  const currentTotalProfit = comparison?.summary.total_vivid_profit || 0;

  return (
    <Layout>
      <div className="page-header">
        <div>
          <h1>Analytics</h1>
          <p className="subtitle">Price and profit tracking over time (updates every hour)</p>
        </div>
        <button className="snapshot-btn" onClick={handleTakeSnapshot}>
          Take Snapshot Now
        </button>
      </div>

      {/* Current Total Profit - Big Display */}
      {!comparisonLoading && comparison && (
        <div className="profit-hero">
          <div className="profit-hero-label">Current Total Profit</div>
          <div className={`profit-hero-value ${currentTotalProfit >= 0 ? 'positive' : 'negative'}`}>
            {currentTotalProfit >= 0 ? '+' : ''}{formatCurrency(currentTotalProfit)}
          </div>
          <div className="profit-hero-sub">
            {comparison.summary.total_tickets} tickets | Cost: {formatCurrency(comparison.summary.total_cost)}
          </div>
        </div>
      )}

      {/* Total Profit Over Time Chart */}
      <div className="chart-section">
        <h2>Total Profit Over Time</h2>
        {profitChartData.length > 0 ? (
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={profitChartData}>
                <defs>
                  <linearGradient id="profitGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#059669" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#059669" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="time" tick={{ fontSize: 12 }} />
                <YAxis
                  tickFormatter={(value) => `$${value.toLocaleString()}`}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip
                  formatter={(value: number) => [`$${value.toLocaleString()}`, 'Total Profit']}
                  labelStyle={{ fontWeight: 600 }}
                />
                <Area
                  type="monotone"
                  dataKey="Total Profit"
                  stroke="#059669"
                  strokeWidth={3}
                  fill="url(#profitGradient)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="no-data">
            <p>No profit history yet. Click "Take Snapshot Now" to start tracking.</p>
          </div>
        )}
      </div>

      {/* Price History Chart */}
      <div className="chart-section">
        <h2>Prices by Set Over Time</h2>
        {priceChartData.length > 0 ? (
          <div className="chart-container">
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={priceChartData}>
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
          </div>
        )}
      </div>

      {/* Current Prices by Set */}
      {!comparisonLoading && comparison && (
        <div className="current-prices">
          <h2>Current Prices by Set</h2>
          <div className="price-cards">
            {comparison.sets.map((set) => {
              const profit = set.vivid_you_receive
                ? (set.vivid_you_receive - set.cost_per_ticket) * set.quantity
                : null;

              return (
                <div key={set.set_name} className="price-card" style={{ borderLeftColor: setColors[set.set_name] }}>
                  <div className="price-card-header">
                    <span className="set-name">{set.set_name}</span>
                    <span className="section">{set.section}</span>
                  </div>
                  <div className="price-card-body">
                    <div className="price-row">
                      <span className="label">Qty:</span>
                      <span className="value">{set.quantity}</span>
                    </div>
                    <div className="price-row">
                      <span className="label">Price:</span>
                      <span className="value">{formatCurrency(set.vivid_buyer_price)}</span>
                    </div>
                    <div className="price-row">
                      <span className="label">You Get:</span>
                      <span className="value highlight">{formatCurrency(set.vivid_you_receive)}</span>
                    </div>
                    <div className="price-row profit-row">
                      <span className="label">Profit:</span>
                      <span className={`value ${profit !== null && profit >= 0 ? 'positive' : 'negative'}`}>
                        {profit !== null ? `${profit >= 0 ? '+' : ''}${formatCurrency(profit)}` : '-'}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

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
                  <th>Price</th>
                  <th>You Receive</th>
                  <th>Profit/Ticket</th>
                  <th>Total Profit</th>
                </tr>
              </thead>
              <tbody>
                {history.snapshots.slice(0, 30).map((snapshot, idx) => (
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
                    <td className="price">{formatCurrency(snapshot.you_receive)}</td>
                    <td className={snapshot.profit_per_ticket !== null && snapshot.profit_per_ticket >= 0 ? 'positive' : 'negative'}>
                      {snapshot.profit_per_ticket !== null ? `${snapshot.profit_per_ticket >= 0 ? '+' : ''}${formatCurrency(snapshot.profit_per_ticket)}` : '-'}
                    </td>
                    <td className={`profit ${snapshot.total_profit !== null && snapshot.total_profit >= 0 ? 'positive' : 'negative'}`}>
                      {snapshot.total_profit !== null ? `${snapshot.total_profit >= 0 ? '+' : ''}${formatCurrency(snapshot.total_profit)}` : '-'}
                    </td>
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

        .profit-hero {
          background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
          border-radius: 16px;
          padding: 32px;
          text-align: center;
          margin-bottom: 32px;
          border: 2px solid #059669;
        }
        .profit-hero-label {
          font-size: 14px;
          color: #059669;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 1px;
          margin-bottom: 8px;
        }
        .profit-hero-value {
          font-size: 48px;
          font-weight: 800;
        }
        .profit-hero-value.positive {
          color: #059669;
        }
        .profit-hero-value.negative {
          color: #dc2626;
        }
        .profit-hero-sub {
          font-size: 14px;
          color: #666;
          margin-top: 8px;
        }

        .chart-section {
          background: white;
          border-radius: 12px;
          padding: 24px;
          margin-bottom: 24px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .chart-section h2 {
          font-size: 18px;
          margin: 0 0 20px;
        }
        .chart-container {
          width: 100%;
        }
        .no-data {
          text-align: center;
          padding: 40px;
          color: #666;
        }

        .current-prices {
          margin-bottom: 24px;
        }
        .current-prices h2 {
          font-size: 18px;
          margin: 0 0 16px;
        }
        .price-cards {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
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
          margin-bottom: 12px;
        }
        .set-name {
          font-weight: 700;
          font-size: 16px;
          display: block;
        }
        .section {
          font-size: 12px;
          color: #666;
        }
        .price-row {
          display: flex;
          justify-content: space-between;
          margin-bottom: 4px;
          font-size: 13px;
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
        .profit-row {
          margin-top: 8px;
          padding-top: 8px;
          border-top: 1px solid #e5e7eb;
        }
        .positive {
          color: #059669;
          font-weight: 600;
        }
        .negative {
          color: #dc2626;
          font-weight: 600;
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
        .history-table .profit {
          font-weight: 700;
        }
      `}</style>
    </Layout>
  );
}
