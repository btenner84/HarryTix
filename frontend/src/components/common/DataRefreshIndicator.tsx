import { useIsFetching } from '@tanstack/react-query';

export function DataRefreshIndicator() {
  const isFetching = useIsFetching();

  return (
    <div className="refresh-indicator">
      {isFetching > 0 ? (
        <span>Updating...</span>
      ) : (
        <span>Auto-refresh: 5 min</span>
      )}
    </div>
  );
}
