import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

const PERIODS = [
  { label: "1S", days: 7 },
  { label: "1M", days: 30 },
  { label: "3M", days: 90 },
  { label: "Todo", days: null },
];

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
  const gain = d.portfolioValue - d.contributions;
  const isPos = gain >= 0;

  return (
    <div className="chart-tooltip">
      <p className="tooltip-date">
        {d.date.toLocaleDateString("es-CL", {
          day: "2-digit",
          month: "short",
          year: "numeric",
        })}
      </p>
      <p className="tooltip-value">{formatCLP(d.portfolioValue)}</p>
      <p className={`tooltip-gain ${isPos ? "positive" : "negative"}`}>
        {isPos ? "+" : ""}
        {formatCLP(gain)}
      </p>
      <p className="tooltip-return">
        Retorno diario:{" "}
        <strong className={d.dailyReturn >= 0 ? "positive" : "negative"}>
          {(d.dailyReturn * 100).toFixed(3)}%
        </strong>
      </p>
    </div>
  );
}

export default function EvolutionChart({ data, period, onPeriodChange }) {
  const filtered = (() => {
    const selected = PERIODS.find((p) => p.label === period);
    if (!selected?.days) return data;
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - selected.days);
    const result = data.filter((d) => d.date >= cutoff);
    return result.length > 0 ? result : data.slice(-selected.days);
  })();

  const chartData = filtered.map((d) => ({
    ...d,
    timestamp: d.date.getTime(),
    dateLabel: d.date.toLocaleDateString("es-CL", {
      day: "2-digit",
      month: "short",
    }),
  }));

  const values = chartData.map((d) => d.portfolioValue);
  const minVal = Math.min(...values);
  const maxVal = Math.max(...values);
  const padding = (maxVal - minVal) * 0.1;
  const contribution = chartData[0]?.contributions ?? 1000000;
  const isPositive =
    (chartData[chartData.length - 1]?.portfolioValue ?? 0) >= contribution;

  const gradientId = "portfolioGradient";
  const strokeColor = isPositive ? "#16a34a" : "#dc2626";

  return (
    <div className="chart-wrapper">
      {/* Period selector */}
      <div className="period-selector">
        {PERIODS.map((p) => (
          <button
            key={p.label}
            className={`period-btn ${period === p.label ? "active" : ""}`}
            onClick={() => onPeriodChange(p.label)}
          >
            {p.label}
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={340}>
        <AreaChart data={chartData} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={strokeColor} stopOpacity={0.18} />
              <stop offset="95%" stopColor={strokeColor} stopOpacity={0} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />

          <XAxis
            dataKey="timestamp"
            type="number"
            domain={["dataMin", "dataMax"]}
            tick={{ fontSize: 11, fill: "#9ca3af" }}
            tickLine={false}
            axisLine={false}
            interval="preserveStartEnd"
            tickFormatter={(value) =>
              new Date(value).toLocaleDateString("es-CL", {
                day: "2-digit",
                month: "short",
              })
            }
          />

          <YAxis
            domain={[minVal - padding, maxVal + padding]}
            tick={{ fontSize: 11, fill: "#9ca3af" }}
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

          <ReferenceLine
            y={contribution}
            stroke="#d1d5db"
            strokeDasharray="4 4"
            label={{
              value: "Aportado",
              position: "insideTopRight",
              fontSize: 10,
              fill: "#9ca3af",
            }}
          />

          <Area
            type="monotone"
            dataKey="portfolioValue"
            stroke={strokeColor}
            strokeWidth={2}
            fill={`url(#${gradientId})`}
            dot={false}
            activeDot={{ r: 5, stroke: strokeColor, strokeWidth: 2, fill: "#fff" }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
