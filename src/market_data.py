"""Bybit V5 market data fetcher — multi-source, multi-timeframe context builder."""

from __future__ import annotations

import requests
import pandas as pd
import math

BYBIT_BASE    = "https://api.bybit.com"
COINGLASS_BASE = "https://open-api.coinglass.com/public/v2"
FNG_URL       = "https://api.alternative.me/fng/"

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

# Timeframe display ordering (smallest → largest)
TF_ORDER = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]


# ─────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────

def _get(url: str, params: dict, timeout: int = 10) -> dict:
    resp = requests.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def _bybit_get(path: str, params: dict) -> dict:
    data = _get(BYBIT_BASE + path, params)
    if data.get("retCode", 0) != 0:
        raise RuntimeError(f"Bybit API error: {data.get('retMsg')} — params={params}")
    return data["result"]


def _fetch_klines(symbol: str, interval: str, limit: int = 200) -> pd.DataFrame:
    result = _bybit_get("/v5/market/kline", {
        "category": "linear",
        "symbol":   symbol,
        "interval": interval,
        "limit":    limit,
    })
    rows = result["list"]
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume", "turnover"])
    df = df.astype({
        "ts": "int64", "open": "float64", "high": "float64",
        "low": "float64", "close": "float64", "volume": "float64",
    })
    return df.sort_values("ts").reset_index(drop=True)


def _fetch_ticker(symbol: str) -> dict:
    result = _bybit_get("/v5/market/tickers", {"category": "linear", "symbol": symbol})
    items = result.get("list", [])
    return items[0] if items else {}


# ─────────────────────────────────────────────
# Indicator calculations
# ─────────────────────────────────────────────

def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, float("inf"))
    return 100 - (100 / (1 + rs))


def _macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast    = _ema(series, fast)
    ema_slow    = _ema(series, slow)
    macd_line   = ema_fast - ema_slow
    signal_line = _ema(macd_line, signal)
    histogram   = macd_line - signal_line
    return macd_line, signal_line, histogram


def _atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, prev_close = df["high"], df["low"], df["close"].shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(com=period - 1, adjust=False).mean()


def _bollinger(series: pd.Series, period: int = 20, std_mult: float = 2.0):
    mid  = series.rolling(period).mean()
    std  = series.rolling(period).std(ddof=0)
    upper = mid + std_mult * std
    lower = mid - std_mult * std
    return upper, mid, lower


# ─────────────────────────────────────────────
# External data sources
# ─────────────────────────────────────────────

def _fetch_fear_greed() -> dict:
    """Fetch Fear & Greed index from alternative.me (no auth required)."""
    try:
        data = _get(FNG_URL, {"limit": 1}, timeout=8)
        entry = data["data"][0]
        return {
            "value":       int(entry["value"]),
            "label":       entry["value_classification"],
            "timestamp":   entry["timestamp"],
        }
    except Exception:
        return {}


def _fetch_liquidation_analysis(symbol: str, price: float, funding: float = 0.0) -> str:
    """Bybit order book'tan likidasyon bölgelerini hesapla."""
    try:
        result = _bybit_get("/v5/market/orderbook", {
            "category": "linear", "symbol": symbol, "limit": 200
        })
        bids = [(float(p), float(s)) for p, s in result.get("b", [])]
        asks = [(float(p), float(s)) for p, s in result.get("a", [])]
        if not bids or not asks:
            return ""

        total_bid = sum(s * p for p, s in bids)
        total_ask = sum(s * p for p, s in asks)
        avg_bid = total_bid / len(bids)
        avg_ask = total_ask / len(asks)

        big_bids = sorted([(p, s*p) for p, s in bids if s*p > avg_bid*3],
                          key=lambda x: x[1], reverse=True)[:2]
        big_asks = sorted([(p, s*p) for p, s in asks if s*p > avg_ask*3],
                          key=lambda x: x[1], reverse=True)[:2]

        bar = round(total_bid / total_ask, 2) if total_ask > 0 else 1.0
        funding_abs = abs(funding) * 100

        lines = ["\n── LİKİDASYON & EMIR KİTABI ────────────"]
        if big_bids:
            p, v = big_bids[0]
            pct = round(abs(p - price) / price * 100, 2)
            lines.append(f"Büyük LONG havuzu : ${p:,.1f}  (${v:,.0f}  —  %{pct} uzakta)")
        if big_asks:
            p, v = big_asks[0]
            pct = round(abs(p - price) / price * 100, 2)
            lines.append(f"Büyük SHORT havuzu: ${p:,.1f}  (${v:,.0f}  —  %{pct} uzakta)")
        lines.append(f"Alış/Satış oranı  : {bar}  {'alıcı baskın' if bar > 1.1 else 'satıcı baskın' if bar < 0.9 else 'dengeli'}")
        if funding_abs > 0.05:
            lines.append(f"Funding riski     : %{funding_abs:.4f} — aşırı, likidasyon cascade olası")
        return "\n".join(lines)
    except Exception:
        return ""


