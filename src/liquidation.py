"""Likidasyon bölgesi analizi — Oscar (Colab) için bağımsız versiyon."""

from __future__ import annotations

import time
from typing import Any

import requests

BYBIT_BASE = "https://api.bybit.com"


def _get(path: str, params: dict, retries: int = 2) -> dict:
    url = BYBIT_BASE + path
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("retCode", 0) != 0:
                raise RuntimeError(data.get("retMsg"))
            return data["result"]
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(1)
    return {}


def _find_liquidity_clusters(symbol: str, price: float) -> dict:
    try:
        ob = _get("/v5/market/orderbook", {"category": "linear", "symbol": symbol, "limit": 200})
        bids = [(float(p), float(s)) for p, s in ob.get("b", [])]
        asks = [(float(p), float(s)) for p, s in ob.get("a", [])]

        if not bids or not asks:
            return {}

        total_bid = sum(s * p for p, s in bids)
        total_ask = sum(s * p for p, s in asks)
        avg_bid = total_bid / len(bids) if bids else 0
        avg_ask = total_ask / len(asks) if asks else 0

        big_bids = sorted([(p, s * p) for p, s in bids if s * p > avg_bid * 3],
                          key=lambda x: x[1], reverse=True)[:3]
        big_asks = sorted([(p, s * p) for p, s in asks if s * p > avg_ask * 3],
                          key=lambda x: x[1], reverse=True)[:3]

        def pct_away(p):
            return round(abs(p - price) / price * 100, 2)

        return {
            "long_liq_zones":  [{"price": p, "hacim_usd": round(v), "uzaklik_pct": pct_away(p)} for p, v in big_bids],
            "short_liq_zones": [{"price": p, "hacim_usd": round(v), "uzaklik_pct": pct_away(p)} for p, v in big_asks],
            "bid_ask_ratio":   round(total_bid / total_ask, 2) if total_ask > 0 else 1.0,
        }
    except Exception:
        return {}


def _oi_change_rate(symbol: str) -> dict:
    try:
        result = _get("/v5/market/open-interest", {
            "category": "linear", "symbol": symbol,
            "intervalTime": "5min", "limit": 12,
        })
        history = result.get("list", [])
        if len(history) < 3:
            return {"oi_degisim_pct": 0.0, "cascade_riski": "bilinmiyor"}

        latest = float(history[0]["openInterest"])
        oldest = float(history[-1]["openInterest"])
        degisim_pct = round((latest - oldest) / oldest * 100, 2) if oldest > 0 else 0.0

        cascade = ("YÜKSEK" if degisim_pct < -3 else
                   "ORTA"   if degisim_pct < -1 else
                   "birikim" if degisim_pct > 2 else "düşük")

        return {"oi_son": round(latest), "oi_1s_once": round(oldest),
                "oi_degisim_pct": degisim_pct, "cascade_riski": cascade}
    except Exception:
        return {"oi_degisim_pct": 0.0, "cascade_riski": "bilinmiyor"}


def _stress_score(funding: float, oi_change: float, bid_ask_ratio: float) -> dict:
    score = 0
    funding_pct = abs(funding) * 100
    if funding_pct > 0.05:  score += 3
    elif funding_pct > 0.02: score += 1
    if oi_change < -3:      score += 4
    elif oi_change < -1:    score += 2
    if bid_ask_ratio < 0.7 or bid_ask_ratio > 1.4:  score += 2
    elif bid_ask_ratio < 0.85 or bid_ask_ratio > 1.2: score += 1
    score = min(score, 10)
    seviye = "kritik" if score >= 7 else "yüksek" if score >= 4 else "normal"
    return {"stres_skoru": score, "stres_seviyesi": seviye}


def get_liquidation_context(symbol: str, price: float, funding: float = 0.0) -> dict:
    clusters = _find_liquidity_clusters(symbol, price)
    oi_info  = _oi_change_rate(symbol)
    bar      = clusters.get("bid_ask_ratio", 1.0)
    stress   = _stress_score(funding, oi_info.get("oi_degisim_pct", 0), bar)
    return {**clusters, **oi_info, **stress}


def format_for_oscar(liq: dict, symbol: str) -> str:
    if not liq:
        return ""

    lines = [f"\n── LİKİDASYON ANALİZİ ({symbol}) ──"]

    cascade = liq.get("cascade_riski", "")
    if cascade == "YÜKSEK":
        lines.append("⚠️  CASCADE RİSKİ YÜKSEK — OI hızla düşüyor.")
    elif cascade == "ORTA":
        lines.append("⚡ OI düşüyor — cascade riski var.")
    elif cascade == "birikim":
        lines.append("📈 OI artıyor — büyük oyuncu pozisyon açıyor.")

    stres = liq.get("stres_skoru", 0)
    lines.append(f"Piyasa stres skoru: {stres}/10 ({liq.get('stres_seviyesi', '?')})")

    long_zones = liq.get("long_liq_zones", [])
    if long_zones:
        z = long_zones[0]
        lines.append(f"En büyük LONG havuzu: ${z['price']:,.1f} (${z['hacim_usd']:,} — %{z['uzaklik_pct']} uzakta)")

    short_zones = liq.get("short_liq_zones", [])
    if short_zones:
        z = short_zones[0]
        lines.append(f"En büyük SHORT havuzu: ${z['price']:,.1f} (${z['hacim_usd']:,} — %{z['uzaklik_pct']} uzakta)")

    oi_deg = liq.get("oi_degisim_pct", 0)
    lines.append(f"OI 1 saatlik değişim: %{oi_deg:+.2f}")

    return "\n".join(lines)
