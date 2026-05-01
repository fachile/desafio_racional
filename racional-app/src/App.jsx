import { useState } from "react";
import { useInvestmentEvolution } from "./hooks/useInvestmentEvolution";
import { useIntradayEvolution } from "./hooks/useIntradayEvolution";
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

function formatSignedCLP(value) {
  return `${value >= 0 ? "+" : "-"}${formatCLP(Math.abs(value))}`;
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
  const endDate = latest?.date ?? data[data.length - 1].date;

  const dateRange =
    data.length > 0
      ? `${first.date.toLocaleDateString("es-CL", {
          day: "2-digit", month: "short", year: "numeric",
        })} — ${endDate.toLocaleDateString("es-CL", {
          day: "2-digit", month: "short", year: "numeric",
        })}`
      : "";

  const isGainPositive = gain >= 0;
  const intradayDelta =
    ticks.length >= 2
      ? ticks[ticks.length - 1].portfolioValue - ticks[0].portfolioValue
      : null;
  const gainLabel = gain >= 0 ? "He ganado" : "He perdido";

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

        <div className="portfolio-summary">
          <div className="portfolio-summary-main">
            <span className="portfolio-summary-item-label">Saldo total</span>
            <span className="portfolio-summary-item-value">{formatCLP(currentValue)}</span>
          </div>

          <div className="portfolio-summary-grid">
            <div className="portfolio-summary-item">
              <span className="portfolio-summary-item-label">He invertido</span>
              <span className="portfolio-summary-item-value">{formatCLP(contributions)}</span>
            </div>
            <div className="portfolio-summary-item portfolio-summary-item-end">
              <span className="portfolio-summary-item-label">{gainLabel}</span>
              <span className={`portfolio-summary-item-value ${gain >= 0 ? "positive" : "negative"}`}>
                {formatSignedCLP(gain)}
              </span>
            </div>
          </div>
        </div>

        {/* Intraday */}
        <div className="chart-card" style={{ marginBottom: 20 }}>
          <div className="chart-header">
            <div>
              <div className="chart-title-row">
                <h2 className="chart-title">Evolución de hoy</h2>
                <span className="live-badge">
                  <span className="live-dot-sm" />
                  TIEMPO REAL
                </span>
              </div>
              <p className="chart-subtitle">Actualizaciones minuto a minuto durante la sesión</p>
              <p className="chart-subtitle">Retorno del día: <strong>{formatPct(dailyReturn)}</strong></p>
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
              <p className="chart-subtitle">Rentabilidad total: <strong>{formatPct(totalReturn)}</strong></p>
            </div>
            <div className={`trend-badge ${isGainPositive ? "positive" : "negative"}`}>
              {isGainPositive ? "▲" : "▼"} {formatPct(totalReturn)}
            </div>
          </div>
          <EvolutionChart data={data} period={period} onPeriodChange={setPeriod} />
        </div>

        <p className="footer-note">
          Datos en tiempo real · {data.length} registros históricos
        </p>
      </main>
    </div>
  );
}
