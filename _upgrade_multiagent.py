"""
Multi-agent Oscar + 15 coin + pre-filter tarama sistemi.
Cell 2 (Baslat): chat() fonksiyonuna system_override ekle + 4 ajan fonksiyonu
Cell 3 (Calistir): COINS_TO_SCAN guncelle + multi-agent scan loop
"""
import json, re

nb = json.load(open("setup.ipynb", encoding="utf-8"))

# ─────────────────────────────────────────────────────────────────────────────
# CELL 2 — multi-agent fonksiyonlari ekle
# ─────────────────────────────────────────────────────────────────────────────
src2 = nb["cells"][4]["source"]
if isinstance(src2, list):
    src2 = "".join(src2)

# Chat fonksiyonunu bul — system_override parametresi ekle
OLD_CHAT_DEF = 'def chat(prompt, market_context="", reset=False, thinking=True):'
NEW_CHAT_DEF = 'def chat(prompt, market_context="", reset=False, thinking=True, system_override=None):'

OLD_CHAT_MSGS = '    messages = build_trading_messages(prompt, market_context, history=None if reset else conversation_history)'
NEW_CHAT_MSGS = '    messages = build_trading_messages(prompt, market_context, history=None if reset else conversation_history, system_override=system_override)'

if OLD_CHAT_DEF in src2:
    src2 = src2.replace(OLD_CHAT_DEF, NEW_CHAT_DEF)
    print("OK: chat() system_override parametresi eklendi")
else:
    print("UYARI: chat() fonksiyonu bulunamadi — manuel kontrol gerekli")

if OLD_CHAT_MSGS in src2:
    src2 = src2.replace(OLD_CHAT_MSGS, NEW_CHAT_MSGS)
    print("OK: chat() mesaj olusturucu guncellendi")

# Multi-agent fonksiyonlarini dosyanin sonuna ekle (run_auto_loop'tan once)
MULTI_AGENT_CODE = '''

# ── Multi-Agent Oscar ─────────────────────────────────────────────────────────
from src.trading_prompt import (
    TECH_AGENT_PROMPT, DERIV_AGENT_PROMPT,
    LIQ_AGENT_PROMPT, META_AGENT_PROMPT, PREFILTER_PROMPT
)

def _extract_score(text: str) -> int:
    """SKOR: X satirindan skoru cek."""
    m = re.search(r"SKOR\\s*:\\s*(\\d+)", text)
    return int(m.group(1)) if m else 0

def _extract_direction(text: str) -> str:
    m = re.search(r"YON\\s*:\\s*(LONG|SHORT|TARAFSIZ)", text)
    return m.group(1) if m else "TARAFSIZ"

def oscar_prefilter(symbol: str, ctx: str) -> tuple[int, str]:
    """Hizli on eleme — 5 saniye, thinking=False."""
    soru = f"{symbol} icin hizli tarama yap."
    result = chat(soru, market_context=ctx, reset=True,
                  thinking=False, system_override=PREFILTER_PROMPT)
    score = _extract_score(result)
    direction = _extract_direction(result)
    return score, direction

def oscar_signal_v2(symbol: str) -> dict | None:
    """
    Multi-agent sinyal uretici.
    1. Pre-filter (hizli) — skor < 6 ise atla
    2. Teknik Ajan (ICT/SMC)
    3. Turev Ajani (Funding/OI/CVD)
    4. Likit Ajani (Cascade/Sweep)
    5. Meta-Oscar (sentez + KOSUL)
    """
    import sys
    sys.path.insert(0, REPO_DIR)
    from src.market_data import fetch_multi_tf_context
    from src.liquidation import get_liquidation_context, format_for_oscar

    # Piyasa verisi cek
    try:
        ctx = fetch_multi_tf_context(symbol)
    except Exception as e:
        print(f"[{symbol}] Veri hatasi: {e}")
        return None

    # Likidasyon verisi
    try:
        price_match = re.search(r"Son fiyat[^:]*:\\s*([\\d.]+)", ctx)
        price = float(price_match.group(1)) if price_match else 0.0
        liq = get_liquidation_context(symbol, price, funding=0.0)
        liq_text = format_for_oscar(liq, symbol)
    except Exception:
        liq_text = ""

    # 1. Pre-filter
    score, direction = oscar_prefilter(symbol, ctx)
    print(f"  [{symbol}] Pre-filter: {score}/10 — {direction}")
    if score < 6:
        return None

    ctx_with_liq = ctx + ("\\n\\n" + liq_text if liq_text else "")

    # 2. Teknik Ajan
    tech = chat(
        f"{symbol} teknik analiz yap.",
        market_context=ctx, reset=True,
        thinking=False, system_override=TECH_AGENT_PROMPT
    )

    # 3. Turev Ajani
    deriv = chat(
        f"{symbol} turev piyasasi analizi yap.",
        market_context=ctx, reset=True,
        thinking=False, system_override=DERIV_AGENT_PROMPT
    )

    # 4. Likidasyon Ajani
    liq_analysis = chat(
        f"{symbol} likidasyon cascade analizi yap.",
        market_context=ctx_with_liq, reset=True,
        thinking=False, system_override=LIQ_AGENT_PROMPT
    )

    # 5. Meta-Oscar sentez (thinking=True)
    sentez = (
        f"SEMBOL: {symbol}\\n\\n"
        f"=== TEKNİK AJAN ===\\n{tech}\\n\\n"
        f"=== TÜREV AJANI ===\\n{deriv}\\n\\n"
        f"=== LİKİDASYON AJANI ===\\n{liq_analysis}"
    )
    final = chat(
        f"{symbol} icin 3 ajan raporunu sentezle ve nihai karar ver.",
        market_context=sentez, reset=True,
        thinking=True, system_override=META_AGENT_PROMPT
    )

    print(f"  [{symbol}] Meta-Oscar cevabi alindi")

    # KOSUL blogunu parse et
    m = re.search(r"```KOSUL[ \\t]*\\n(.+?)```", final, re.DOTALL)
    if not m:
        print(f"  [{symbol}] KOSUL blogu bulunamadi")
        return None

    lines = m.group(1).strip().splitlines()
    kosul = {}
    for line in lines:
        if ":" in line:
            k, _, v = line.partition(":")
            kosul[k.strip()] = v.strip()

    if kosul.get("TIP") in (None, "NONE", ""):
        print(f"  [{symbol}] KAÇIN/BEKLE — sinyal yok")
        return None

    try:
        return {
            "symbol":      symbol,
            "yon":         kosul.get("YON", ""),
            "kosul_tipi":  kosul.get("TIP", "DIRECT"),
            "kosul_fiyat": float(kosul.get("TETIK", "0") or "0"),
            "entry":       float(kosul.get("ENTRY", "0") or "0"),
            "stop":        float(kosul.get("STOP", "0") or "0"),
            "hedef_1":     float(kosul.get("HEDEF_1", "0") or "0"),
            "hedef_2":     float(kosul.get("HEDEF_2", "0") or "0"),
            "analiz":      final,
            "prefilter_score": score,
        }
    except ValueError as e:
        print(f"  [{symbol}] Parse hatasi: {e}")
        return None

print("Multi-agent Oscar hazir.")
'''

