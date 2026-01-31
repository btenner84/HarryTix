import { Layout } from '../components/layout/Layout';
import { useComparison } from '../hooks/useComparison';

function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return '-';
  return `$${value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

export function Analytics() {
  const { data, isLoading } = useComparison();

  if (isLoading) {
    return (
      <Layout>
        <div style={{ textAlign: 'center', padding: '80px' }}>Loading...</div>
      </Layout>
    );
  }

  if (!data) {
    return (
      <Layout>
        <div style={{ textAlign: 'center', padding: '80px', color: '#666' }}>No data available</div>
      </Layout>
    );
  }

  const { summary } = data;

  return (
    <Layout>
      <div style={{ marginBottom: '24px' }}>
        <h1>Analytics</h1>
        <p style={{ color: '#666' }}>Revenue projections and profit analysis</p>
      </div>

      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '32px' }}>
        <div style={{ background: 'white', padding: '20px', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <div style={{ color: '#666', fontSize: '13px', marginBottom: '8px' }}>Total Tickets</div>
          <div style={{ fontSize: '28px', fontWeight: 700 }}>{summary.total_tickets}</div>
        </div>
        <div style={{ background: 'white', padding: '20px', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <div style={{ color: '#666', fontSize: '13px', marginBottom: '8px' }}>Total Cost</div>
          <div style={{ fontSize: '28px', fontWeight: 700 }}>{formatCurrency(summary.total_cost)}</div>
        </div>
        <div style={{ background: 'linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)', padding: '20px', borderRadius: '12px', borderLeft: '4px solid #2563eb' }}>
          <div style={{ color: '#666', fontSize: '13px', marginBottom: '8px' }}>Vivid Revenue</div>
          <div style={{ fontSize: '28px', fontWeight: 700, color: '#1d4ed8' }}>{formatCurrency(summary.total_vivid_revenue)}</div>
        </div>
        <div style={{ background: 'linear-gradient(135deg, #fdf4ff 0%, #f3e8ff 100%)', padding: '20px', borderRadius: '12px', borderLeft: '4px solid #9333ea' }}>
          <div style={{ color: '#666', fontSize: '13px', marginBottom: '8px' }}>StubHub Revenue</div>
          <div style={{ fontSize: '28px', fontWeight: 700, color: '#7c3aed' }}>{formatCurrency(summary.total_stubhub_revenue)}</div>
        </div>
      </div>

      {/* Profit Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px', marginBottom: '32px' }}>
        <div style={{ background: 'white', padding: '24px', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h3 style={{ margin: '0 0 16px', color: '#1d4ed8' }}>Vivid Seats (10% fee)</h3>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ color: '#666' }}>Revenue:</span>
            <span style={{ fontWeight: 600 }}>{formatCurrency(summary.total_vivid_revenue)}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ color: '#666' }}>Cost:</span>
            <span style={{ fontWeight: 600 }}>-{formatCurrency(summary.total_cost)}</span>
          </div>
          <hr style={{ border: 'none', borderTop: '1px solid #e5e7eb', margin: '12px 0' }} />
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontWeight: 700 }}>Profit:</span>
            <span style={{ fontWeight: 700, fontSize: '20px', color: summary.total_vivid_profit >= 0 ? '#059669' : '#dc2626' }}>
              {summary.total_vivid_profit >= 0 ? '+' : ''}{formatCurrency(summary.total_vivid_profit)}
            </span>
          </div>
        </div>

        <div style={{ background: 'white', padding: '24px', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h3 style={{ margin: '0 0 16px', color: '#7c3aed' }}>StubHub (15% fee)</h3>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ color: '#666' }}>Revenue:</span>
            <span style={{ fontWeight: 600 }}>{formatCurrency(summary.total_stubhub_revenue)}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ color: '#666' }}>Cost:</span>
            <span style={{ fontWeight: 600 }}>-{formatCurrency(summary.total_cost)}</span>
          </div>
          <hr style={{ border: 'none', borderTop: '1px solid #e5e7eb', margin: '12px 0' }} />
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontWeight: 700 }}>Profit:</span>
            <span style={{ fontWeight: 700, fontSize: '20px', color: summary.total_stubhub_profit >= 0 ? '#059669' : '#dc2626' }}>
              {summary.total_stubhub_profit >= 0 ? '+' : ''}{formatCurrency(summary.total_stubhub_profit)}
            </span>
          </div>
        </div>
      </div>

      {/* Per-Set Breakdown */}
      <div style={{ background: 'white', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #e5e7eb' }}>
          <h3 style={{ margin: 0 }}>Profit by Set</h3>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
          <thead>
            <tr style={{ background: '#f9fafb' }}>
              <th style={{ padding: '12px 16px', textAlign: 'left' }}>Set</th>
              <th style={{ padding: '12px 16px', textAlign: 'left' }}>Section</th>
              <th style={{ padding: '12px 16px', textAlign: 'center' }}>Qty</th>
              <th style={{ padding: '12px 16px', textAlign: 'right' }}>Cost</th>
              <th style={{ padding: '12px 16px', textAlign: 'right', background: '#eff6ff' }}>Vivid Profit</th>
              <th style={{ padding: '12px 16px', textAlign: 'right', background: '#fdf4ff' }}>StubHub Profit</th>
              <th style={{ padding: '12px 16px', textAlign: 'center' }}>Best</th>
            </tr>
          </thead>
          <tbody>
            {data.sets.map((set) => {
              const vividProfit = set.vivid_you_receive
                ? (set.vivid_you_receive - set.cost_per_ticket) * set.quantity
                : null;
              const stubhubProfit = set.stubhub_you_receive
                ? (set.stubhub_you_receive - set.cost_per_ticket) * set.quantity
                : null;

              return (
                <tr key={set.set_name} style={{ borderBottom: '1px solid #e5e7eb' }}>
                  <td style={{ padding: '12px 16px', fontWeight: 600 }}>{set.set_name}</td>
                  <td style={{ padding: '12px 16px' }}>{set.section}</td>
                  <td style={{ padding: '12px 16px', textAlign: 'center' }}>{set.quantity}</td>
                  <td style={{ padding: '12px 16px', textAlign: 'right' }}>{formatCurrency(set.total_cost)}</td>
                  <td style={{
                    padding: '12px 16px',
                    textAlign: 'right',
                    background: '#eff6ff',
                    color: vividProfit !== null ? (vividProfit >= 0 ? '#059669' : '#dc2626') : '#666',
                    fontWeight: 600
                  }}>
                    {vividProfit !== null ? `${vividProfit >= 0 ? '+' : ''}${formatCurrency(vividProfit)}` : '-'}
                  </td>
                  <td style={{
                    padding: '12px 16px',
                    textAlign: 'right',
                    background: '#fdf4ff',
                    color: stubhubProfit !== null ? (stubhubProfit >= 0 ? '#059669' : '#dc2626') : '#666',
                    fontWeight: 600
                  }}>
                    {stubhubProfit !== null ? `${stubhubProfit >= 0 ? '+' : ''}${formatCurrency(stubhubProfit)}` : '-'}
                  </td>
                  <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                    {set.best_platform && (
                      <span style={{
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: 600,
                        background: set.best_platform === 'Vivid' ? '#dbeafe' : '#f3e8ff',
                        color: set.best_platform === 'Vivid' ? '#1d4ed8' : '#7c3aed'
                      }}>
                        {set.best_platform}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}
