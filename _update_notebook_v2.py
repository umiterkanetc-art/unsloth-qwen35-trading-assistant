"""Notebook'u v2 mimarisine guncelle:
- Cell 24 (oscar_signal): KOSUL blogu parse desteği
- Step 13: Oscar karar motoru (triggers.json okur, GIR/PAS/IPTAL)
- drive.py helpers notebook'a ekle (load_triggers, set_trigger_decision)
"""
import json

nb = json.load(open("setup.ipynb", encoding="utf-8"))


# ─── Cell 24: oscar_signal v2 ─────────────────────────────────────────────

OSCAR_SIGNAL_V2 = r'''import re
from datetime import datetime, timezone

def _utcnow():
    return datetime.now(timezone.utc).isoformat()

def _to_float(s):
    s = str(s).strip().replace(",", "").replace("$", "").replace(" ", "")
    if s.lower().endswith("k"): return float(s[:-1]) * 1000
    if s.lower().endswith("m"): return float(s[:-1]) * 1_000_000
    return float(s)

def _parse_kosul_block(analysis: str) -> dict:
    """```KOSUL ... ``` blogunu parse et."""
    m = re.search(r"```KOSUL\n(.+?)```", analysis, re.DOTALL | re.IGNORECASE)
    if not m:
        return {}
    block = m.group(1)
    result = {}
    for line in block.strip().splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip().upper()] = val.strip()
    return result

def _parse_signal(analysis: str, symbol: str) -> dict | None:
    """Oscar analiz metninden sinyal cikar — once KOSUL blogu, sonra regex."""
    NUM = r"[$]?[\d][\d,.]*[kKmM]?"

    kb = _parse_kosul_block(analysis)

    def kb_float(key):
        try: return _to_float(kb[key]) if key in kb else None
        except: return None

    yon         = kb.get("YON", "").upper() or None
    entry       = kb_float("ENTRY")
    stop        = kb_float("STOP")
    tp1         = kb_float("HEDEF_1")
    tp2         = kb_float("HEDEF_2")
    kosul_tipi  = kb.get("TIP", "DIRECT").upper()
    kosul_fiyat = kb_float("TETIK") or entry

    if not yon:
        text_lower  = analysis.lower()
        long_score  = text_lower.count("long") + text_lower.count("bullish")
        short_score = text_lower.count("short") + text_lower.count("bearish")
        if   long_score  > short_score: yon = "LONG"
        elif short_score > long_score:  yon = "SHORT"

    def find(patterns):
        for pat in patterns:
            m = re.search(pat, analysis, re.IGNORECASE)
            if m:
                try: return _to_float(m.group(1))
                except: pass
        return None

    if not entry:
        entry = find([r"[Ee]ntry[\s*:]+(" + NUM + ")", r"[Gg]iri[sş][\s*:]+(" + NUM + ")"])
    if not stop:
        stop  = find([r"[Ss]top[\s*:]+(" + NUM + ")", r"\bSL[\s*:]+(" + NUM + ")"])
    if not tp1:
        tp1   = find([r"[Hh]edef\s*1[\s*:]+(" + NUM + ")", r"TP\s*1[\s*:]+(" + NUM + ")"])
    if not tp2:
        tp2   = find([r"[Hh]edef\s*2[\s*:]+(" + NUM + ")", r"TP\s*2[\s*:]+(" + NUM + ")"])

    if not all([yon, entry, stop, tp1]):
        return None

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return {
        "sinyal_id":        f"{symbol}_{ts}",
        "symbol":           symbol,
        "yon":              yon,
        "entry":            entry,
        "stop":             stop,
        "hedef_1":          tp1,
        "hedef_2":          tp2 or tp1,
        "kosul_tipi":       kosul_tipi,
        "kosul_fiyat":      kosul_fiyat,
        "durum":            "bekliyor",
        "analiz":           analysis,
        "olusturma_zamani": _utcnow(),
    }


def _build_context_from_cache(symbol: str) -> str:
    md = load_market_data()
    if symbol not in md:
        return ""
    d = md[symbol]
    lines = [f"Sembol: {symbol}"]
    for tf, tfd in d.get("timeframes", {}).items():
        lines.append(f"\n── {tf.upper()} ─────────────")
        lines.append(f"Fiyat   : {tfd.get('price', 0):.2f}")
        lines.append(f"RSI14   : {tfd.get('rsi14', 0):.1f}")
        lines.append(f"ATR14   : {tfd.get('atr14', 0):.4f}")
        lines.append(f"EMA bias: {tfd.get('ema_bias', '?')}")
        lines.append(f"MACD hist: {tfd.get('macd_hist', 0):.4f}")
    try:
        funding_pct = float(d.get("funding_rate", 0)) * 100
        lines.append(f"\nFunding : {funding_pct:.4f}%")
    except Exception:
        pass
    lines.append(f"OI      : {d.get('open_interest', 'N/A')}")
    lines.append(f"Veri ts : {d.get('ts', 'N/A')}")
    return "\n".join(lines)


def oscar_signal(symbol: str, timeframe: str = "4h", soru: str = "") -> dict | None:
    if not soru:
        soru = (
            "Bu sembol icin net bir trade sinyali ver. "
            "Entry, stop ve iki hedef belirt. "
            "KOSUL blogunu mutlaka doldur."
        )

    ctx = _build_context_from_cache(symbol)
    if not ctx:
        from src.market_data import fetch_multi_tf_context
        print(f"[{symbol}] Cache yok — canli veri cekiliyor...")
        ctx = fetch_multi_tf_context(symbol)

    print(f"[{symbol}] Oscar analiz yapiyor...")
    analiz = chat(soru, market_context=ctx, reset=True)
    print("\n" + analiz)
    print("─" * 55)

    sinyal = _parse_signal(analiz, symbol)
    if sinyal:
        save_signal(sinyal)
        print(f"\n OK Sinyal Drive'a yazildi: {sinyal['sinyal_id']}")
        print(f"   {sinyal['yon']}  Entry:{sinyal['entry']}  Stop:{sinyal['stop']}")
        print(f"   TP1:{sinyal['hedef_1']}  TP2:{sinyal['hedef_2']}")
        print(f"   Kosul: {sinyal['kosul_tipi']} @ {sinyal['kosul_fiyat']}")
    else:
        print("\n UYARI Sinyal parse edilemedi.")
    return sinyal


print("OK oscar_signal() v2 hazir — kosul destekli")
'''

