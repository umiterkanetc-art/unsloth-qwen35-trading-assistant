"""Notebook'un en ustune tek hucrelik hizli baslangic ekle."""
import json

nb = json.load(open("setup.ipynb", encoding="utf-8"))

# Tum kod hucrelerinin icerigini topla (markdown atlaniyor)
cell_indices = [2, 4, 6, 8, 10, 12, 22, 24, 26, 28, 30]
parts = []
for i in cell_indices:
    src = nb["cells"][i]["source"]
    if isinstance(src, list):
        src = "".join(src)
    # Markdown hucreleri atla
    if nb["cells"][i]["cell_type"] != "code":
        continue
    parts.append(f"# {'─'*60}\n# ADIM {i}\n# {'─'*60}\n{src}\n")

quickstart_code = "\n".join(parts)

# Baslangica banner ekle
header = '''"""
╔══════════════════════════════════════════════════════════╗
║         OSCAR HIZLI BAŞLANGIÇ — TEK HÜCRE               ║
║  Bu hücreyi çalıştır, her şey otomatik yüklenir.         ║
║  Model yüklemesi ~10-15 dakika sürer.                    ║
╚══════════════════════════════════════════════════════════╝
"""
print("Oscar hizli baslangic basliyor...")
print("Adimlar: Repo → Unsloth → Model → Drive → Sinyaller → Karar → Tarama")
print()

'''

quickstart_code = header + quickstart_code

# Sona durum mesaji ekle
quickstart_code += '''
print()
print("=" * 55)
print("  OSCAR TAMAMEN HAZIR")
print("  Otomatik tarama aktif — Telegram bildirimleri acik")
print("=" * 55)
'''

quickstart_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": quickstart_code
}

quickstart_md = {
    "cell_type": "markdown",
    "metadata": {},
    "source": "# OSCAR — Hizli Baslangic\n\n**Sadece bu hucreyi calistir.** Tum kurulum, model yukleme ve otomatik tarama otomatik baslar.\n\n> Model yukleme ~10-15 dakika surer."
}

# En basa ekle (config hucresinden once, index 0'a)
nb["cells"].insert(0, quickstart_cell)
nb["cells"].insert(0, quickstart_md)

with open("setup.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"OK: Hizli baslangic hucresi eklendi. Toplam {len(nb['cells'])} hucre.")
print("Notebook'un en ustunde 'OSCAR Hizli Baslangic' basligini goreceksin.")
