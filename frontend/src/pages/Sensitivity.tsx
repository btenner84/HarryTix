import { useState } from 'react';
import { Layout } from '../components/layout/Layout';
import { useComparison } from '../hooks/useComparison';

const VIVID_FEE = 0.10;

function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return '-';
  return `$${value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

export function Sensitivity() {
  const { data, isLoading } = useComparison();
  const [sellingPrices, setSellingPrices] = useState<Record<string, string>>({});

  const handlePriceChange = (setName: string, value: string) => {
    setSellingPrices(prev => ({ ...prev, [setName]: value }));
  };

  const getPrice = (setName: string): number | null => {
    const val = sellingPrices[setName];
    if (!val || val === '') return null;
    const num = parseFloat(val);
    return isNaN(num) ? null : num;
  };

  // Calculate totals - use summary for cost, calculate profit from user inputs
  let totalProfit = 0;
  const totalCost = data?.summary.total_cost || 0;

  if (data) {
    data.sets.forEach(set => {
      const price = getPrice(set.set_name);
      if (price) {
        const receive = price * (1 - VIVID_FEE);
        totalProfit += (receive - set.cost_per_ticket) * set.quantity;
      }
    });
  }

  return (
    <Layout>
      <div className="page-header">
        <h1>Sensitivity Calculator</h1>
        <p className="subtitle">Enter selling prices to calculate projected profit (Vivid Seats - 10% fee)</p>
      </div>

      {isLoading ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
        </div>
      ) : data ? (
        <>
          <div className="table-container">
            <table className="comparison-table">
              <thead>
                <tr>
                  <th>Set</th>
                  <th>Date</th>
                  <th>Section</th>
                  <th>Qty</th>
                  <th>Your Cost</th>
                  <th>Sell Price</th>
                  <th>You Receive</th>
                  <th>Profit/Ticket</th>
                  <th>Total Profit</th>
                </tr>
              </thead>
              <tbody>
                {data.sets.map((set) => {
                  const price = getPrice(set.set_name);
                  const receive = price ? price * (1 - VIVID_FEE) : null;
                  const profitPerTicket = receive ? receive - set.cost_per_ticket : null;
                  const totalSetProfit = profitPerTicket ? profitPerTicket * set.quantity : null;

                  return (
                    <tr key={set.set_name}>
                      <td className="cell-set">{set.set_name}</td>
                      <td>{set.date}</td>
                      <td className="cell-section">{set.section}</td>
                      <td className="cell-center">{set.quantity}</td>
                      <td>{formatCurrency(set.cost_per_ticket)}</td>
                      <td>
                        <div className="price-input-wrapper">
                          <span className="price-prefix">$</span>
                          <input
                            type="number"
                            className="price-input"
                            placeholder="0"
                            value={sellingPrices[set.set_name] || ''}
                            onChange={(e) => handlePriceChange(set.set_name, e.target.value)}
                          />
                        </div>
                      </td>
                      <td className="cell-highlight">{formatCurrency(receive)}</td>
                      <td className={profitPerTicket !== null ? (profitPerTicket >= 0 ? 'cell-positive' : 'cell-negative') : ''}>
                        {profitPerTicket !== null ? `${profitPerTicket >= 0 ? '+' : ''}${formatCurrency(profitPerTicket)}` : '-'}
                      </td>
                      <td className={`cell-total ${totalSetProfit !== null ? (totalSetProfit >= 0 ? 'cell-positive' : 'cell-negative') : ''}`}>
                        {totalSetProfit !== null ? `${totalSetProfit >= 0 ? '+' : ''}${formatCurrency(totalSetProfit)}` : '-'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr className="totals-row">
                  <td colSpan={4}></td>
                  <td className="totals-label">TOTAL</td>
                  <td></td>
                  <td></td>
                  <td></td>
                  <td className={`totals-value ${totalProfit >= 0 ? 'cell-positive' : 'cell-negative'}`}>
                    {totalProfit !== 0 ? `${totalProfit >= 0 ? '+' : ''}${formatCurrency(totalProfit)}` : '-'}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>

          <div className="info-section">
            <p><strong>Total Cost:</strong> {formatCurrency(totalCost)}</p>
            <p><strong>Vivid Seats Fee:</strong> 10% (you receive 90% of sell price)</p>
          </div>
        </>
      ) : null}

      <style>{`
        .page-header {
          margin-bottom: 24px;
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
        .loading-container {
          display: flex;
          justify-content: center;
          padding: 80px;
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
        .cell-total {
          font-weight: 700;
          font-size: 15px;
        }
        .price-input-wrapper {
          display: flex;
          align-items: center;
          background: #f3f4f6;
          border-radius: 6px;
          padding: 0 8px;
          width: 90px;
        }
        .price-prefix {
          color: #666;
          font-weight: 500;
        }
        .price-input {
          border: none;
          background: transparent;
          padding: 8px 4px;
          width: 100%;
          font-size: 14px;
          font-weight: 600;
        }
        .price-input:focus {
          outline: none;
        }
        .price-input::placeholder {
          color: #aaa;
        }
        .totals-row {
          background: #f9fafb;
          border-top: 2px solid #e5e7eb;
        }
        .totals-row td {
          border-bottom: none;
        }
        .totals-label {
          font-weight: 700;
          text-align: right;
        }
        .totals-value {
          font-size: 18px;
          font-weight: 700;
        }
        .info-section {
          margin-top: 16px;
          padding: 16px;
          background: #f9fafb;
          border-radius: 8px;
          font-size: 14px;
          color: #666;
        }
        .info-section p {
          margin: 4px 0;
        }
      `}</style>
    </Layout>
  );
}
