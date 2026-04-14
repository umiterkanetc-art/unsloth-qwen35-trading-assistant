"""
Model yuklemesini Drive cache'e yonlendir.
- Ilk calistirmada Drive'a indirir (~20 dk, bir kez)
- Sonraki her session'da Drive'dan yukler (~2-3 dk)
- Ayrica duplicate ModelScope blogunu temizler
"""
import json, re

nb = json.load(open("setup.ipynb", encoding="utf-8"))
src = nb["cells"][4]["source"]
if isinstance(src, list):
    src = "".join(src)

# Eski model yukleme blogunu bul ve temizle (duplicate dahil)
# "# ── ModelScope" ile baslayan her seyi ve from_pretrained'i degistir
old_block = """\
# ── ModelScope (HuggingFace down oldugunda / daha hizli) ─────────────────
import subprocess, os
subprocess.run(["pip", "install", "-q", "modelscope"], check=False)
os.environ["UNSLOTH_USE_MODELSCOPE"] = "1"   # Unsloth resmi destek

from unsloth import FastLanguageModel
# ── ModelScope (HuggingFace down oldugunda / daha hizli) ─────────────────
import subprocess, os
subprocess.run(["pip", "install", "-q", "modelscope"], check=False)
os.environ["UNSLOTH_USE_MODELSCOPE"] = "1"   # Unsloth resmi destek

from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name      = MODEL_NAME,"""

new_block = """\
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

from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name      = MODEL_NAME,"""

if old_block in src:
    src = src.replace(old_block, new_block)
    print("OK: Drive cache blogu eklendi, duplicate temizlendi")
else:
    print("UYARI: Tam blok eslesmedi, satir satir arama yapiliyor...")
    # Daha esnek: sadece duplicate kismi temizle, cache ekle
    # Iki kez gelen ModelScope blogunu tek yap
    double = """\
# ── ModelScope (HuggingFace down oldugunda / daha hizli) ─────────────────
import subprocess, os
subprocess.run(["pip", "install", "-q", "modelscope"], check=False)
os.environ["UNSLOTH_USE_MODELSCOPE"] = "1"   # Unsloth resmi destek

from unsloth import FastLanguageModel
# ── ModelScope (HuggingFace down oldugunda / daha hizli) ─────────────────
import subprocess, os
subprocess.run(["pip", "install", "-q", "modelscope"], check=False)
os.environ["UNSLOTH_USE_MODELSCOPE"] = "1"   # Unsloth resmi destek

from unsloth import FastLanguageModel"""

    single = """\
# ── Model: Drive cache (ilk seferinde indirir, sonra Drive'dan yukler) ───
import subprocess, os
subprocess.run(["pip", "install", "-q", "modelscope"], check=False)

DRIVE_CACHE = "/content/drive/MyDrive/oscar_model_cache"
os.makedirs(DRIVE_CACHE, exist_ok=True)
os.environ["MODELSCOPE_CACHE"]       = DRIVE_CACHE
os.environ["HF_HOME"]                = DRIVE_CACHE
os.environ["UNSLOTH_USE_MODELSCOPE"] = "1"

_cached = [d for d in os.listdir(DRIVE_CACHE) if "Qwen3" in d or "qwen3" in d.lower()] if os.path.exists(DRIVE_CACHE) else []
if _cached:
    print(f"Drive cache bulundu: {_cached[0]} — Drive'dan yukleniyor (~2-3 dk)")
else:
    print("Ilk yuklem — ModelScope'tan Drive'a indiriliyor (~15-20 dk, bir kez)")

from unsloth import FastLanguageModel"""

    if double in src:
        src = src.replace(double, single)
        print("OK: Duplicate temizlendi + Drive cache eklendi")
    else:
        print("HATA: Blok bulunamadi — manuel inceleme gerekli")

nb["cells"][4]["source"] = src

with open("setup.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Kaydedildi.")
