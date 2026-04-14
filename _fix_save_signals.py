"""_scan_all'a Drive kaydetme + duplicate run_auto_loop duzelt."""
import json

nb = json.load(open("setup.ipynb", encoding="utf-8"))
src = nb["cells"][6]["source"]
if isinstance(src, list):
    src = "".join(src)

# 1. _scan_all icine add_signal ekle
OLD_SCAN = '''\
def _scan_all() -> list[dict]:
    """Tum coinleri tara, sinyal uret."""
    signals = []
    for sym in COINS_TO_SCAN:
        try:
            sig = oscar_signal_v2(sym)
            if sig:
                signals.append(sig)
                yon   = sig.get("yon", "?")
                entry = sig.get("entry", "?")
                kosul = sig.get("kosul_tipi", "DIRECT")
                tetik = sig.get("kosul_fiyat", "?")
                _tg(f"📡 <b>Sinyal: {sym}</b>\\nYon: {yon} | Entry: {entry}\\nKosul: {kosul} @ {tetik}")
            else:
                _tg(f"⏩ {sym} — sinyal yok / pas")
            _time.sleep(2)
        except Exception as e:
            print(f"  [{sym}] Hata: {e}")
            _tg(f"⚠️ {sym} analiz hatasi: {e}")
    return signals'''

NEW_SCAN = '''\
def _scan_all() -> list[dict]:
    """Tum coinleri tara, sinyal uret, Drive'a kaydet."""
    import uuid
    signals = []
    for sym in COINS_TO_SCAN:
        try:
            sig = oscar_signal_v2(sym)
            if sig:
                # Drive'a kaydet
                sig["sinyal_id"] = f"{sym}_{uuid.uuid4().hex[:8]}"
                sig["durum"]     = "bekliyor"
                try:
                    add_signal(sig)
                except Exception as de:
                    print(f"  [{sym}] Drive kayit hatasi: {de}")

                signals.append(sig)
                yon   = sig.get("yon", "?")
                entry = sig.get("entry", "?")
                kosul = sig.get("kosul_tipi", "DIRECT")
                tetik = sig.get("kosul_fiyat", "?")
                _tg(f"📡 <b>Sinyal: {sym}</b>\\nYon: {yon} | Entry: {entry}\\nKosul: {kosul} @ {tetik}")
            else:
                _tg(f"⏩ {sym} — sinyal yok / pas")
            _time.sleep(2)
        except Exception as e:
            print(f"  [{sym}] Hata: {e}")
            _tg(f"⚠️ {sym} analiz hatasi: {e}")
    return signals'''

if OLD_SCAN in src:
    src = src.replace(OLD_SCAN, NEW_SCAN)
    print("OK: _scan_all Drive kayit eklendi")
else:
    print("UYARI: _scan_all bulunamadi")

# 2. Duplicate run_auto_loop kaldir
DUPLICATE = '''\


# Baslat
run_auto_loop()'''

if DUPLICATE in src:
    src = src.replace(DUPLICATE, "")
    print("OK: duplicate run_auto_loop kaldirildi")

nb["cells"][6]["source"] = src

with open("setup.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print("Kaydedildi.")
