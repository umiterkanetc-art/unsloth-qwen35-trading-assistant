"""ModelScope yerine hf-mirror.com kullan — unsloth modelleri sadece HF'de var."""
import json

nb = json.load(open("setup.ipynb", encoding="utf-8"))

src = nb["cells"][4]["source"]
if isinstance(src, list):
    src = "".join(src)

OLD = """\
# ── Model: Drive cache (ilk seferinde indirir, sonra Drive'dan yukler) ───
import subprocess, os
subprocess.run(["pip", "install", "-q", "modelscope"], check=False)

# Drive cache klasoru — Drive mount edilmisse buraya indirir, bir daha indirmez
DRIVE_CACHE = "/content/drive/MyDrive/oscar_model_cache"
os.makedirs(DRIVE_CACHE, exist_ok=True)
os.environ["MODELSCOPE_CACHE"]    = DRIVE_CACHE
os.environ["HF_HOME"]             = DRIVE_CACHE
os.environ["UNSLOTH_USE_MODELSCOPE"] = "1"

# Cache kontrol
_cached = [d for d in os.listdir(DRIVE_CACHE) if "Qwen3" in d or "qwen3" in d.lower()] if os.path.exists(DRIVE_CACHE) else []
if _cached:
    print(f"Drive cache bulundu: {_cached[0]} — Drive'dan yukleniyor (~2-3 dk)")
else:
    print("Ilk yuklem — ModelScope'tan Drive'a indiriliyor (~15-20 dk, bir kez)")

from unsloth import FastLanguageModel"""

NEW = """\
# ── Model: Drive cache + HF mirror (ilk seferinde indirir, sonra Drive'dan yukler) ───
import subprocess, os
# hf-mirror.com = HuggingFace CDN mirror, unsloth modelleri icin gerekli
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# Drive cache — bir kez indirir, sonra hep Drive'dan yukler
DRIVE_CACHE = "/content/drive/MyDrive/oscar_model_cache"
os.makedirs(DRIVE_CACHE, exist_ok=True)
os.environ["HF_HOME"] = DRIVE_CACHE

# ModelScope'u devre disi birak (unsloth/ modelleri orada yok)
os.environ.pop("UNSLOTH_USE_MODELSCOPE", None)

import glob as _glob
_cached = _glob.glob(f"{DRIVE_CACHE}/**/*Qwen3*72B*", recursive=True)
if _cached:
    print(f"Drive cache bulundu — Drive'dan yukleniyor (~2-3 dk)")
else:
    print("Ilk yuklem — hf-mirror'dan Drive'a indiriliyor (~15-20 dk, bir kez)")

from unsloth import FastLanguageModel"""

if OLD in src:
    src = src.replace(OLD, NEW)
    print("OK: HF mirror blogu eklendi")
else:
    # Daha esnek arama
    if 'UNSLOTH_USE_MODELSCOPE' in src:
        import re
        # Tum ModelScope satirlarini bul ve degistir
        src = re.sub(
            r"subprocess\.run\(\[\"pip\", \"install\", \"-q\", \"modelscope\"\].*?\n",
            "", src
        )
        src = src.replace(
            'os.environ["UNSLOTH_USE_MODELSCOPE"] = "1"',
            'os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"\nos.environ.pop("UNSLOTH_USE_MODELSCOPE", None)'
        )
        src = src.replace(
            'os.environ["UNSLOTH_USE_MODELSCOPE"] = "1"   # Unsloth resmi destek',
            'os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"\nos.environ.pop("UNSLOTH_USE_MODELSCOPE", None)'
        )
        print("OK: ModelScope -> HF mirror degistirildi")
    else:
        print("UYARI: Degistirilecek blok bulunamadi")

nb["cells"][4]["source"] = src

with open("setup.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Kaydedildi.")
