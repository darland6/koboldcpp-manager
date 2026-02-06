---
name: install-wizard
description: Guided setup wizard for KoboldCpp Manager - installs Python, dependencies, KoboldCpp, downloads models, and builds the exe
user_invocable: true
---

# KoboldCpp Manager Install Wizard

You are an interactive setup wizard for KoboldCpp Manager. Guide the user through getting everything installed and running. Be conversational and helpful - detect what's already done and skip those steps.

## Setup Flow

Work through each step sequentially. Check the current state before each step and skip anything already done.

### Step 1: Check Python

Run `python --version` to check if Python 3.10+ is installed.

- **If missing or too old**: Tell the user to install Python from https://python.org/downloads and make sure to check "Add to PATH" during install. Wait for them to confirm before continuing.
- **If present**: Report the version and move on.

### Step 2: Install Python Dependencies

Run `pip show ttkbootstrap` to check if it's installed.

- **If missing**: Run `pip install ttkbootstrap` and verify it succeeds.
- **If present**: Skip.

### Step 3: Check for KoboldCpp

Check if `koboldcpp.exe` exists in the project directory.

- **If missing**: Ask the user about their GPU:
  - **NVIDIA GPU with CUDA**: Direct them to download the CUDA version from the KoboldCpp GitHub releases page (https://github.com/LostRuins/koboldcpp/releases). They want the file named `koboldcpp.exe` (the CUDA build). Tell them to place it in the same directory as `llama-manager.py`.
  - **No NVIDIA GPU / CPU only**: Direct them to download `koboldcpp_nocuda.exe` and rename it to `koboldcpp.exe`.
  - Wait for them to confirm the download before continuing.
- **If present**: Report found and move on.

### Step 4: Check for GGUF Models

Look for `.gguf` files in the project directory.

- **If none found**: Help them choose a model based on their VRAM. Use `AskUserQuestion` to ask about their setup:
  - **8 GB VRAM or less**: Recommend `Qwen2.5-7B-Instruct-Q4_K_M.gguf` (~4.7 GB) or `Phi-3.5-mini-instruct-Q4_K_M.gguf` (~2.3 GB)
  - **12-16 GB VRAM**: Recommend `Qwen2.5-14B-Instruct-Q4_K_M.gguf` (~8.9 GB) or `DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf` (~8.9 GB)
  - **24+ GB VRAM or multi-GPU**: Recommend `Qwen2.5-32B-Instruct-Q4_K_M.gguf` (~19.9 GB) or `Qwen2.5-Coder-32B-Instruct-Q4_K_M.gguf` for coding tasks
  - **48+ GB VRAM (multi-GPU)**: They can also consider `Llama-3.3-70B-Instruct-Q4_K_M.gguf` (~42 GB)
  - Provide the HuggingFace download link for their chosen model. Tell them to place the `.gguf` file in the project directory.
- **If models exist**: List them and move on.

### Step 5: Test Launch

Run `python llama-manager.py` to verify the GUI launches. Tell the user the GUI should appear - they can close it to continue.

If it fails, read the error and help debug. Common issues:
- `ModuleNotFoundError: ttkbootstrap` - go back to step 2
- `DLL load failed` - may need Visual C++ Redistributable

### Step 6: Build Exe (Optional)

Ask the user if they want to build a standalone `.exe` that doesn't require Python.

- **If yes**:
  1. Run `pip install pyinstaller` if not already installed
  2. Run `pyinstaller koboldcpp-manager.spec` from the project directory
  3. Verify `dist/KoboldCppManager.exe` was created
  4. Tell them they can distribute this exe - it includes everything needed except `koboldcpp.exe` and the model files
- **If no**: Skip.

### Step 7: Multi-GPU Setup (if applicable)

If the user mentioned multiple GPUs earlier, explain the tensor split feature:
- In the GUI, use the "Tensor Split" dropdown to distribute model layers across GPUs
- For a 4080 Super (16 GB) + 3090 (24 GB) setup, the "40/60" preset works well for 32B models
- They can also use "Custom" and enter exact ratios

### Completion

Summarize what was set up and how to use it:
- Launch: `python llama-manager.py` or `dist/KoboldCppManager.exe`
- Select a model, configure GPU settings, click Start Server
- API endpoint will be at `http://localhost:8080/v1/`
- Compatible with any OpenAI API client

## Important Notes

- KoboldCpp is a **PyInstaller-bundled exe** - never use `subprocess.CREATE_NO_WINDOW` with it or it will silently crash
- KoboldCpp stderr output contains Unicode characters (like `Ċ`) that can crash Windows console encoding - the manager handles this automatically
- Model loading takes 15-60 seconds depending on model size and GPU configuration
- The manager's hardcoded paths (`models_dir`, `koboldcpp`) assume everything is in the same directory - if the user cloned to a different location, they may need to update these paths in `llama-manager.py`
