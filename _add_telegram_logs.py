"""Step 14 (auto loop) ve Step 13 (karar motoru) Telegram bildirimleri ekle."""
import json

nb = json.load(open("setup.ipynb", encoding="utf-8"))


# ── Step 14 guncelle ──────────────────────────────────────────────────────
src30 = nb["cells"][30]["source"]
if isinstance(src30, list):
    src30 = "".join(src30)

# Telegram helper ekle
TELEGRAM_HELPER = '''
# ── Telegram bildirimi (Oscar) ────────────────────────────────────────────
import requests as _requests

def _tg(text: str) -> None:
    """Oscar Telegram bildirimi. Token/chat yoksa sessizce atla."""
    token = "8680964677:AAGp9MHbMKsAZRYH-Z_3yt9wQELCe6MLQYo"
    chat  = "524569814"
    try:
        _requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat, "text": text, "parse_mode": "HTML"},
            timeout=8,
        )
    except Exception:
        pass

'''

# _scan_all fonksiyonuna Telegram ekle
OLD_SCAN = '''def _scan_all() -> list[dict]:
    """Tum coinleri tara, sinyal uret."""
    signals = []
    for sym in COINS_TO_SCAN:
        try:
            sig = oscar_signal(sym)
            if sig:
                signals.append(sig)
            _time.sleep(2)   # model nefes alsin
        except Exception as e:
            print(f"[{sym}] Hata: {e}")
    return signals'''

NEW_SCAN = '''def _scan_all() -> list[dict]:
    """Tum coinleri tara, sinyal uret."""
    signals = []
    for sym in COINS_TO_SCAN:
        try:
            sig = oscar_signal(sym)
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
            print(f"[{sym}] Hata: {e}")
            _tg(f"⚠️ {sym} analiz hatasi: {e}")
    return signals'''

# run_auto_loop fonksiyonuna Telegram ekle
OLD_LOOP = '''    while True:
        cycle += 1
        print(f"\\n--- Tarama #{cycle}  {datetime.utcnow().strftime('%H:%M UTC')} ---")
        try:
            signals = _scan_all()
            print(f"Bu turda {len(signals)} sinyal uretildi.")
        except Exception as e:
            print(f"Tarama hatasi: {e}")'''

NEW_LOOP = '''    while True:
        cycle += 1
        ts = datetime.utcnow().strftime("%H:%M UTC")
        print(f"\\n--- Tarama #{cycle}  {ts} ---")
        _tg(f"🔍 <b>Tarama #{cycle}</b> basliyor — {ts}\\n{len(COINS_TO_SCAN)} coin")
        try:
            signals = _scan_all()
            print(f"Bu turda {len(signals)} sinyal uretildi.")
            _tg(f"✅ Tarama #{cycle} tamamlandi — {len(signals)} sinyal uretildi")
        except Exception as e:
            print(f"Tarama hatasi: {e}")
            _tg(f"❌ Tarama #{cycle} hatasi: {e}")'''

if OLD_SCAN in src30:
    src30 = TELEGRAM_HELPER + src30.replace(OLD_SCAN, NEW_SCAN)
    print("OK: _scan_all Telegram eklendi")
else:
    print("UYARI: _scan_all bulunamadi")

if OLD_LOOP in src30:
    src30 = src30.replace(OLD_LOOP, NEW_LOOP)
    print("OK: run_auto_loop Telegram eklendi")
else:
    print("UYARI: run_auto_loop bulunamadi")

nb["cells"][30]["source"] = src30


# ── Step 13 guncelle — karar Telegram ────────────────────────────────────
src28 = nb["cells"][28]["source"]
if isinstance(src28, list):
    src28 = "".join(src28)

OLD_KARAR = '''                    try:
                        karar = oscar_decide_trigger(trigger)
                        set_trigger_decision(sid, karar)
                        print(f"[{sid}] Karar: {karar}")
                    except Exception as e:
                        print(f"[{sid}] Karar hatasi: {e}")'''

NEW_KARAR = '''                    try:
                        karar = oscar_decide_trigger(trigger)
                        set_trigger_decision(sid, karar)
                        print(f"[{sid}] Karar: {karar}")
                        emoji = "🎯" if karar == "GİR" else ("⏩" if karar == "PAS" else "🚫")
                        sym = trigger.get("symbol", "?")
                        _tg(f"{emoji} <b>Oscar Karari: {karar}</b>\\n{sym} — {trigger.get('yon','?')} @ {trigger.get('entry','?')}")
                    except Exception as e:
                        print(f"[{sid}] Karar hatasi: {e}")
                        _tg(f"⚠️ Karar hatasi [{sid}]: {e}")'''

if OLD_KARAR in src28:
    src28 = src28.replace(OLD_KARAR, NEW_KARAR)
    print("OK: Step 13 Telegram eklendi")
else:
    print("UYARI: Step 13 karar blogu bulunamadi")

nb["cells"][28]["source"] = src28

with open("setup.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Notebook kaydedildi.")
