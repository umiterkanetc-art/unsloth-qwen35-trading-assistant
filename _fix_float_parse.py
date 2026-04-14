"""oscar_signal_v2'de float parse hatasini duzelt — '74,502.3' gibi sayilari isle."""
import json, re

nb = json.load(open("setup.ipynb", encoding="utf-8"))
src = nb["cells"][4]["source"]
if isinstance(src, list):
    src = "".join(src)

OLD = """\
    try:
        return {
            "symbol":      symbol,
            "yon":         kosul.get("YON", ""),
            "kosul_tipi":  kosul.get("TIP", "DIRECT"),
            "kosul_fiyat": float(kosul.get("TETIK", "0") or "0"),
            "entry":       float(kosul.get("ENTRY", "0") or "0"),
            "stop":        float(kosul.get("STOP", "0") or "0"),
            "hedef_1":     float(kosul.get("HEDEF_1", "0") or "0"),
            "hedef_2":     float(kosul.get("HEDEF_2", "0") or "0"),
            "analiz":      final,
            "prefilter_score": score,
        }
    except ValueError as e:
        print(f"  [{symbol}] Parse hatasi: {e}")
        return None"""

NEW = """\
    def _f(val: str) -> float:
        \"\"\"Virgul ve bosluklu sayilari float'a cevirir: '74,502.3' -> 74502.3\"\"\"
        try:
            return float(str(val).replace(",", "").replace(" ", "").strip() or "0")
        except ValueError:
            return 0.0

    try:
        return {
            "symbol":      symbol,
            "yon":         kosul.get("YON", ""),
            "kosul_tipi":  kosul.get("TIP", "DIRECT"),
            "kosul_fiyat": _f(kosul.get("TETIK", "0")),
            "entry":       _f(kosul.get("ENTRY", "0")),
            "stop":        _f(kosul.get("STOP", "0")),
            "hedef_1":     _f(kosul.get("HEDEF_1", "0")),
            "hedef_2":     _f(kosul.get("HEDEF_2", "0")),
            "analiz":      final,
            "prefilter_score": score,
        }
    except Exception as e:
        print(f"  [{symbol}] Parse hatasi: {e}")
        return None"""

if OLD in src:
    src = src.replace(OLD, NEW)
    print("OK: float parse duzeltildi")
else:
    print("UYARI: blok bulunamadi")

nb["cells"][4]["source"] = src
with open("setup.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print("Kaydedildi.")
