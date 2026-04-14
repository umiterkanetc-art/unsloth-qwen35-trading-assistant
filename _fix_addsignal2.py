"""Cell 3 basina add_signal ve load_active_signals inline tanimla."""
import json

nb = json.load(open("setup.ipynb", encoding="utf-8"))
src = nb["cells"][6]["source"]
if isinstance(src, list):
    src = "".join(src)

DEFINITIONS = """\
# ── Drive: sinyal kaydet / oku ────────────────────────────────────────────
import json as _json, uuid
from pathlib import Path as _Path

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

# def add_signal veya def load_active_signals yoksa ekle
if "def add_signal" not in src:
    # Banner'dan sonraki ilk bos satiri bul
    idx = src.find("\n\n")
    if idx > 0:
        src = src[:idx+2] + DEFINITIONS + src[idx+2:]
    else:
        src = DEFINITIONS + src
    print("OK: add_signal + load_active_signals eklendi")
else:
    print("INFO: zaten tanimi var")

nb["cells"][6]["source"] = src
with open("setup.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print("Kaydedildi.")
