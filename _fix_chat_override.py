"""chat() fonksiyonuna system_override parametresi ekle."""
import json

nb = json.load(open("setup.ipynb", encoding="utf-8"))
src = nb["cells"][4]["source"]
if isinstance(src, list):
    src = "".join(src)

# chat() imzasina system_override ekle
OLD_SIG = """\
def chat(
    user_message: str,
    market_context: str = "",
    reset: bool = False,
    thinking: bool = True,         # \u2190 varsay\u0131lan A\u00c7IK: model \u00f6nce d\u00fc\u015f\u00fcn\u00fcr, sonra yazar
    max_new_tokens: int = 2048,    # \u2190 d\u00fc\u015f\u00fcnce zinciri i\u00e7in art\u0131r\u0131ld\u0131
    temperature: float = 0.6,
    top_p: float = 0.95,
):"""

NEW_SIG = """\
def chat(
    user_message: str,
    market_context: str = "",
    reset: bool = False,
    thinking: bool = True,
    max_new_tokens: int = 2048,
    temperature: float = 0.6,
    top_p: float = 0.95,
    system_override: str | None = None,
):"""

OLD_BUILD = """\
    messages = build_trading_messages(
        user_message=user_message,
        market_context=market_context,
        history=_conversation_history,
    )"""

NEW_BUILD = """\
    messages = build_trading_messages(
        user_message=user_message,
        market_context=market_context,
        history=_conversation_history,
        system_override=system_override,
    )"""

changed = 0
if OLD_SIG in src:
    src = src.replace(OLD_SIG, NEW_SIG)
    print("OK: chat() imzasi guncellendi")
    changed += 1
else:
    print("UYARI: chat() imzasi bulunamadi — unicode farki olabilir, encoding kontrol ediliyor")
    # Encoding-safe yontem
    lines = src.split("\n")
    for i, line in enumerate(lines):
        if "def chat(" in line:
            print(f"  chat() satir {i+1}: {line!r}")
        if "top_p: float" in line:
            # Bir sonraki satira system_override ekle
            lines.insert(i+1, "    system_override: str | None = None,")
            print(f"  system_override {i+2}. satira eklendi")
            changed += 1
            break
    src = "\n".join(lines)

if OLD_BUILD in src:
    src = src.replace(OLD_BUILD, NEW_BUILD)
    print("OK: build_trading_messages system_override ile guncellendi")
    changed += 1
else:
    # Satir bazli bul
    lines = src.split("\n")
    for i, line in enumerate(lines):
        if "history=_conversation_history," in line:
            # Sonrasina system_override ekle
            lines.insert(i+1, "        system_override=system_override,")
            print(f"  system_override {i+2}. satira eklendi (build_trading_messages)")
            changed += 1
            break
    src = "\n".join(lines)

nb["cells"][4]["source"] = src

with open("setup.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"\n{changed} degisiklik yapildi, kaydedildi.")
