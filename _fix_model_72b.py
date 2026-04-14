"""Qwen3-72B 4-bit — H100 80GB icin optimize."""
import json

nb = json.load(open("setup.ipynb", encoding="utf-8"))

for cell_idx in [2, 4]:
    src = nb["cells"][cell_idx]["source"]
    if isinstance(src, list):
        src = "".join(src)

    src = src.replace(
        'MODEL_NAME     = "unsloth/Qwen3-32B"',
        'MODEL_NAME     = "unsloth/Qwen3-72B"'
    )
    src = src.replace(
        'MODEL_NAME     = "unsloth/Qwen3-32B"',
        'MODEL_NAME     = "unsloth/Qwen3-72B"'
    )
    # MAX_SEQ_LENGTH de artir — 72B daha uzun context kaldırır
    src = src.replace(
        'MAX_SEQ_LENGTH = 16384',
        'MAX_SEQ_LENGTH = 32768'
    )

    nb["cells"][cell_idx]["source"] = src
    print(f"Cell {cell_idx} guncellendi")

with open("setup.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("OK: Qwen3-72B, 32k context, H100 icin hazir.")
