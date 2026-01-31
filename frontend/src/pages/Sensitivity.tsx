import { useState } from 'react';
import { Layout } from '../components/layout/Layout';
import { useComparison } from '../hooks/useComparison';

const VIVID_FEE = 0.10;
const STUBHUB_FEE = 0.15;

function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined) return '-';
  return `$${value.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

export function Sensitivity() {
  const { data, isLoading } = useComparison();

  // Store selling prices for each set (keyed by set_name)
  const [sellingPrices, setSellingPrices] = useState<Record<string, string>>({});

  const handlePriceChange = (setName: string, value: string) => {
    setSellingPrices(prev => ({ ...prev, [setName]: value }));
  };

  const getSellingPrice = (setName: string): number | null => {
    const val = sellingPrices[setName];
    if (!val || val === '') return null;
    const num = parseFloat(val);
    return isNaN(num) ? null : num;
  };

  // Calculate totals
  const calculateTotals = () => {
    if (!data) return null;

    let totalCost = 0;
    let totalVividRevenue = 0;
    let totalStubHubRevenue = 0;
    let totalTickets = 0;

    data.sets.forEach(set => {
      const price = getSellingPrice(set.set_name);
      totalCost += set.cost_per_ticket * set.quantity;
      totalTickets += set.quantity;

      if (price) {
        totalVividRevenue += price * (1 - VIVID_FEE) * set.quantity;
        totalStubHubRevenue += price * (1 - STUBHUB_FEE) * set.quantity;
      }
    });

    return {
      totalCost,
      totalTickets,
      totalVividRevenue,
      totalStubHubRevenue,
      totalVividProfit: totalVividRevenue - totalCost,
      totalStubHubProfit: totalStubHubRevenue - totalCost,
    };
  };

  const totals = calculateTotals();

  return (
    <Layout>
      <div className="sensitivity-header">
        <h1>Sensitivity Calculator</h1>
        <p className="subtitle">Enter your target selling prices to calculate projected profits</p>
      </div>

      {isLoading ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading inventory...</p>
        </div>
      ) : data ? (
        <>
          {/* Summary Cards */}
          {totals && (
            <div className="summary-grid">
              <div className="summary-card">
                <span className="summary-card-label">Total Tickets</span>
                <span className="summary-card-value">{totals.totalTickets}</span>
              </div>
              <div className="summary-card">
                <span className="summary-card-label">Total Cost</span>
                <span className="summary-card-value">{formatCurrency(totals.totalCost)}</span>
              </div>
              <div className="summary-card summary-card-vivid">
                <span className="summary-card-label">Vivid Profit (10% fee)</span>
                <span className="summary-card-value" style={{ color: totals.totalVividProfit >= 0 ? '#059669' : '#dc2626' }}>
                  {totals.totalVividProfit !== 0 ? formatCurrency(totals.totalVividProfit) : '-'}
                </span>
              </div>
              <div className="summary-card summary-card-stubhub">
                <span className="summary-card-label">StubHub Profit (15% fee)</span>
                <span className="summary-card-value" style={{ color: totals.totalStubHubProfit >= 0 ? '#059669' : '#dc2626' }}>
                  {totals.totalStubHubProfit !== 0 ? formatCurrency(totals.totalStubHubProfit) : '-'}
                </span>
              </div>
            </div>
          )}

          {/* Input Table */}
          <div className="table-container">
            <table className="sensitivity-table">
              <thead>
                <tr>
                  <th>Set</th>
                  <th>Date</th>
                  <th>Section</th>
                  <th>Qty</th>
                  <th>Your Cost</th>
                  <th>Sell Price</th>
                  <th className="col-vivid">Vivid You Get</th>
                  <th className="col-vivid">Vivid Profit</th>
                  <th className="col-stubhub">StubHub You Get</th>
                  <th className="col-stubhub">StubHub Profit</th>
                </tr>
              </thead>
              <tbody>
                {data.sets.map((set) => {
                  const sellPrice = getSellingPrice(set.set_name);
                  const vividReceive = sellPrice ? sellPrice * (1 - VIVID_FEE) : null;
                  const stubhubReceive = sellPrice ? sellPrice * (1 - STUBHUB_FEE) : null;
                  const vividProfitPer = vividReceive ? vividReceive - set.cost_per_ticket : null;
                  const stubhubProfitPer = stubhubReceive ? stubhubReceive - set.cost_per_ticket : null;
                  const vividTotalProfit = vividProfitPer ? vividProfitPer * set.quantity : null;
                  const stubhubTotalProfit = stubhubProfitPer ? stubhubProfitPer * set.quantity : null;

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
                      <td className="col-vivid">{formatCurrency(vividReceive)}</td>
                      <td className={`col-vivid ${vividProfitPer !== null ? (vividProfitPer >= 0 ? 'cell-positive' : 'cell-negative') : ''}`}>
                        {vividTotalProfit !== null ? (
                          <div>
                            <div>{vividProfitPer! >= 0 ? '+' : ''}{formatCurrency(vividProfitPer)}/tix</div>
                            <div className="profit-total">{vividTotalProfit >= 0 ? '+' : ''}{formatCurrency(vividTotalProfit)} total</div>
                          </div>
                        ) : '-'}
                      </td>
                      <td className="col-stubhub">{formatCurrency(stubhubReceive)}</td>
                      <td className={`col-stubhub ${stubhubProfitPer !== null ? (stubhubProfitPer >= 0 ? 'cell-positive' : 'cell-negative') : ''}`}>
                        {stubhubTotalProfit !== null ? (
                          <div>
                            <div>{stubhubProfitPer! >= 0 ? '+' : ''}{formatCurrency(stubhubProfitPer)}/tix</div>
                            <div className="profit-total">{stubhubTotalProfit >= 0 ? '+' : ''}{formatCurrency(stubhubTotalProfit)} total</div>
                          </div>
                        ) : '-'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Breakeven Info */}
          <div className="breakeven-section">
            <h3>Breakeven Prices (to cover your cost)</h3>
            <div className="breakeven-grid">
              {data.sets.map((set) => {
                const vividBreakeven = set.cost_per_ticket / (1 - VIVID_FEE);
                const stubhubBreakeven = set.cost_per_ticket / (1 - STUBHUB_FEE);
                return (
                  <div key={set.set_name} className="breakeven-card">
                    <div className="breakeven-set">{set.set_name} - {set.section}</div>
                    <div className="breakeven-prices">
                      <span className="breakeven-vivid">Vivid: {formatCurrency(vividBreakeven)}</span>
                      <span className="breakeven-stubhub">StubHub: {formatCurrency(stubhubBreakeven)}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      ) : (
        <div className="empty-state">
          <p>No data available.</p>
        </div>
      )}

      <style>{`
        .sensitivity-header {
          margin-bottom: 32px;
        }

        .sensitivity-header h1 {
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

        .summary-card-stubhub {
          background: linear-gradient(135deg, #fdf4ff 0%, #f3e8ff 100%);
          border-left: 4px solid #9333ea;
        }

        .table-container {
          overflow-x: auto;
          background: white;
          border-radius: 12px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .sensitivity-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 14px;
        }

        .sensitivity-table th,
        .sensitivity-table td {
          padding: 12px 16px;
          text-align: left;
          border-bottom: 1px solid #e5e7eb;
          white-space: nowrap;
        }

        .sensitivity-table th {
          background: #f9fafb;
          font-weight: 600;
          color: #374151;
        }

        .sensitivity-table tbody tr:hover {
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

        .cell-positive {
          color: #059669;
          font-weight: 600;
        }

        .cell-negative {
          color: #dc2626;
          font-weight: 600;
        }

        .price-input-wrapper {
          display: flex;
          align-items: center;
          background: #f3f4f6;
          border-radius: 6px;
          padding: 0 8px;
          width: 100px;
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

        .profit-total {
          font-size: 12px;
          opacity: 0.8;
          margin-top: 2px;
        }

        .breakeven-section {
          margin-top: 32px;
          padding: 20px;
          background: #f9fafb;
          border-radius: 12px;
        }

        .breakeven-section h3 {
          margin: 0 0 16px;
          font-size: 16px;
        }

        .breakeven-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
          gap: 12px;
        }

        .breakeven-card {
          background: white;
          padding: 12px 16px;
          border-radius: 8px;
          box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }

        .breakeven-set {
          font-weight: 600;
          margin-bottom: 8px;
        }

        .breakeven-prices {
          display: flex;
          gap: 16px;
          font-size: 13px;
        }

        .breakeven-vivid {
          color: #1d4ed8;
        }

        .breakeven-stubhub {
          color: #7c3aed;
        }

        .empty-state {
          text-align: center;
          padding: 60px 20px;
          color: #666;
        }
      `}</style>
    </Layout>
  );
}
