interface RevenueCardProps {
  title: string;
  value: number | null | undefined;
  subtitle?: string;
  isLoading?: boolean;
  variant?: 'default' | 'positive' | 'negative';
}

export function RevenueCard({ title, value, subtitle, isLoading, variant = 'default' }: RevenueCardProps) {
  const formatCurrency = (amount: number | null | undefined) => {
    if (amount === null || amount === undefined) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getValueClass = () => {
    if (variant === 'positive' || (value && value > 0 && variant === 'default')) {
      return 'stat-value positive';
    }
    if (variant === 'negative' || (value && value < 0)) {
      return 'stat-value negative';
    }
    return 'stat-value';
  };

  return (
    <div className="stat-card">
      <div className="stat-label">{title}</div>
      {isLoading ? (
        <div className="stat-value">...</div>
      ) : (
        <div className={getValueClass()}>
          {formatCurrency(value)}
        </div>
      )}
      {subtitle && <div className="price-range">{subtitle}</div>}
    </div>
  );
}