def _fetch_coinglass_ls(symbol: str) -> dict:
    """
    Fetch long/short ratio from Coinglass open public endpoint (no API key).
    Returns dict with top_long_pct, top_short_pct or empty dict on failure.
    """
    # Coinglass open endpoint — coin symbol (BTC, ETH, SOL ...)
    coin = symbol.replace("USDT", "").replace("USDC", "").upper()
    try:
        data = _get(
            f"https://fapi.coinglass.com/api/openInterest/v3/chart",
            {"symbol": coin, "timeType": "0", "exchangeName": "Bybit"},
            timeout=8,
        )
        # Fallback: if this endpoint fails, try alternative
        if not data.get("success"):
            raise ValueError("no data")
        return {}
    except Exception:
        pass

    # Alternative Coinglass public endpoint for long/short
    try:
        data = _get(
            "https://fapi.coinglass.com/api/pro/v1/futures/longShort/chart",
            {"ex": "Bybit", "pair": f"{coin}USDT", "interval": "0", "limit": 1},
            timeout=8,
        )
        if data.get("success") and data.get("data"):
            last = data["data"][-1]
            return {
                "long_pct":  round(float(last.get("longRatio",  0)) * 100, 2),
                "short_pct": round(float(last.get("shortRatio", 0)) * 100, 2),
            }
    except Exception:
        pass

    return {}


# ─────────────────────────────────────────────
# Single-timeframe context block
# ─────────────────────────────────────────────

