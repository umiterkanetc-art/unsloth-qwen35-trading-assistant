"""Kurulum hucresinde REPO_DIR'i CLONE'dan once tanimla."""
import json

nb = json.load(open("setup.ipynb", encoding="utf-8"))
src = nb["cells"][2]["source"]
if isinstance(src, list):
    src = "".join(src)

# Kurulum hucresi icin temiz yeniden yaz
CELL1 = '''\
# ╔══════════════════════════════════════════════════════════╗
# ║  HUCRE 1 — KURULUM  (sadece ilk seferde calistir)       ║
# ╚══════════════════════════════════════════════════════════╝

# ── Unsloth guncelle ──────────────────────────────────────
import subprocess, sys
print("Unsloth guncelleniyor...")
subprocess.run([
    sys.executable, "-m", "pip", "install", "-q", "-U",
    "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git",
    "unsloth_zoo"
], check=False)
print("OK Unsloth guncellendi.")

# ── Config (REPO_DIR once tanimla) ───────────────────────
import os, pathlib

REPO_URL = os.environ.get(
    "PROJECT_REPO_URL",
    "https://github.com/umiterkanetc-art/unsloth-qwen35-trading-assistant.git",
)
HF_TOKEN       = os.environ.get("HF_TOKEN", "")
REPO_DIR       = "/content/unsloth-qwen35-trading-assistant"
MODEL_NAME     = "unsloth/Qwen3-32B"
MAX_SEQ_LENGTH = 16384
DTYPE          = None
LOAD_IN_4BIT   = True

print(f"Model   : {MODEL_NAME}")
print(f"Repo    : {REPO_URL}")
print(f"HF token: {'set' if HF_TOKEN else 'not set'}")

# ── Repo clone / update ───────────────────────────────────
def _run(cmd, **kwargs):
    result = subprocess.run(cmd, capture_output=True, text=True, **kwargs)
    output = (result.stdout + result.stderr).strip()
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\\n{output}")
    return output

def git_pull_latest():
    """Clone the repo on first run; fast-forward pull on subsequent runs."""
    repo = pathlib.Path(REPO_DIR)
    if repo.exists():
        print(_run(["git", "-C", str(repo), "pull", "--ff-only"]))
    else:
        print(_run(["git", "clone", REPO_URL, str(repo)]))
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    print(f"Repo ready at {repo}")

git_pull_latest()

# ── HF login ─────────────────────────────────────────────
if HF_TOKEN:
    from huggingface_hub import login
    login(token=HF_TOKEN, add_to_git_credential=False)
    print("Logged in to Hugging Face Hub.")
else:
    print("No HF_TOKEN set — public model download will still work.")

print()
print("OK Kurulum tamamlandi. Artik Hucre 2'yi calistirabilirsin.")
'''

nb["cells"][2]["source"] = CELL1

with open("setup.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("OK: Hucre 1 duzeltildi ve kaydedildi.")
