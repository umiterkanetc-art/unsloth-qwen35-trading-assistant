"""Notebook'u 3 temiz hucreye yeniden yaz."""
import json

nb = json.load(open("setup.ipynb", encoding="utf-8"))

def get(i):
    src = nb["cells"][i]["source"]
    return src if isinstance(src, str) else "".join(src)

# Mevcut hucrelerden icerik al
CONFIG      = get(5)
CLONE       = get(7)
UNSLOTH     = get(9)
HF_LOGIN    = get(11)
MODEL_LOAD  = get(13)
CHAT_FN     = get(15)
DRIVE       = get(25)
SIGNAL      = get(27)
REFLECT     = get(29)
KARAR       = get(31)
TARAMA      = get(33)

def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text}

def code(text):
    return {"cell_type": "code", "execution_count": None,
            "metadata": {}, "outputs": [], "source": text.strip()}

# ─────────────────────────────────────────────────────────────────────────
# HUCRE 1: KURULUM (sadece ilk seferde)
# ─────────────────────────────────────────────────────────────────────────

CELL1 = f"""
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

# ── Config (REPO_DIR ve diger sabitler) ──────────────────
{CONFIG}

# ── Repo clone / update ───────────────────────────────────
{CLONE}

# ── HF login ─────────────────────────────────────────────
{HF_LOGIN}

print()
print("OK Kurulum tamamlandi. Artik Hucre 2'yi calistirabilirsin.")
"""

# ─────────────────────────────────────────────────────────────────────────
# HUCRE 2: BASLAT (her session'da)
# ─────────────────────────────────────────────────────────────────────────

CELL2 = f"""
# ╔══════════════════════════════════════════════════════════╗
# ║  HUCRE 2 — BASLAT  (her session'da calistir)            ║
# ╚══════════════════════════════════════════════════════════╝

import os, sys, re, json, time as _time, threading as _threading
import requests as _requests
from pathlib import Path
from datetime import datetime, timezone

# ── Config ────────────────────────────────────────────────
{CONFIG}

# ── Repo guncelle ─────────────────────────────────────────
{CLONE}

# ── Model yukle ───────────────────────────────────────────
from unsloth import FastLanguageModel
{MODEL_LOAD}

# ── Chat fonksiyonu ───────────────────────────────────────
{CHAT_FN}

# ── Drive baglantisi ──────────────────────────────────────
{DRIVE}

# ── Sinyal uretici ────────────────────────────────────────
{SIGNAL}

# ── Yansima motoru ────────────────────────────────────────
{REFLECT}

print()
print("=" * 55)
print("  Oscar hazir. Hucre 3'u calistir.")
print("=" * 55)
"""

# ─────────────────────────────────────────────────────────────────────────
# HUCRE 3: CALISTIR
# ─────────────────────────────────────────────────────────────────────────

CELL3 = f"""
# ╔══════════════════════════════════════════════════════════╗
# ║  HUCRE 3 — CALISTIR  (Hucre 2'den sonra)                ║
# ║  Durdurmak icin: Interrupt (kare buton)                 ║
# ╚══════════════════════════════════════════════════════════╝

# ── Karar motoru + Tarama dongusu ────────────────────────
{KARAR}

{TARAMA}

# Baslat
run_auto_loop()
"""

# ─────────────────────────────────────────────────────────────────────────
# Yeni notebook olustur
# ─────────────────────────────────────────────────────────────────────────

new_cells = [
    md("# Oscar — Kripto Analiz Sistemi\n\n**3 hucre:** Kurulum → Baslat → Calistir"),
    md("## Hucre 1 — Kurulum\nSadece **ilk seferde** calistir. Unsloth kurar, repo'yu ceker."),
    code(CELL1),
    md("## Hucre 2 — Baslat\n**Her session'da** calistir. Modeli yukler, fonksiyonlari hazirlar. ~10-15 dk."),
    code(CELL2),
    md("## Hucre 3 — Calistir\nHucre 2 bittikten sonra calistir. Oscar taramaya baslar."),
    code(CELL3),
]

new_nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": nb["metadata"],
    "cells": new_cells,
}

with open("setup.ipynb", "w", encoding="utf-8") as f:
    json.dump(new_nb, f, ensure_ascii=False, indent=1)

print(f"OK: Notebook 3 hucreye indirildi.")
print("  Hucre 1: Kurulum (ilk seferde)")
print("  Hucre 2: Baslat (her session'da)")
print("  Hucre 3: Calistir")
