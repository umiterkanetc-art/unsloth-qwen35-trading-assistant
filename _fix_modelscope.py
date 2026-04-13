"""Hucre 2'de model yuklemesini ModelScope'a gec — Colab'da daha hizli."""
import json

nb = json.load(open("setup.ipynb", encoding="utf-8"))

src = nb["cells"][4]["source"]
if isinstance(src, list):
    src = "".join(src)

# Model yukleme blogunu bul ve ModelScope ile degistir
OLD_LOAD = 'from unsloth import FastLanguageModel'

NEW_LOAD = '''\
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

from unsloth import FastLanguageModel'''

# MODEL_NAME satirini da guncelle — yerel path kullan
OLD_MODEL_NAME = 'MODEL_NAME     = "unsloth/Qwen3-32B"'
NEW_MODEL_NAME = 'MODEL_NAME     = _ms_path  # ModelScope yerel path'

if OLD_LOAD in src:
    src = src.replace(OLD_LOAD, NEW_LOAD)
    print("OK: ModelScope import eklendi")
else:
    print("UYARI: 'from unsloth import FastLanguageModel' bulunamadi")

if OLD_MODEL_NAME in src:
    src = src.replace(OLD_MODEL_NAME, NEW_MODEL_NAME)
    print("OK: MODEL_NAME guncellendi")
else:
    # Hucre 2'de MODEL_NAME tekrar tanimlanmis olabilir, kontrol et
    if 'MODEL_NAME' in src:
        print("INFO: MODEL_NAME mevcut ama farkli format — kontrol et")

nb["cells"][4]["source"] = src

with open("setup.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Kaydedildi.")
