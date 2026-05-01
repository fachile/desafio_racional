import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

function formatCLP(value) {
  return new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    maximumFractionDigits: 0,
  }).format(value);
}

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  const isPos = d.dailyReturn >= 0;

  return (
    <div className="chart-tooltip">
      <p className="tooltip-date">{d.time}</p>
      <p className="tooltip-value">{formatCLP(d.portfolioValue)}</p>
      <p className={`tooltip-gain ${isPos ? "positive" : "negative"}`}>
        Retorno: {isPos ? "+" : ""}{(d.dailyReturn * 100).toFixed(4)}%
      </p>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="intraday-empty">
      <div className="intraday-empty-icon">
        <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
          <circle cx="20" cy="20" r="19" stroke="currentColor" strokeWidth="1.5" strokeDasharray="4 3" opacity="0.3"/>
          <path d="M8 28 L14 20 L20 23 L26 15 L32 18" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" opacity="0.4"/>
          <circle cx="20" cy="20" r="3" fill="currentColor" opacity="0.2"/>
        </svg>
      </div>
      <p className="intraday-empty-title">Esperando datos de hoy</p>
      <p className="intraday-empty-sub">
        El gráfico se construirá en tiempo real a medida que lleguen actualizaciones
      </p>
      <div className="intraday-waiting">
        <span className="live-dot" style={{ display: "inline-block" }} />
        <span>Escuchando Firestore...</span>
      </div>
    </div>
  );
}

export default function IntradayChart({ ticks, latestValue }) {
  if (!ticks || ticks.length === 0) return <EmptyState />;

  const values = ticks.map((t) => t.portfolioValue);
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const padding = Math.max((maxVal - minVal) * 0.15, 500);

  const firstValue = ticks[0]?.portfolioValue;
  const lastValue = ticks[ticks.length - 1]?.portfolioValue;
  const isPositive = lastValue >= firstValue;
  const strokeColor = isPositive ? "#16a34a" : "#dc2626";

  // Mostrar solo primer, algunos intermedios y último tick en el eje X
  const xInterval = Math.max(1, Math.floor(ticks.length / 5) - 1);

  return (
    <div className="chart-wrapper">
      {/* Tick counter */}
      <div className="intraday-meta">
        <span className="intraday-ticks">
          {ticks.length} {ticks.length === 1 ? "actualización" : "actualizaciones"} hoy
        </span>
        <span className="intraday-last">
          Último: <strong>{formatCLP(lastValue)}</strong>
        </span>
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={ticks} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />

          <XAxis
            dataKey="time"
            tick={{ fontSize: 10, fill: "#9ca3af" }}
            tickLine={false}
            axisLine={false}
            interval={xInterval}
          />

          <YAxis
            domain={[minVal - padding, maxVal + padding]}
            tick={{ fontSize: 10, fill: "#9ca3af" }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v) =>
              new Intl.NumberFormat("es-CL", {
                notation: "compact",
                maximumFractionDigits: 1,
              }).format(v)
            }
            width={64}
          />

          <Tooltip content={<CustomTooltip />} />

          {/* Línea de referencia = primer valor del día */}
          {ticks.length > 1 && (
            <ReferenceLine
              y={firstValue}
              stroke="#d1d5db"
              strokeDasharray="4 4"
              label={{
                value: "Apertura",
                position: "insideTopRight",
                fontSize: 10,
                fill: "#9ca3af",
              }}
            />
          )}

          <Line
            type="monotone"
            dataKey="portfolioValue"
            stroke={strokeColor}
            strokeWidth={2}
            dot={ticks.length <= 10
              ? { r: 3, fill: strokeColor, strokeWidth: 0 }
              : false
            }
            activeDot={{ r: 5, stroke: strokeColor, strokeWidth: 2, fill: "#fff" }}
            isAnimationActive={true}
            animationDuration={400}
            animationEasing="ease-out"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
