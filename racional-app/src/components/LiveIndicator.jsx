function formatUpdatedAt(lastUpdated) {
  if (!lastUpdated) {
    return "Sin actualización";
  }

  const today = new Date();
  const isSameDay =
    lastUpdated.getFullYear() === today.getFullYear() &&
    lastUpdated.getMonth() === today.getMonth() &&
    lastUpdated.getDate() === today.getDate();

  const time = lastUpdated.toLocaleTimeString("es-CL", {
    hour: "2-digit",
    minute: "2-digit",
  });

  if (isSameDay) {
    return `hoy a las ${time}`;
  }

  return `el ${lastUpdated.toLocaleDateString("es-CL", {
    day: "2-digit",
    month: "short",
  })} a las ${time}`;
}

export default function LiveIndicator({ lastUpdated }) {
  const time = formatUpdatedAt(lastUpdated);

  return (
    <div className="live-indicator">
      <span className="live-dot" />
      <span className="live-text">Actualizado</span>
      <span className="live-time">{time}</span>
    </div>
  );
}
