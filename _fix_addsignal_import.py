"""Cell 3 basina add_signal import ekle."""
import json

nb = json.load(open("setup.ipynb", encoding="utf-8"))
src = nb["cells"][6]["source"]
if isinstance(src, list):
    src = "".join(src)

IMPORT = """\
# ── Drive fonksiyonlari ───────────────────────────────────────────────────
import sys
sys.path.insert(0, REPO_DIR)
from src.drive_oscar import add_signal, load_active_signals, save_active_signals

"""

# drive_oscar modulu yoksa direkt inline tanimla
IMPORT_INLINE = """\
# ── Drive: sinyal kaydet ──────────────────────────────────────────────────
import json as _json
from pathlib import Path as _Path
from datetime import datetime as _dt

def _drive_dir():
    p = _Path("/content/drive/MyDrive/oscar_duman")
    p.mkdir(parents=True, exist_ok=True)
    return p

def add_signal(sig: dict) -> None:
    d = _drive_dir()
    f = d / "active_signals.json"
    data = _json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    data[sig["sinyal_id"]] = sig
    f.write_text(_json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def load_active_signals() -> dict:
    f = _drive_dir() / "active_signals.json"
    return _json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}

print("Drive fonksiyonlari hazir.")

"""

# Cell 3'un en basina ekle (banner'dan sonra)
if "add_signal" not in src:
    # Banner bittikten sonra ekle
    banner_end = src.find("\n\n")
    if banner_end > 0:
        src = src[:banner_end+2] + IMPORT_INLINE + src[banner_end+2:]
    else:
        src = IMPORT_INLINE + src
    print("OK: add_signal inline tanimi eklendi")
else:
    print("INFO: add_signal zaten mevcut")

nb["cells"][6]["source"] = src
with open("setup.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print("Kaydedildi.")