nb["cells"][24]["source"] = OSCAR_SIGNAL_V2


# ─── Step 9 hücresine load_triggers / set_trigger_decision ekle ──────────
# Cell 22: Drive baglantisi — sonuna trigger fonksiyonlarini ekle

TRIGGER_HELPERS = '''

# ── Trigger (Oscar karar kuyruğu) ─────────────────────────────────────────
TRIGGERS_FILE = DRIVE_DIR / "triggers.json"

def load_triggers() -> dict:
    if not TRIGGERS_FILE.exists():
        return {}
    try:
        return json.loads(TRIGGERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def set_trigger_decision(sinyal_id: str, karar: str) -> None:
    """Oscar kararini triggers.json'a yaz: GIR / PAS / IPTAL."""
    triggers = load_triggers()
    if sinyal_id in triggers:
        triggers[sinyal_id]["karar"]        = karar
        triggers[sinyal_id]["karar_zamani"] = datetime.utcnow().isoformat()
        TRIGGERS_FILE.write_text(
            json.dumps(triggers, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"[{sinyal_id}] Karar yazildi: {karar}")
    else:
        print(f"[{sinyal_id}] Trigger bulunamadi.")

print("OK Trigger yardimcilari hazir.")
'''

cell22_src = nb["cells"][22]["source"]
if isinstance(cell22_src, str):
    cell22_src = cell22_src
else:
    cell22_src = "".join(cell22_src)

