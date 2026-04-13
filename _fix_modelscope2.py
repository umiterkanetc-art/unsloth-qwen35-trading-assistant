"""Unsloth'un resmi ModelScope destegini kullan — tek env var yeterli."""
import json

nb = json.load(open("setup.ipynb", encoding="utf-8"))

src = nb["cells"][4]["source"]
if isinstance(src, list):
    src = "".join(src)

# Onceki karmasik ModelScope blogunu kaldir, Unsloth'un kendi destegini kullan
OLD = """\
# ── ModelScope uzerinden indir (HuggingFace'den daha hizli) ──────────────
import subprocess
subprocess.run(["pip", "install", "-q", "modelscope"], check=False)

import os
os.environ["MODELSCOPE_CACHE"] = "/content/modelscope_cache"

from modelscope import snapshot_download
print("ModelScope'tan Qwen3-32B indiriliyor...")
_ms_path = snapshot_download(
    "Qwen/Qwen3-32B",
    cache_dir="/content/modelscope_cache",
)
print(f"Model indirildi: {_ms_path}")

from unsloth import FastLanguageModel"""

NEW = """\
# ── ModelScope (HuggingFace down oldugunda / daha hizli) ─────────────────
import subprocess, os
subprocess.run(["pip", "install", "-q", "modelscope"], check=False)
os.environ["UNSLOTH_USE_MODELSCOPE"] = "1"   # Unsloth resmi destek

from unsloth import FastLanguageModel"""

# MODEL_NAME duzelt
OLD_NAME = "MODEL_NAME     = _ms_path  # ModelScope yerel path"
NEW_NAME = 'MODEL_NAME     = "unsloth/Qwen3-32B"'

if OLD in src:
    src = src.replace(OLD, NEW)
    print("OK: ModelScope blogu guncellendi")
else:
    print("UYARI: eski blok bulunamadi — elle ekleniyor")
    src = src.replace(
        "from unsloth import FastLanguageModel",
        NEW
    )

if OLD_NAME in src:
    src = src.replace(OLD_NAME, NEW_NAME)
    print("OK: MODEL_NAME duzeltildi")

nb["cells"][4]["source"] = src

with open("setup.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Kaydedildi.")
