# Static mock prices in CLP (Chilean Pesos)
# In a real system this would call a market data provider

MOCK_PRICES: dict[str, int] = {
    "AAPL":  int(178.50  * 950),   # ~169,575 CLP
    "GOOGL": int(165.20  * 950),   # ~156,940 CLP
    "MSFT":  int(415.30  * 950),   # ~394,535 CLP
    "AMZN":  int(185.75  * 950),   # ~176,463 CLP
    "TSLA":  int(172.40  * 950),   # ~163,780 CLP
    "META":  int(490.10  * 950),   # ~465,595 CLP
    "NVDA":  int(875.60  * 950),   # ~831,820 CLP
    "JPM":   int(198.30  * 950),   # ~188,385 CLP
    "BRKB":  int(395.00  * 950),   # ~375,250 CLP
    "V":     int(275.80  * 950),   # ~261,010 CLP
}


def get_price(ticker: str) -> int:
    ticker = ticker.upper()
    if ticker not in MOCK_PRICES:
        raise ValueError(f"Ticker '{ticker}' not found. Available: {list(MOCK_PRICES.keys())}")
    return MOCK_PRICES[ticker]


def get_all_tickers() -> list[str]:
    return list(MOCK_PRICES.keys())
