"""KOSUL parse'i toleranli yap + debug ekle."""
import json, re

nb = json.load(open("setup.ipynb", encoding="utf-8"))
src = nb["cells"][4]["source"]
if isinstance(src, list):
    src = "".join(src)

OLD = '''    # KOSUL blogunu parse et
    m = re.search(r"```KOSUL[ \\t]*\\n(.+?)```", final, re.DOTALL)
    if not m:
        print(f"  [{symbol}] KOSUL blogu bulunamadi")
        return None'''

NEW = '''    # KOSUL blogunu parse et — toleranli regex (kucuk/buyuk harf, bosluk)
    m = re.search(r"```[Kk][Oo][Ss][Uu][Ll][ \\t]*\\n(.+?)```", final, re.DOTALL)
    if not m:
        # Blok yoksa TIP: satirini direkt ara
        m_tip = re.search(r"TIP\\s*:", final)
        if m_tip:
            # TIP satirindan itibaren parse et
            kosul_text = final[m_tip.start():]
            print(f"  [{symbol}] KOSUL blok yok ama TIP bulundu, ham parse...")
            class _FakeMatch:
                def group(self, n): return kosul_text
            m = _FakeMatch()
        else:
            preview = final[-500:] if len(final) > 500 else final
            print(f"  [{symbol}] KOSUL bulunamadi. Meta-Oscar son 500 kar:")
            print(preview)
            print("---")
            return None'''

if OLD in src:
    src = src.replace(OLD, NEW)
    nb["cells"][4]["source"] = src
    with open("setup.ipynb", "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    print("OK: KOSUL parse toleranli + debug eklendi")
else:
    print("WARN: OLD pattern bulunamadi")
    # Gercek formati bul
    idx = src.find("KOSUL blogunu parse et")
    if idx >= 0:
        print("Bulunan blok:")
        print(repr(src[idx:idx+300]))
    else:
        print("'KOSUL blogunu parse et' de yok!")
        # En yakin sey
        idx2 = src.find("KOSUL")
        print(f"KOSUL ilk gorunumu idx={idx2}")
        print(repr(src[idx2:idx2+200]))
