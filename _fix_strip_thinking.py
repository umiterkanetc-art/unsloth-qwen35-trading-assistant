"""_strip_thinking duzelt + Meta-Oscar max_new_tokens artir."""
import json, re

nb = json.load(open("setup.ipynb", encoding="utf-8"))
src = nb["cells"][4]["source"]
if isinstance(src, list):
    src = "".join(src)

# 1. _strip_thinking duzelt: </think> yoksa son <think>'ten sonrasini al
OLD_STRIP = '''def _strip_thinking(text: str) -> str:
    """
    Qwen3 <think>...</think> bloğunu temizle, sadece asıl cevabı döndür.
    Thinking içeriği tamamen kaldırılır — kullanıcıya sade, temiz çıktı gider.
    """
    # <think>...</think> bloğunu (multiline) kaldır
    cleaned = re.sub(r"<think>[\\s\\S]*?</think>", "", text, flags=re.DOTALL)
    return cleaned.strip()'''

NEW_STRIP = '''def _strip_thinking(text: str) -> str:
    """
    Qwen3 <think>...</think> bloğunu temizle, sadece asıl cevabı döndür.
    Eger </think> kapanisi yoksa (token limiti nedeniyle truncate oldu),
    son <think> etiketinden onceki kismi, veya KOSUL blogunu bul.
    """
    # Normal durum: <think>...</think> var
    if "</think>" in text:
        cleaned = re.sub(r"<think>[\\s\\S]*?</think>", "", text, flags=re.DOTALL)
        return cleaned.strip()

    # Truncate durumu: </think> yok
    # Onceden KOSUL blogu var mi? (thinking icinde yazilmis olabilir)
    kosul_idx = text.rfind("```KOSUL")
    if kosul_idx < 0:
        kosul_idx = text.rfind("```kosul")
    if kosul_idx >= 0:
        # KOSUL'dan itibaren al
        return text[kosul_idx:].strip()

    # TIP: satiri var mi?
    tip_idx = text.rfind("TIP:")
    if tip_idx >= 0:
        return text[tip_idx:].strip()

    # Hicbiri yoksa: <think> oncesini al (eger varsa)
    think_idx = text.find("<think>")
    if think_idx > 50:
        return text[:think_idx].strip()

    # Son care: tum metni dondur
    return text.strip()'''

if OLD_STRIP in src:
    src = src.replace(OLD_STRIP, NEW_STRIP)
    print("OK: _strip_thinking duzeltildi")
else:
    print("WARN: _strip_thinking bulunamadi")
    # Gercek formati goster
    idx = src.find("def _strip_thinking")
    print(repr(src[idx:idx+300]))

# 2. Meta-Oscar max_new_tokens: 2048 -> 4096 (thinking icin yer)
OLD_META = '''# 5. Meta-Oscar sentez (thinking=True, tam analiz — 1500 token)
    print(f"  [{symbol}] Meta-Oscar...")'''

NEW_META = '''# 5. Meta-Oscar sentez (thinking=True, tam analiz — 4096 token)
    # Qwen3 thinking modu 1000-2000 token thinking harcıyor; KOSUL blogu icin yer lazım
    print(f"  [{symbol}] Meta-Oscar...")'''

if OLD_META in src:
    src = src.replace(OLD_META, NEW_META)
    print("OK: Meta-Oscar yorumu guncellendi")

# Meta-Oscar chat() cagrisi - max_new_tokens guncelle
OLD_CHAT = '''    final = chat(
        f"{symbol} icin 3 ajan raporunu sentezle ve nihai karar ver.",
        market_context=sentez, reset=True,
        thinking=True, system_override=META_AGENT_PROMPT
    )'''

NEW_CHAT = '''    final = chat(
        f"{symbol} icin 3 ajan raporunu sentezle ve nihai karar ver.",
        market_context=sentez, reset=True,
        thinking=True, max_new_tokens=4096,
        system_override=META_AGENT_PROMPT
    )'''

if OLD_CHAT in src:
    src = src.replace(OLD_CHAT, NEW_CHAT)
    print("OK: Meta-Oscar max_new_tokens=4096 ayarlandi")
else:
    print("WARN: Meta-Oscar chat() cagrisi bulunamadi")
    idx = src.find("3 ajan raporunu sentezle")
    print(repr(src[max(0,idx-50):idx+200]))

nb["cells"][4]["source"] = src
with open("setup.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print("Kaydedildi.")
