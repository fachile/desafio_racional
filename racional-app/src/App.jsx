import { useState } from "react";
import { useInvestmentEvolution } from "./hooks/useInvestmentEvolution";
import { useIntradayEvolution } from "./hooks/useIntradayEvolution";
import MetricCard from "./components/MetricCard";
import EvolutionChart from "./components/EvolutionChart";
import IntradayChart from "./components/IntradayChart";
import LiveIndicator from "./components/LiveIndicator";
import "./App.css";

function formatCLP(value) {
  return new Intl.NumberFormat("es-CL", {
    style: "currency",
    currency: "CLP",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPct(value) {
  return `${value >= 0 ? "+" : ""}${(value * 100).toFixed(2)}%`;
}

export default function App() {
  const { data, loading, error, lastUpdated } = useInvestmentEvolution();
  const { ticks, latestValue } = useIntradayEvolution();
  const [period, setPeriod] = useState("Todo");

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner" />
        <p>Conectando al portafolio...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="loading-screen">
        <p className="error-text">Error: {error}</p>
      </div>
    );
  }

  const latest = latestValue ?? (data.length > 0
    ? {
        portfolioValue: data[data.length - 1].portfolioValue,
        contributions: data[data.length - 1].contributions,
        dailyReturn: data[data.length - 1].dailyReturn,
        date: data[data.length - 1].date,
      }
    : null);

  const first = data[0];
  const currentValue = latest?.portfolioValue ?? 0;
  const contributions = latest?.contributions ?? 0;
  const gain = currentValue - contributions;
  const totalReturn = contributions > 0 ? gain / contributions : 0;
  const dailyReturn = latest?.dailyReturn ?? 0;

  const dateRange =
    data.length > 0
      ? `${first.date.toLocaleDateString("es-CL", {
          day: "2-digit", month: "short", year: "numeric",
        })} — ${(latest?.date ?? data[data.length - 1]?.date).toLocaleDateString("es-CL", {
          day: "2-digit", month: "short", year: "numeric",
        })}`
      : "";

  const isGainPositive = gain >= 0;
  const intradayDelta =
    ticks.length >= 2
      ? ticks[ticks.length - 1].portfolioValue - ticks[0].portfolioValue
      : null;

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <div className="logo">
            <span className="logo-mark">R</span>
            <span className="logo-text">Racional</span>
          </div>
          <div className="header-divider" />
          <span className="header-title">Mi Portafolio</span>
        </div>
        <LiveIndicator lastUpdated={lastUpdated} />
      </header>

      <main className="main">
        <p className="date-range">{dateRange}</p>

        <div className="cards-grid">
          <MetricCard label="Valor actual" value={formatCLP(currentValue)} trend={0} delay={0} />
          <MetricCard label="Rentabilidad total" value={formatPct(totalReturn)} sub={formatPct(totalReturn)} trend={totalReturn} delay={80} />
          <MetricCard label="Ganancia / Pérdida" value={formatCLP(gain)} sub={formatCLP(gain)} trend={gain} delay={160} />
          <MetricCard label="Retorno del día" value={formatPct(dailyReturn)} sub={formatPct(dailyReturn)} trend={dailyReturn} delay={240} />
        </div>

        {/* Intraday */}
        <div className="chart-card" style={{ marginBottom: 20 }}>
          <div className="chart-header">
            <div>
              <div className="chart-title-row">
                <h2 className="chart-title">Movimiento de hoy</h2>
                <span className="live-badge">
                  <span className="live-dot-sm" />
                  TIEMPO REAL
                </span>
              </div>
              <p className="chart-subtitle">Actualizaciones minuto a minuto durante la sesión</p>
            </div>
            {intradayDelta !== null && (
              <div className={`trend-badge ${intradayDelta >= 0 ? "positive" : "negative"}`}>
                {intradayDelta >= 0 ? "▲" : "▼"} {formatCLP(Math.abs(intradayDelta))}
              </div>
            )}
          </div>
          <IntradayChart ticks={ticks} latestValue={latestValue} />
        </div>

        {/* Historical */}
        <div className="chart-card">
          <div className="chart-header">
            <div>
              <h2 className="chart-title">Evolución histórica</h2>
              <p className="chart-subtitle">Aporte inicial: <strong>{formatCLP(contributions)}</strong></p>
            </div>
            <div className={`trend-badge ${isGainPositive ? "positive" : "negative"}`}>
              {isGainPositive ? "▲" : "▼"} {formatPct(totalReturn)}
            </div>
          </div>
          <EvolutionChart data={data} period={period} onPeriodChange={setPeriod} />
        </div>

        <p className="footer-note">
          Datos en tiempo real · {data.length} registros históricos · Fuente: Racional
        </p>
      </main>
    </div>
  );
}
