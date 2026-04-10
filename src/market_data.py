"""Bybit V5 market data fetcher and indicator formatter for Atlas Trade."""

from __future__ import annotations

import requests
import pandas as pd

BYBIT_BASE = "https://api.bybit.com"

# Human-readable timeframe aliases -> Bybit interval codes
TIMEFRAME_MAP: dict[str, str] = {
    "1m":  "1",
    "5m":  "5",
    "15m": "15",
    "30m": "30",
    "1h":  "60",
    "4h":  "240",
    "1d":  "D",
    "1w":  "W",
}


def _get(path: str, params: dict) -> dict:
    url = BYBIT_BASE + path
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("retCode", 0) != 0:
        raise RuntimeError(f"Bybit API error: {data.get('retMsg')} — params={params}")
    return data["result"]


def _fetch_klines(symbol: str, interval: str, limit: int = 200) -> pd.DataFrame:
    """Fetch OHLCV klines from Bybit linear (USDT perpetual) market."""
    result = _get("/v5/market/kline", {
        "category": "linear",
        "symbol":   symbol,
        "interval": interval,
        "limit":    limit,
    })
    rows = result["list"]
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume", "turnover"])
    df = df.astype({"ts": "int64", "open": "float64", "high": "float64",
                    "low": "float64", "close": "float64", "volume": "float64"})
    df = df.sort_values("ts").reset_index(drop=True)
    return df


def _fetch_ticker(symbol: str) -> dict:
    """Fetch 24h ticker snapshot (last price, funding, OI, etc.)."""
    result = _get("/v5/market/tickers", {"category": "linear", "symbol": symbol})
    items = result.get("list", [])
    return items[0] if items else {}


def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, float("inf"))
    return 100 - (100 / (1 + rs))


def _macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = _ema(series, fast)
    ema_slow = _ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = _ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def fetch_context(
    symbol: str,
    timeframe: str = "4h",
    limit: int = 200,
) -> str:
    """
    Fetch live market data from Bybit and return a formatted market_context string
    ready to pass into chat().

    Parameters
    ----------
    symbol    : Bybit symbol, e.g. "BTCUSDT", "ETHUSDT", "SOLUSDT"
    timeframe : Human-readable timeframe: "1m","5m","15m","30m","1h","4h","1d","1w"
    limit     : Number of candles to fetch (min 50 recommended for indicator warmup)

    Returns
    -------
    str : Formatted market context block.
    """
    interval = TIMEFRAME_MAP.get(timeframe.lower())
    if interval is None:
        raise ValueError(f"Unknown timeframe '{timeframe}'. Use one of: {list(TIMEFRAME_MAP)}")

    df      = _fetch_klines(symbol, interval, limit)
    ticker  = _fetch_ticker(symbol)

    close   = df["close"]
    volume  = df["volume"]

    # --- Indicators ---
    ema20   = _ema(close, 20).iloc[-1]
    ema50   = _ema(close, 50).iloc[-1]
    ema200  = _ema(close, 200).iloc[-1]
    rsi14   = _rsi(close, 14).iloc[-1]

    macd_line, signal_line, histogram = _macd(close)
    macd_val  = macd_line.iloc[-1]
    signal_val = signal_line.iloc[-1]
    hist_val  = histogram.iloc[-1]
    hist_prev = histogram.iloc[-2]

    # --- Price info ---
    last_close  = close.iloc[-1]
    prev_close  = close.iloc[-2]
    pct_change  = (last_close - prev_close) / prev_close * 100

    # --- Volume context ---
    vol_last    = volume.iloc[-1]
    vol_avg20   = volume.iloc[-20:].mean()
    vol_ratio   = vol_last / vol_avg20 if vol_avg20 > 0 else 1.0

    # --- Ticker extras (funding, OI) ---
    funding_rate = ticker.get("fundingRate", "N/A")
    open_interest = ticker.get("openInterestValue", "N/A")
    if funding_rate != "N/A":
        try:
            funding_rate = f"{float(funding_rate) * 100:.4f}%"
        except ValueError:
            pass

    # --- MACD description ---
    if hist_val > 0 and hist_val > hist_prev:
        macd_desc = "pozitif ve yükseliyor (bullish momentum artıyor)"
    elif hist_val > 0 and hist_val <= hist_prev:
        macd_desc = "pozitif ama düşüyor (bullish momentum zayıflıyor)"
    elif hist_val < 0 and hist_val < hist_prev:
        macd_desc = "negatif ve düşüyor (bearish momentum artıyor)"
    else:
        macd_desc = "negatif ama yükseliyor (bearish momentum zayıflıyor)"

    # --- Volume description ---
    if vol_ratio >= 2.0:
        vol_desc = f"çok yüksek (ortalamanın {vol_ratio:.1f}x üzerinde)"
    elif vol_ratio >= 1.3:
        vol_desc = f"ortalama üzerinde ({vol_ratio:.1f}x)"
    elif vol_ratio >= 0.7:
        vol_desc = f"ortalama civarı ({vol_ratio:.1f}x)"
    else:
        vol_desc = f"düşük (ortalamanın {vol_ratio:.1f}x altı)"

    # --- Price vs EMA ---
    price_vs_ema20  = "üzerinde" if last_close > ema20  else "altında"
    price_vs_ema50  = "üzerinde" if last_close > ema50  else "altında"
    price_vs_ema200 = "üzerinde" if last_close > ema200 else "altında"

    context = f"""Sembol     : {symbol}
Timeframe  : {timeframe.upper()}
Son fiyat  : {last_close:,.2f} USDT  ({pct_change:+.2f}% önceki muma göre)

--- Hareketli Ortalamalar ---
EMA20      : {ema20:,.2f}  (fiyat {price_vs_ema20})
EMA50      : {ema50:,.2f}  (fiyat {price_vs_ema50})
EMA200     : {ema200:,.2f}  (fiyat {price_vs_ema200})

--- Momentum ---
RSI(14)    : {rsi14:.1f}
MACD       : {macd_desc}
  MACD line   : {macd_val:.4f}
  Signal line : {signal_val:.4f}
  Histogram   : {hist_val:.4f}

--- Hacim ---
Son mum hacmi : {vol_last:,.0f}
20 mum ort.   : {vol_avg20:,.0f}
Durum         : {vol_desc}

--- Futures (Bybit Linear) ---
Funding rate  : {funding_rate}
Açık pozisyon : {open_interest}"""

    return context.strip()


__all__ = ["fetch_context", "TIMEFRAME_MAP"]