# Hucre 2'nin sonuna ekle
if "oscar_signal_v2" not in src2:
    src2 = src2.rstrip() + "\n" + MULTI_AGENT_CODE
    print("OK: Multi-agent fonksiyonlar eklendi")
else:
    print("INFO: Multi-agent zaten mevcut")

nb["cells"][4]["source"] = src2

# ─────────────────────────────────────────────────────────────────────────────
# CELL 3 — 15 coin + pre-filter + v2 scan loop
# ─────────────────────────────────────────────────────────────────────────────
src3 = nb["cells"][6]["source"]
if isinstance(src3, list):
    src3 = "".join(src3)

# COINS_TO_SCAN guncelle
OLD_COINS = re.search(r"COINS_TO_SCAN\s*=\s*\[.*?\]", src3, re.DOTALL)
NEW_COINS = """COINS_TO_SCAN = [
    # Buyuk cap
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    # Orta cap
    "AVAXUSDT", "DOGEUSDT", "ADAUSDT", "LINKUSDT", "DOTUSDT",
    # Yuksek volatilite
    "INJUSDT", "SUIUSDT", "NEARUSDT", "ATOMUSDT", "LTCUSDT",
]"""

if OLD_COINS:
    src3 = src3[:OLD_COINS.start()] + NEW_COINS + src3[OLD_COINS.end():]
    print("OK: COINS_TO_SCAN 15 coin ile guncellendi")
else:
    print("UYARI: COINS_TO_SCAN bulunamadi")

# oscar_signal cagrilarini oscar_signal_v2 ile degistir
src3 = src3.replace("oscar_signal(sym)", "oscar_signal_v2(sym)")
src3 = src3.replace("sig = oscar_signal(", "sig = oscar_signal_v2(")
print("OK: oscar_signal -> oscar_signal_v2")

# _scan_all log mesajini guncelle
src3 = src3.replace(
    'print(f"[{sym}] Hata: {e}")',
    'print(f"  [{sym}] Hata: {e}")'
)

nb["cells"][6]["source"] = src3

# ─────────────────────────────────────────────────────────────────────────────
with open("setup.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("\nKaydedildi.")
print("Degisiklikler:")
print("  - 4 ajan prompt (Teknik/Turev/Likidasyon/Meta) trading_prompt.py'a eklendi")
print("  - chat() system_override destegi kazandi")
print("  - oscar_signal_v2() multi-agent akis eklendi")
print("  - COINS_TO_SCAN: 5 -> 15 coin")
print("  - Tarama: pre-filter (hizli) -> sadece skoru yuksek coinler derin analiz")
