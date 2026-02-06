# KoboldCpp Manager

A Windows GUI for managing [KoboldCpp](https://github.com/LostRuins/koboldcpp) LLM servers. Download, configure, and run GGUF models with multi-GPU support.

![KoboldCpp Manager](https://img.shields.io/badge/platform-Windows-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Python](https://img.shields.io/badge/python-3.10+-yellow)

## Features

- **One-click server management** - Start/stop KoboldCpp with a GUI instead of command lines
- **Multi-GPU tensor splitting** - Presets for common multi-GPU setups (e.g. RTX 4080 + 3090) or custom ratios
- **Model browser** - See installed GGUF models, discover popular ones, download with one click
- **Live server logs** - Stream KoboldCpp stdout/stderr directly in the GUI
- **Configurable** - GPU layers, context length, CUDA toggle, LAN access, port selection
- **Theme support** - 11 ttkbootstrap themes (darkly, superhero, vapor, etc.)
- **OpenAI-compatible API** - KoboldCpp serves models on a standard `/v1/` endpoint

## Quick Start

### Option A: Run from source

```bash
git clone https://github.com/YOUR_USERNAME/koboldcpp-manager.git
cd koboldcpp-manager
pip install -r requirements.txt
python llama-manager.py
```

### Option B: Download the exe

Grab `KoboldCppManager.exe` from [Releases](../../releases) and run it. No Python needed.

### Option C: Guided setup with Claude Code

If you have [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed, it can walk you through the entire setup interactively:

```bash
cd koboldcpp-manager
claude
# Then type: /install-wizard
```

Claude will detect your system, install dependencies, download KoboldCpp and models, and build the exe - all guided step by step.

## Requirements

- **OS**: Windows 10/11
- **Python**: 3.10+ (only needed if running from source)
- **KoboldCpp**: Download from [KoboldCpp releases](https://github.com/LostRuins/koboldcpp/releases) - place `koboldcpp.exe` in the same directory
- **GPU**: NVIDIA GPU with CUDA support recommended (CPU-only works but is slow)
- **Models**: Any GGUF format model (the app helps you find and download them)

## How It Works

1. Place `koboldcpp.exe` and your `.gguf` model files in the same directory as `llama-manager.py`
2. Launch the manager
3. Select a model, configure GPU settings, and click **Start Server**
4. The server exposes an OpenAI-compatible API at `http://localhost:8080/v1/`
5. Point any OpenAI-compatible client at that endpoint

## Multi-GPU Setup

If you have multiple NVIDIA GPUs, use the **Tensor Split** dropdown to distribute the model across them:

| Preset | Description |
|--------|-------------|
| Auto | Let KoboldCpp decide |
| GPU 0 only | Use only the first GPU |
| GPU 1 only | Use only the second GPU |
| 50/50 | Split evenly |
| 40/60 | More on GPU 1 (e.g. 4080 Super + 3090) |
| Custom | Enter your own ratio |

## Building the Exe

```bash
pip install pyinstaller
pyinstaller koboldcpp-manager.spec
# Output: dist/KoboldCppManager.exe
```

## License

MIT
