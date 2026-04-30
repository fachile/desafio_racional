export default function MetricCard({ label, value, sub, trend, delay = 0 }) {
  const isPositive = trend > 0;
  const isNeutral = trend === 0;

  return (
    <div
      className="metric-card"
      style={{ animationDelay: `${delay}ms` }}
    >
      <span className="metric-label">{label}</span>
      <span className="metric-value">{value}</span>
      {sub !== undefined && (
        <span
          className={`metric-sub ${
            isNeutral ? "neutral" : isPositive ? "positive" : "negative"
          }`}
        >
          {isPositive && "+"}
          {sub}
        </span>
      )}
    </div>
  );
}