if "load_triggers" not in cell22_src:
    nb["cells"][22]["source"] = cell22_src + TRIGGER_HELPERS


# ─── Step 13: Oscar karar motoru ─────────────────────────────────────────

def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text}

def code(text):
    return {"cell_type": "code", "execution_count": None,
            "metadata": {}, "outputs": [], "source": text}


STEP13_MD = md("""---
## Step 13 — Oscar Karar Motoru

Duman bir sinyal kosulu olusturduğunda `triggers.json`'a yazar.
Bu hucre arka planda calisarak tetikleyicileri kontrol eder.
Oscar guncel piyasaya bakarak: **GIR / PAS / IPTAL** karar verir.""")


STEP13_CODE = code('''import time as _time
import threading as _threading

def oscar_decide_trigger(trigger: dict) -> str:
    """Tetiklenmis sinyal icin Oscar GIR/PAS/IPTAL kararı verir."""
    sid         = trigger["sinyal_id"]
    sym         = trigger.get("symbol", "")
    yon         = trigger.get("yon", "")
    analiz_ozet = trigger.get("analiz", "")[:400]
    ctx         = _build_context_from_cache(sym)

    prompt = f"""Daha once {sym} icin bir sinyal kurmuştun.
Simdi giris kosulu olustu. Guncel piyasaya bak ve karar ver.

Orijinal analizin (ozet):
{analiz_ozet}

Sinyal detaylari:
Yon    : {yon}
Entry  : {trigger.get("entry")}
Stop   : {trigger.get("stop")}
Hedef1 : {trigger.get("hedef_1")}
Hedef2 : {trigger.get("hedef_2")}
Kosul  : {trigger.get("kosul_tipi")} @ {trigger.get("kosul_fiyat")}

Guncel piyasa:
{ctx}

Karar ver — sadece su uctan birini yaz ve 2 cumleyle acikla:
GIR   — kosullar hala gecerli, isleme gir
PAS   — kosul olustu ama setup bozuldu, bu sinyali atla
IPTAL — analiz tamamen gecersiz, sinyali sil"""

    karar_text = chat(prompt, thinking=True, reset=True)
    print(f"[{sid}] Oscar karar metni:\\n{karar_text[:300]}")

    ku = karar_text.upper()
    if "GIR" in ku or "GİR" in ku:
        return "GİR"
    elif "IPTAL" in ku or "İPTAL" in ku:
        return "İPTAL"
    else:
        return "PAS"


def _decision_loop(check_interval: int = 30):
    """Arka plan dongusu — tetikleyici gelince Oscar karar verir."""
    print("Oscar karar motoru baslatildi.")
    while True:
        try:
            triggers = load_triggers()
            pending  = {sid: t for sid, t in triggers.items()
                        if t.get("karar") is None}
            if pending:
                print(f"{len(pending)} bekleyen karar...")
                for sid, trigger in pending.items():
                    try:
                        karar = oscar_decide_trigger(trigger)
                        set_trigger_decision(sid, karar)
                    except Exception as e:
                        print(f"[{sid}] Karar hatasi: {e}")
        except Exception as e:
            print(f"Karar dongusu hatasi: {e}")
        _time.sleep(check_interval)


_threading.Thread(target=_decision_loop, daemon=True).start()
print("OK Oscar karar motoru arka planda calisiyor.")
print("   Siradaki adim: run_auto_loop() ile taramayı baslat.")
''')

# Step 13'u Step 12 oncesine ekle (index 28 ve 29 Step 12'dir)
nb["cells"].insert(28, STEP13_CODE)
nb["cells"].insert(28, STEP13_MD)

with open("setup.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"OK: {len(nb['cells'])} hucre toplam")
print("Degisiklikler:")
print("  - Cell 24: oscar_signal() v2 (KOSUL blogu parse)")
print("  - Cell 22: load_triggers() + set_trigger_decision() eklendi")
print("  - Cell 28-29: Step 13 Oscar karar motoru (yeni)")
