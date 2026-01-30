import { useMemo } from 'react';
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
import type { PriceHistoryPoint } from '../../types/analytics';

interface PriceChartProps {
  data: PriceHistoryPoint[] | undefined;
  isLoading?: boolean;
}

const PLATFORM_COLORS = {
  stubhub: '#3d5a80',
  seatgeek: '#9d4edd',
  vividseats: '#06d6a0',
};

export function PriceChart({ data, isLoading }: PriceChartProps) {
  const chartData = useMemo(() => {
    if (!data) return [];

    return data.map((point) => ({
      date: new Date(point.recorded_date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      }),
      stubhub: point.platform_breakdown?.stubhub?.avg,
      seatgeek: point.platform_breakdown?.seatgeek?.avg,
      vividseats: point.platform_breakdown?.vividseats?.avg,
      average: point.avg_price,
    }));
  }, [data]);

  if (isLoading) {
    return (
      <div className="chart-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        Loading chart...
      </div>
    );
  }

  if (!chartData.length) {
    return (
      <div className="chart-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#666' }}>
        No price history data yet. Data will appear after the first price collection.
      </div>
    );
  }

  return (
    <div className="chart-container">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis
            tickFormatter={(value) => `$${value}`}
            domain={['dataMin - 50', 'dataMax + 50']}
          />
          <Tooltip
            formatter={(value: number) => [`$${value?.toFixed(2) || 'N/A'}`, '']}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="stubhub"
            stroke={PLATFORM_COLORS.stubhub}
            name="StubHub"
            dot={false}
            strokeWidth={2}
          />
          <Line
            type="monotone"
            dataKey="seatgeek"
            stroke={PLATFORM_COLORS.seatgeek}
            name="SeatGeek"
            dot={false}
            strokeWidth={2}
          />
          <Line
            type="monotone"
            dataKey="vividseats"
            stroke={PLATFORM_COLORS.vividseats}
            name="Vivid Seats"
            dot={false}
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
