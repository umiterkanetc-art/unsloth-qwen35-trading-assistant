# unsloth-qwen35-trading-assistant

Production-ready, inference-first repository for running `unsloth/Qwen3.5-27B` inside VS Code with the official Google Colab extension on a Google Colab Pro A100 80GB runtime.

This project is designed around three non-negotiables:

- Git only. No Google Drive mounts, no Drive sync, no notebook copies living outside version control.
- Hugging Face Hub for model weights today, and for LoRA adapters later when you decide to fine-tune.
- One clean notebook-first workflow for high-end inference with `bf16`, `max_seq_length=16384`, and Unsloth fast inference enabled.

## Why this setup

`unsloth/Qwen3.5-27B` is the strongest practical choice for a single Colab Pro A100 80GB inference workflow when you want a large, capable model without dropping to 4-bit quantization. This repository is intentionally inference-first and keeps the runtime logic focused on:

- A100-compatible Unsloth installation
- BF16 model loading
- Long context configuration
- Fast inference with `FastLanguageModel.for_inference`
- A strong crypto trading system prompt tuned for technical analysis, trade planning, and risk management

## Repository layout

```text
unsloth-qwen35-trading-assistant/
├── README.md
├── .gitignore
├── requirements.txt
├── setup.ipynb
├── src/
│   ├── __init__.py
│   └── trading_prompt.py
├── notebooks/
│   └── quick_test.ipynb
├── .vscode/
│   └── settings.json
└── LICENSE
```

## Prerequisites

- A GitHub account and a repository that will host this project
- A Hugging Face account
- A Hugging Face token if you want authenticated downloads or later want to push adapters
- Google Colab Pro with access to an A100 80GB runtime
- VS Code
- VS Code extensions:
  - Python
  - Jupyter
  - `Colab` by Google (`Google.colab`)

The official Colab VS Code extension quick-start flow is:

1. Install the extension.
2. Open a notebook.
3. Sign in when prompted.
4. Click `Select Kernel`.
5. Choose `Colab`.
6. Choose `New Colab Server`.

## First run

### 1. Create the GitHub repository

