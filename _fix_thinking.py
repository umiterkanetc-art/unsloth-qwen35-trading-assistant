"""oscar_signal cagrilarinda thinking=False yap — tarama hizlanir, hata duzulur.
Karar motoru (oscar_decide_trigger) thinking=True kalir."""
import json

nb = json.load(open("setup.ipynb", encoding="utf-8"))

fixed = 0

for i, c in enumerate(nb["cells"]):
    src = c["source"] if isinstance(c["source"], str) else "".join(c["source"])

    # oscar_signal fonksiyonunda chat cagrisini bul ve thinking=False ekle
    if "def oscar_signal(" in src and "analiz = chat(" in src:
        old = 'analiz = chat(soru, market_context=ctx, reset=True)'
        new = 'analiz = chat(soru, market_context=ctx, reset=True, thinking=False)'
        if old in src:
            src = src.replace(old, new)
            nb["cells"][i]["source"] = src
            print(f"Cell {i}: oscar_signal thinking=False yapildi")
            fixed += 1

    # temp_QA silme kodunu kaldir (yanlis duzeltme)
    if "temp_QA" in src and "delattr" in src:
        old_clear = '''    # Unsloth thinking state temizle (temp_QA hatası önleme)
    for _m in model.modules():
        for _attr in ["temp_QA", "temp_KV", "temp_O", "temp_seq"]:
            try:
                if hasattr(_m, _attr): delattr(_m, _attr)
            except Exception:
                pass

    '''
        if old_clear in src:
            src = src.replace(old_clear, "    ")
            nb["cells"][i]["source"] = src
            print(f"Cell {i}: yanlis temp_QA silme kodu kaldirildi")
            fixed += 1

print(f"\nToplam {fixed} degisiklik yapildi.")

with open("setup.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print("Kaydedildi.")
