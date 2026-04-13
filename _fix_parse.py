import json

nb = json.load(open("setup.ipynb", encoding="utf-8"))
src = nb["cells"][24]["source"]
if isinstance(src, list):
    src = "".join(src)

# 1. KOSUL regex — trailing spaces duzelt
src = src.replace(
    'm = re.search(r"```KOSUL\\n(.+?)```", analysis, re.DOTALL | re.IGNORECASE)',
    'm = re.search(r"```KOSUL[ \\t]*\\n(.+?)```", analysis, re.DOTALL | re.IGNORECASE)'
)

# 2. _build_context_from_cache — likidasyon blogu ekle
OLD = '''    lines.append(f"OI      : {d.get('open_interest', 'N/A')}")
    lines.append(f"Veri ts : {d.get('ts', 'N/A')}")
    return "\\n".join(lines)'''

NEW = '''    lines.append(f"OI      : {d.get('open_interest', 'N/A')}")
    lines.append(f"Veri ts : {d.get('ts', 'N/A')}")
    liq = d.get("liquidation", {})
    if liq:
        lines.append("")
        lines.append("── LIKIDASYON ──────────────────────")
        cascade = liq.get("cascade_riski", "")
        if cascade in ("YUKSEK", "YÜKSEK"):
            lines.append("UYARI: CASCADE RISKI YUKSEK")
        long_z = liq.get("long_liq_zones", [])
        short_z = liq.get("short_liq_zones", [])
        if long_z:
            z = long_z[0]
            lines.append(f"Long liq havuzu : ${z['price']:,.1f}  (${z['hacim_usd']:,}  — %{z['uzaklik_pct']} uzakta)")
        if short_z:
            z = short_z[0]
            lines.append(f"Short liq havuzu: ${z['price']:,.1f}  (${z['hacim_usd']:,}  — %{z['uzaklik_pct']} uzakta)")
        oi_deg = liq.get("oi_degisim_pct", 0)
        lines.append(f"OI 1s degisim   : %{oi_deg:+.2f}  |  Stres: {liq.get('stres_skoru', 0)}/10")
        bar = liq.get("bid_ask_ratio", 1.0)
        lines.append(f"Alis/Satis      : {bar}")
    return "\\n".join(lines)'''

if OLD in src:
    src = src.replace(OLD, NEW)
    print("OK: likidasyon blogu eklendi")
else:
    print("UYARI: OI satiri bulunamadi, manuel kontrol et")

nb["cells"][24]["source"] = src
with open("setup.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print("Notebook kaydedildi")
