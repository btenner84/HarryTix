export function LoadingSpinner({ text = 'Loading...' }: { text?: string }) {
  return (
    <div className="loading">
      <div className="spinner"></div>
      <span>{text}</span>
    </div>
  );
}