def _build_tf_block(symbol: str, timeframe: str, limit: int = 200) -> str:
    """Build indicator summary for a single timeframe."""
    interval = TIMEFRAME_MAP.get(timeframe.lower())
    if interval is None:
        raise ValueError(f"Bilinmeyen timeframe '{timeframe}'. Seçenekler: {list(TIMEFRAME_MAP)}")

    df     = _fetch_klines(symbol, interval, limit)
    close  = df["close"]
    volume = df["volume"]

    # EMAs
    ema20  = _ema(close, 20).iloc[-1]
    ema50  = _ema(close, 50).iloc[-1]
    ema200 = _ema(close, 200).iloc[-1]

    # RSI
    rsi14 = _rsi(close, 14).iloc[-1]
    rsi_prev = _rsi(close, 14).iloc[-2]
    rsi_div = "yükseliyor" if rsi14 > rsi_prev else "düşüyor"

    # MACD
    macd_line, signal_line, histogram = _macd(close)
    hist_val  = histogram.iloc[-1]
    hist_prev = histogram.iloc[-2]
    hist_slope = hist_val - hist_prev

    # ATR
    atr_val = _atr(df, 14).iloc[-1]
    atr_pct = (atr_val / close.iloc[-1]) * 100

    # Bollinger Bands
    bb_upper, bb_mid, bb_lower = _bollinger(close, 20, 2.0)
    bb_u = bb_upper.iloc[-1]
    bb_l = bb_lower.iloc[-1]
    bb_m = bb_mid.iloc[-1]
    bb_width = (bb_u - bb_l) / bb_m * 100  # band genişliği %
    price_in_bb = (close.iloc[-1] - bb_l) / (bb_u - bb_l) * 100  # 0-100 arası konum

    # Price change
    last_close = close.iloc[-1]
    prev_close = close.iloc[-2]
    pct_change = (last_close - prev_close) / prev_close * 100

    # Volume
    vol_last   = volume.iloc[-1]
    vol_avg20  = volume.iloc[-20:].mean()
    vol_ratio  = vol_last / vol_avg20 if vol_avg20 > 0 else 1.0

    # EMA alignment
    ema_bull  = last_close > ema20 > ema50 > ema200
    ema_bear  = last_close < ema20 < ema50 < ema200
    ema_state = "tam bullish dizilim ✅" if ema_bull else ("tam bearish dizilim ❌" if ema_bear else "karışık dizilim ↔️")

    # Descriptions
    if hist_val > 0 and hist_slope > 0:
        macd_desc = "pozitif ↑ bullish momentum artıyor"
    elif hist_val > 0 and hist_slope <= 0:
        macd_desc = "pozitif ↓ bullish momentum zayıflıyor"
    elif hist_val < 0 and hist_slope < 0:
        macd_desc = "negatif ↓ bearish momentum artıyor"
    else:
        macd_desc = "negatif ↑ bearish momentum zayıflıyor"

    if vol_ratio >= 2.0:
        vol_desc = f"çok yüksek ({vol_ratio:.1f}x ort.)"
    elif vol_ratio >= 1.3:
        vol_desc = f"ort. üzerinde ({vol_ratio:.1f}x)"
    elif vol_ratio >= 0.7:
        vol_desc = f"normal ({vol_ratio:.1f}x)"
    else:
        vol_desc = f"zayıf ({vol_ratio:.1f}x)"

    # RSI zone
    if rsi14 >= 70:
        rsi_zone = "aşırı alım ⚠️"
    elif rsi14 <= 30:
        rsi_zone = "aşırı satım ⚠️"
    elif rsi14 >= 55:
        rsi_zone = "bullish bölge"
    elif rsi14 <= 45:
        rsi_zone = "bearish bölge"
    else:
        rsi_zone = "nötr"

    # BB position description
    if price_in_bb >= 90:
        bb_desc = f"üst banda dayanıyor ({price_in_bb:.0f}%)"
    elif price_in_bb <= 10:
        bb_desc = f"alt banda dayanıyor ({price_in_bb:.0f}%)"
    else:
        bb_desc = f"band içi konum {price_in_bb:.0f}% (alt=0, üst=100)"

    block = f"""── {timeframe.upper()} ──────────────────────────────
Son Fiyat   : {last_close:,.2f} USDT  ({pct_change:+.2f}%)
EMA Durumu  : {ema_state}
  EMA20={ema20:,.2f}  EMA50={ema50:,.2f}  EMA200={ema200:,.2f}

RSI(14)     : {rsi14:.1f} [{rsi_zone}] — {rsi_div}
MACD hist   : {macd_desc}
  MACD={macd_line.iloc[-1]:.4f}  Sinyal={signal_line.iloc[-1]:.4f}  Hist={hist_val:.4f}

ATR(14)     : {atr_val:,.2f}  ({atr_pct:.2f}% fiyatın) — stop referansı
BB(20,2)    : Üst={bb_u:,.2f}  Orta={bb_m:,.2f}  Alt={bb_l:,.2f}
  Bant genişliği {bb_width:.1f}%  |  {bb_desc}

Hacim       : {vol_desc}  (son={vol_last:,.0f}  ort20={vol_avg20:,.0f})"""

    return block.strip()


# ─────────────────────────────────────────────
# Public API: single-timeframe context
# ─────────────────────────────────────────────

def fetch_context(
    symbol: str,
    timeframe: str = "4h",
    limit: int = 200,
    include_sentiment: bool = True,
) -> str:
    """
    Fetch live market data from Bybit and return a formatted market_context string.

    Parameters
    ----------
    symbol             : e.g. "BTCUSDT", "ETHUSDT", "SOLUSDT"
    timeframe          : "1m","5m","15m","30m","1h","4h","1d","1w"
    limit              : Candle count (min 200 recommended for indicator warmup)
    include_sentiment  : Whether to include Fear & Greed + Coinglass data

    Returns
    -------
    str : Formatted context block ready for chat().
    """
    ticker = _fetch_ticker(symbol)

    # Futures extras
    funding_raw   = ticker.get("fundingRate", "")
    open_interest = ticker.get("openInterestValue", "N/A")
    mark_price    = ticker.get("markPrice", "N/A")
    index_price   = ticker.get("indexPrice", "N/A")

    try:
        funding_pct = f"{float(funding_raw) * 100:.4f}%"
        funding_val = float(funding_raw) * 100
        if funding_val > 0.05:
            funding_note = "⚠️ yüksek pozitif — long maliyetli, short avantajlı"
        elif funding_val < -0.05:
            funding_note = "⚠️ yüksek negatif — short maliyetli, long avantajlı"
        elif funding_val > 0:
            funding_note = "nötr-pozitif"
        else:
            funding_note = "nötr-negatif"
    except (ValueError, TypeError):
        funding_pct  = funding_raw or "N/A"
        funding_note = ""

    lines = [f"Sembol: {symbol}"]

    # TF block
    lines.append("\n" + _build_tf_block(symbol, timeframe, limit))

    # Futures block
    lines.append(f"""
── FUTURES (Bybit Linear) ──────────────────
Funding rate  : {funding_pct}  {funding_note}
Açık pozisyon : {open_interest} USDT
Mark price    : {mark_price}
Index price   : {index_price}""")

    # Sentiment block
    if include_sentiment:
        fng = _fetch_fear_greed()
        if fng:
            fng_val   = fng["value"]
            fng_label = fng["label"]
            if fng_val >= 75:
                fng_note = "⚠️ aşırı açgözlülük — zirve riski"
            elif fng_val >= 60:
                fng_note = "dikkatli ol"
            elif fng_val <= 25:
                fng_note = "⚠️ aşırı korku — potansiyel dip"
            elif fng_val <= 40:
                fng_note = "temkinli"
            else:
                fng_note = "nötr"
            lines.append(f"""
── SENTIMENT ────────────────────────────────
Fear & Greed  : {fng_val}/100 — {fng_label}  [{fng_note}]""")

        ls = _fetch_coinglass_ls(symbol)
        if ls:
            lines.append(
                f"Long/Short    : Long {ls['long_pct']:.1f}%  |  Short {ls['short_pct']:.1f}%"
            )

    return "\n".join(lines).strip()


