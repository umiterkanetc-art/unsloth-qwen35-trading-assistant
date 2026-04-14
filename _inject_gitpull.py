"""Hucre 2'nin basina git pull ekle — her session'da otomatik guncelle."""
import json

nb = json.load(open("setup.ipynb", encoding="utf-8"))

src = nb["cells"][4]["source"]
if isinstance(src, list):
    src = "".join(src)

GIT_PULL = """\
# ── Repo guncelle (her session basinda) ──────────────────────────────────
import subprocess
_pull = subprocess.run(
    ["git", "-C", "/content/unsloth-qwen35-trading-assistant", "pull", "--ff-only"],
    capture_output=True, text=True
)
print("Repo:", (_pull.stdout + _pull.stderr).strip())

"""

# Daha once eklenmemisse ekle
if "git pull" not in src:
    # Banner satirinin hemen altina ekle (ilk bos satirdan sonra)
    banner_end = src.find("\n\n")
    if banner_end > 0:
        src = src[:banner_end+2] + GIT_PULL + src[banner_end+2:]
    else:
        src = GIT_PULL + src
    print("OK: git pull basina eklendi")
else:
    print("INFO: git pull zaten mevcut")

nb["cells"][4]["source"] = src

with open("setup.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Kaydedildi.")
