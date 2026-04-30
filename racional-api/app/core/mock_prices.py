from decimal import Decimal

# Static mock prices in USD
# In a real system this would call a market data provider
MOCK_PRICES: dict[str, Decimal] = {
    "AAPL":  Decimal("178.50"),
    "GOOGL": Decimal("165.20"),
    "MSFT":  Decimal("415.30"),
    "AMZN":  Decimal("185.75"),
    "TSLA":  Decimal("172.40"),
    "META":  Decimal("490.10"),
    "NVDA":  Decimal("875.60"),
    "JPM":   Decimal("198.30"),
    "BRK.B": Decimal("395.00"),
    "V":     Decimal("275.80"),
}


def get_price(ticker: str) -> Decimal:
    ticker = ticker.upper()
    if ticker not in MOCK_PRICES:
        raise ValueError(f"Ticker '{ticker}' not found in mock price list. Available: {list(MOCK_PRICES.keys())}")
    return MOCK_PRICES[ticker]


def get_all_tickers() -> list[str]:
    return list(MOCK_PRICES.keys())
