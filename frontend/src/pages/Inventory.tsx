import { Layout } from '../components/layout/Layout';
import { useComparison } from '../hooks/useComparison';

function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return '-';
  return `$${value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

export function Inventory() {
  const { data, isLoading } = useComparison();

  const totalTickets = data?.sets.reduce((sum, s) => sum + s.quantity, 0) || 0;
  const totalCost = data?.sets.reduce((sum, s) => sum + s.total_cost, 0) || 0;

  return (
    <Layout>
      <div style={{ marginBottom: '24px' }}>
        <h1>Inventory</h1>
        <p style={{ color: '#666' }}>
          {totalTickets} tickets across {data?.sets.length || 0} sets | Total investment: {formatCurrency(totalCost)}
        </p>
      </div>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>Loading...</div>
      ) : data ? (
        <div className="table-container" style={{ background: 'white', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
            <thead>
              <tr style={{ background: '#f9fafb' }}>
                <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600 }}>Set</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600 }}>Date</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', fontWeight: 600 }}>Section</th>
                <th style={{ padding: '12px 16px', textAlign: 'center', fontWeight: 600 }}>Qty</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', fontWeight: 600 }}>Cost/Ticket</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', fontWeight: 600 }}>Total Cost</th>
              </tr>
            </thead>
            <tbody>
              {data.sets.map((set) => (
                <tr key={set.set_name} style={{ borderBottom: '1px solid #e5e7eb' }}>
                  <td style={{ padding: '12px 16px', fontWeight: 600 }}>{set.set_name}</td>
                  <td style={{ padding: '12px 16px' }}>{set.date}</td>
                  <td style={{ padding: '12px 16px' }}>{set.section}</td>
                  <td style={{ padding: '12px 16px', textAlign: 'center' }}>{set.quantity}</td>
                  <td style={{ padding: '12px 16px', textAlign: 'right' }}>{formatCurrency(set.cost_per_ticket)}</td>
                  <td style={{ padding: '12px 16px', textAlign: 'right', fontWeight: 600 }}>{formatCurrency(set.total_cost)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr style={{ background: '#f9fafb', fontWeight: 700 }}>
                <td colSpan={3} style={{ padding: '12px 16px' }}>TOTAL</td>
                <td style={{ padding: '12px 16px', textAlign: 'center' }}>{totalTickets}</td>
                <td style={{ padding: '12px 16px' }}></td>
                <td style={{ padding: '12px 16px', textAlign: 'right' }}>{formatCurrency(totalCost)}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      ) : null}
    </Layout>
  );
}
