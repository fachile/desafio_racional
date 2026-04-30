export default function LiveIndicator({ lastUpdated }) {
  const time = lastUpdated
    ? lastUpdated.toLocaleTimeString("es-CL", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    : "--:--:--";

  return (
    <div className="live-indicator">
      <span className="live-dot" />
      <span className="live-text">EN VIVO</span>
      <span className="live-time">{time}</span>
    </div>
  );
}
