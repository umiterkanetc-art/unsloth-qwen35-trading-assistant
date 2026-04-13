"""Step 11 (Yansiima Motoru) ve Step 12 (Otomatik Tarama) hucrelerini ekle."""
import json

nb_path = "setup.ipynb"
nb = json.load(open(nb_path, encoding="utf-8"))

def md(text): return {"cell_type":"markdown","metadata":{},"source":text}
def code(text): return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":text}

# ── Step 11 header ────────────────────────────────────────────────────────
step11_md = md("""---
## Step 11 \u2014 Oscar Yansiima Motoru

Kapanan islemleri okur, her biri icin Oscar'dan oz-degerlendirme ister ve Drive'a yazar.
Bu veriler ilerleyen asamada LoRA fine-tuning ham materyali olacak.""")

step11_code = code("""\
def oscar_reflect(trade: dict) -> dict:
    \"\"\"Kapanan bir islem icin Oscar'dan oz-degerlendirme al.\"\"\"
    sid   = trade.get("sinyal_id", "?")
    sym   = trade.get("symbol", "?")
    yon   = trade.get("yon", "?")
    entry = trade.get("entry", "?")
    stop  = trade.get("stop", "?")
    tp1   = trade.get("hedef_1", "?")
    tp2   = trade.get("hedef_2", "?")
    sonuc = trade.get("sonuc", "?")
    r     = trade.get("r_ratio", "?")

    prompt = f\"\"\"Asagidaki kapanmis islemi analiz et ve ne ogrendigini yaz.

Sembol   : {sym}
Yon      : {yon}
Entry    : {entry}
Stop     : {stop}
Hedef 1  : {tp1}
Hedef 2  : {tp2}
Sonuc    : {sonuc}
R Orani  : {r}

Analiz ozeti:
{trade.get('analiz', '')[:500]}

Lutfen asagidaki sorulari yanit ver (toplam max 300 kelime):
1. Bu islemde ne dogru yapildi?
2. Ne yanlis gitti ya da eksikti?
3. Bir sonraki benzer setupta ne farkli yapilmali?
4. Bu coinle ilgili ogrenilenler nelerdir?\"\"\"

    response = chat(prompt, thinking=False)

    reflection = {
        "sinyal_id":  sid,
        "symbol":     sym,
        "yon":        yon,
        "sonuc":      sonuc,
        "r_ratio":    r,
        "yansiima":   response,
        "ts":         datetime.utcnow().isoformat(),
    }
    save_reflection(reflection)
    print(f"[{sid}] Yansiima kaydedildi. Sonuc: {sonuc} | R: {r}")
    return reflection


def reflect_unprocessed(limit: int = 5) -> int:
    \"\"\"Daha once yansiitilmamis kapali islemleri isle.\"\"\"
    history     = load_trade_history()
    reflections = load_reflections()
    reflected   = {r["sinyal_id"] for r in reflections}

    pending = [t for t in history if t.get("sinyal_id") not in reflected]
    if not pending:
        print("Yansiitilacak yeni islem yok.")
        return 0

    print(f"{len(pending)} islem yansiitilacak (limit={limit})...")
    done = 0
    for trade in pending[:limit]:
        try:
            oscar_reflect(trade)
            done += 1
        except Exception as e:
            print(f"Hata [{trade.get('sinyal_id')}]: {e}")
    return done


# Test: mevcut gecmisten yansiit
reflect_unprocessed(limit=3)
""")

# ── Step 12 header ────────────────────────────────────────────────────────
step12_md = md("""---
## Step 12 \u2014 Otomatik Tarama Dongusu

Oscar'i tamamen otomatige alir: her `interval` dakikada bir tum coinleri tarar,
sinyal uretir, yansiimalari isler. Durdurma: hucreyi kesintiye ugrat (Colab interrupt).

> Not: Colab 12 saatlik oturum limitine tabidir. Uzun sure calistirilmak istenirse
> hucreyi surekli izle ya da Google Colab pro aboneligi kullan.""")

step12_code = code("""\
import time as _time

SCAN_INTERVAL_MIN = 60   # dakika: kac dakikada bir tum coinler taransin
COINS_TO_SCAN = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT",
    "XRPUSDT", "DOGEUSDT", "AVAXUSDT", "ADAUSDT",
    "LINKUSDT", "DOTUSDT", "NEARUSDT", "APTUSDT",
]

def _scan_all() -> list[dict]:
    \"\"\"Tum coinleri tara, sinyal uret.\"\"\"
    signals = []
    for sym in COINS_TO_SCAN:
        try:
            sig = oscar_signal(sym)
            if sig:
                signals.append(sig)
            _time.sleep(2)   # model nefes alsin
        except Exception as e:
            print(f"[{sym}] Hata: {e}")
    return signals


def run_auto_loop():
    \"\"\"Tarama dongusu \u2014 Ctrl+C ile durdur.\"\"\"
    print("Otomatik tarama basladi.")
    print(f"Interval: {SCAN_INTERVAL_MIN} dakika | Coins: {len(COINS_TO_SCAN)}")
    cycle = 0
    while True:
        cycle += 1
        print(f"\\n--- Tarama #{cycle}  {datetime.utcnow().strftime('%H:%M UTC')} ---")
        try:
            signals = _scan_all()
            print(f"Bu turda {len(signals)} sinyal uretildi.")
        except Exception as e:
            print(f"Tarama hatasi: {e}")

        # Yansiimalari isle (en fazla 5 adet)
        try:
            reflect_unprocessed(limit=5)
        except Exception as e:
            print(f"Yansiima hatasi: {e}")

        # Aktif sinyal ozeti
        aktif = load_active_signals()
        print(f"Aktif sinyal sayisi: {len(aktif)}")

        print(f"Sonraki tarama {SCAN_INTERVAL_MIN} dakika sonra...")
        _time.sleep(SCAN_INTERVAL_MIN * 60)


# Donguyu baslat (hucreyi kesmek icin Colab interrupt kullan)
run_auto_loop()
""")

new_cells = [step11_md, step11_code, step12_md, step12_code]
nb["cells"].extend(new_cells)

with open(nb_path, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"OK: {len(nb['cells'])} hucre ({len(new_cells)} yeni eklendi)")