Create an empty GitHub repository named `unsloth-qwen35-trading-assistant`, then push this folder to it:

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-github-username>/unsloth-qwen35-trading-assistant.git
git push -u origin main
```

### 2. Clone locally with Git

```bash
git clone https://github.com/<your-github-username>/unsloth-qwen35-trading-assistant.git
cd unsloth-qwen35-trading-assistant
```

Open the folder in VS Code.

### 3. Optional local Python environment for editing and notebook quality-of-life

This repository runs the actual model in Colab, not on your local workstation. A light local environment is still useful for imports, linting, and notebook editing:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux or macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Open the main notebook in VS Code

Open [setup.ipynb](/c:/Users/bilal/Downloads/mlll/unsloth-qwen35-trading-assistant/setup.ipynb).

Then connect it to Colab:

1. Click `Select Kernel`.
2. Choose `Colab`.
3. Choose `New Colab Server`.
4. Sign in if prompted.
5. Use a Colab Pro runtime with A100 80GB.

Important: this project is intentionally Git-only. Do not mount Google Drive. The Colab extension includes a Drive command, but this repo does not need it.

### 5. Set your repository URL once

In the first configuration cell of [setup.ipynb](/c:/Users/bilal/Downloads/mlll/unsloth-qwen35-trading-assistant/setup.ipynb), set:

```python
REPO_URL = "https://github.com/<your-github-username>/unsloth-qwen35-trading-assistant.git"
```

You can also avoid editing the notebook by setting an environment variable in the runtime:

```python
import os
os.environ["PROJECT_REPO_URL"] = "https://github.com/<your-github-username>/unsloth-qwen35-trading-assistant.git"
os.environ["HF_TOKEN"] = "hf_..."
```

### 6. Run the notebook from top to bottom

The main notebook will:

- clone or fast-forward the Git repo inside `/content/unsloth-qwen35-trading-assistant`
- install Unsloth using the official runtime-aware installer approach
- log in to Hugging Face if `HF_TOKEN` is present
- load `unsloth/Qwen3.5-27B`
- configure `max_seq_length=16384`
- force `bf16`
- keep `load_in_4bit=False`
- enable `FastLanguageModel.for_inference(model)`
- expose a reusable `chat(...)` function for trading analysis

## VS Code + Colab workflow

This is the intended operating model:

1. Edit prompts, notebook cells, and helper code locally in VS Code.
2. Commit and push to GitHub with Git.
3. Open `setup.ipynb` in VS Code using the official Colab extension.
4. Run the `git_pull_latest()` cell inside Colab whenever you want the runtime to pick up the latest Git changes.

That means:

- local editing stays clean and versioned
- Colab is only your execution environment
- model weights stay in Hugging Face cache
- adapters can later live on Hugging Face Hub

## Changing the model later

If you want to switch to another supported Unsloth model later:

1. Update `DEFAULT_MODEL_NAME` in [src/trading_prompt.py](/c:/Users/bilal/Downloads/mlll/unsloth-qwen35-trading-assistant/src/trading_prompt.py).
2. Change `MODEL_NAME` in [setup.ipynb](/c:/Users/bilal/Downloads/mlll/unsloth-qwen35-trading-assistant/setup.ipynb), or override it in the configuration cell.
3. Re-check three things:
   - VRAM fit on A100 80GB
   - supported context length
   - whether you still want `bf16` without quantization

Good knobs to revisit when changing models:

- `MODEL_NAME`
- `MAX_SEQ_LENGTH`
- `DTYPE`
- `LOAD_IN_4BIT`
- generation settings inside `chat(...)`

If a future model is too large for full BF16 inference at 16k context, reduce `MAX_SEQ_LENGTH` first before moving to quantization.

## Pushing LoRA adapters to Hugging Face Hub later

This repository is inference-first, so it does not fine-tune by default. When you decide to add LoRA training later, Unsloth supports pushing adapters directly to the Hugging Face Hub.

Adapter-only push:

```python
model.push_to_hub_merged(
    "your-hf-username/qwen35-trading-assistant-lora",
    tokenizer,
    save_method="lora",
    token=os.environ["HF_TOKEN"],
)
```

Local save first, then push later:

```python
model.save_pretrained_merged(
    "qwen35-trading-assistant-lora",
    tokenizer,
    save_method="lora",
)
```

Recommended Hugging Face flow:

1. Create a fine-grained token at `https://huggingface.co/settings/tokens`
2. Export it as `HF_TOKEN`
3. Use a clear adapter repo name such as `your-hf-username/qwen35-trading-assistant-lora`
4. Keep adapters on HF Hub, not in Git

## Git rules for this repo

- Commit code, notebooks, prompts, configs, and documentation
- Do not commit model weights
- Do not commit Hugging Face cache
- Do not commit LoRA checkpoints or merged model artifacts
- Do not use Google Drive as a persistence layer

## Notes on runtime reliability

- A clean A100 80GB runtime matters. Restart the Colab runtime if memory is fragmented.
- The first model download is large because the BF16 checkpoint is large.
- Pulling the latest Git changes inside the notebook is fast; re-downloading the model is the expensive part.

## Files you will edit most often

- [setup.ipynb](/c:/Users/bilal/Downloads/mlll/unsloth-qwen35-trading-assistant/setup.ipynb): main runtime notebook
- [src/trading_prompt.py](/c:/Users/bilal/Downloads/mlll/unsloth-qwen35-trading-assistant/src/trading_prompt.py): system prompt and message builder
- [notebooks/quick_test.ipynb](/c:/Users/bilal/Downloads/mlll/unsloth-qwen35-trading-assistant/notebooks/quick_test.ipynb): lightweight prompt smoke test

## License

This repository is licensed under Apache 2.0. See [LICENSE](/c:/Users/bilal/Downloads/mlll/unsloth-qwen35-trading-assistant/LICENSE).