# ─────────────────────────────────────────────
# Public API: multi-timeframe context
# ─────────────────────────────────────────────

def fetch_multi_tf_context(
    symbol: str,
    timeframes: list[str] | None = None,
    limit: int = 200,
    include_sentiment: bool = True,
) -> str:
    """
    Fetch and combine multiple timeframe snapshots for a symbol.
    Ideal for full structural analysis: pass to chat() as market_context.

    Parameters
    ----------
    symbol      : e.g. "BTCUSDT"
    timeframes  : List of TFs to include, default ["1d", "4h", "1h"]
    limit       : Candle count per TF

    Returns
    -------
    str : Multi-TF market context block.
    """
    if timeframes is None:
        timeframes = ["1d", "4h", "1h"]

    ticker = _fetch_ticker(symbol)

    funding_raw   = ticker.get("fundingRate", "")
    open_interest = ticker.get("openInterestValue", "N/A")
    mark_price    = ticker.get("markPrice", "N/A")

    try:
        funding_pct = f"{float(funding_raw) * 100:.4f}%"
        funding_val = float(funding_raw) * 100
        if funding_val > 0.05:
            funding_note = "⚠️ yüksek pozitif — long maliyetli"
        elif funding_val < -0.05:
            funding_note = "⚠️ yüksek negatif — short maliyetli"
        elif funding_val > 0:
            funding_note = "nötr-pozitif"
        else:
            funding_note = "nötr-negatif"
    except (ValueError, TypeError):
        funding_pct  = funding_raw or "N/A"
        funding_note = ""

    sections = [f"╔══ {symbol} — ÇOKLU ZAMAN DİLİMİ ANALİZİ ══╗\n"]

    for tf in timeframes:
        try:
            block = _build_tf_block(symbol, tf, limit)
            sections.append(block)
        except Exception as e:
            sections.append(f"── {tf.upper()} — veri alınamadı: {e}")

    sections.append(f"""
── FUTURES (Bybit Linear) ──────────────────
Funding rate  : {funding_pct}  {funding_note}
Açık pozisyon : {open_interest} USDT
Mark price    : {mark_price}""")

    # Likidasyon analizi
    try:
        current_price = float(ticker.get("lastPrice", 0))
        funding_val_raw = float(ticker.get("fundingRate", 0))
        liq_block = _fetch_liquidation_analysis(symbol, current_price, funding_val_raw)
        if liq_block:
            sections.append(liq_block)
    except Exception:
        pass

    if include_sentiment:
        fng = _fetch_fear_greed()
        if fng:
            fng_val   = fng["value"]
            fng_label = fng["label"]
            if fng_val >= 75:
                fng_note = "⚠️ aşırı açgözlülük"
            elif fng_val <= 25:
                fng_note = "⚠️ aşırı korku"
            else:
                fng_note = ""
            sections.append(f"""
── SENTIMENT ────────────────────────────────
Fear & Greed  : {fng_val}/100 — {fng_label}  {fng_note}""")

        ls = _fetch_coinglass_ls(symbol)
        if ls:
            sections[-1] += f"\nLong/Short    : Long {ls['long_pct']:.1f}%  |  Short {ls['short_pct']:.1f}%"

    return "\n".join(sections).strip()


__all__ = ["fetch_context", "fetch_multi_tf_context", "TIMEFRAME_MAP"]
