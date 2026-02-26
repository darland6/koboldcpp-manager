"""
Qwen3.5 llama.cpp Server - System Tray Controller
Right-click the tray icon to start/stop the server.
Icon: green = running, red = stopped

SINGLE INSTANCE via named mutex.
GRACEFUL SHUTDOWN via named event - never leaves ghost icons.
"""

import subprocess
import sys
import threading
import time
import os
import ctypes
import ctypes.wintypes
import urllib.request

kernel32 = ctypes.windll.kernel32
ERROR_ALREADY_EXISTS = 183
INFINITE = 0xFFFFFFFF
EVENT_MODIFY_STATE = 0x0002

MUTEX_NAME = "Global\\Qwen35LlamaCppTray"
SHUTDOWN_EVENT_NAME = "Global\\Qwen35TrayShutdown"

# ── If another instance is running, signal it to exit first ──────
# Try to signal any existing instance to shut down gracefully
existing_event = kernel32.OpenEventW(EVENT_MODIFY_STATE, False, SHUTDOWN_EVENT_NAME)
if existing_event:
    kernel32.SetEvent(existing_event)
    kernel32.CloseHandle(existing_event)
    time.sleep(2)  # Wait for old instance to cleanly remove its icon

# ── Now claim the mutex ──────────────────────────────────────────
mutex_handle = kernel32.CreateMutexW(None, True, MUTEX_NAME)
if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
    # Old instance didn't exit in time - bail out
    kernel32.CloseHandle(mutex_handle)
    sys.exit(0)

# ── Create shutdown event for future instances to signal us ──────
shutdown_event = kernel32.CreateEventW(None, True, False, SHUTDOWN_EVENT_NAME)

# ── Now safe to import heavy deps ────────────────────────────────
import pystray
from PIL import Image, ImageDraw, ImageFont

# ── Config ───────────────────────────────────────────────────────
LLAMA_SERVER = r"C:\Users\cory\projects\models\llama-cpp\bin\llama-server.exe"
MODEL = r"C:\Users\cory\.lmstudio\models\lmstudio-community\Qwen3.5-35B-A3B-GGUF\Qwen3.5-35B-A3B-UD-Q4_K_XL.gguf"
MODEL_FALLBACK = r"C:\Users\cory\.lmstudio\models\lmstudio-community\Qwen3.5-35B-A3B-GGUF\Qwen3.5-35B-A3B-Q4_K_M.gguf"
HOST = "0.0.0.0"
PORT = 8080
HEALTH_URL = f"http://127.0.0.1:{PORT}/health"

SERVER_ARGS = [
    "--host", HOST,
    "--port", str(PORT),
    "--n-gpu-layers", "-1",
    "--main-gpu", "1",
    "--cache-type-k", "q8_0",
    "--cache-type-v", "q8_0",
    "--flash-attn", "on",
    "-np", "1",
    "--ctx-size", "8192",
]

server_process = None
tray_icon = None


def create_icon(running):
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    bg_color = (34, 197, 94) if running else (220, 38, 38)
    draw.rounded_rectangle([4, 4, 60, 60], radius=12, fill=bg_color)
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except OSError:
        font = ImageFont.load_default()
    draw.text((size / 2, size / 2), "Q", fill="white", font=font, anchor="mm")
    return img


def is_server_running():
    try:
        req = urllib.request.urlopen(HEALTH_URL, timeout=2)
        return req.status == 200
    except Exception:
        return False


def start_server(icon, _item=None):
    global server_process
    if is_server_running():
        icon.notify("Server is already running", "Qwen3.5")
        return
    model_path = MODEL if os.path.exists(MODEL) else MODEL_FALLBACK
    if not os.path.exists(model_path):
        icon.notify("No model file found!", "Qwen3.5 Error")
        return
    quant = "UD-Q4_K_XL" if "XL" in model_path else "Q4_K_M"
    cmd = [LLAMA_SERVER, "--model", model_path] + SERVER_ARGS
    server_process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    icon.icon = create_icon(True)
    icon.notify(f"Starting Qwen3.5 ({quant}) on port {PORT}...", "Qwen3.5")

    def wait_for_ready():
        for _ in range(60):
            if is_server_running():
                icon.notify(f"Server ready! ({quant})", "Qwen3.5")
                return
            time.sleep(1)
        icon.notify("Server failed to start", "Qwen3.5 Error")
        icon.icon = create_icon(False)

    threading.Thread(target=wait_for_ready, daemon=True).start()


def stop_server(icon, _item=None):
    global server_process
    if server_process and server_process.poll() is None:
        server_process.terminate()
        try:
            server_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server_process.kill()
        server_process = None
        icon.icon = create_icon(False)
        icon.notify("Server stopped", "Qwen3.5")
    elif is_server_running():
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        for line in result.stdout.splitlines():
            if f":{PORT}" in line and "LISTENING" in line:
                pid = line.strip().split()[-1]
                subprocess.run(
                    ["taskkill", "/PID", pid, "/F"],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                break
        icon.icon = create_icon(False)
        icon.notify("Server stopped", "Qwen3.5")
    else:
        icon.notify("Server is not running", "Qwen3.5")


def on_exit(icon, _item=None):
    if server_process and server_process.poll() is None:
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
    kernel32.CloseHandle(shutdown_event)
    kernel32.CloseHandle(mutex_handle)
    icon.stop()


def get_status_text(_item=None):
    if is_server_running():
        return "Status: RUNNING (port 8080)"
    return "Status: STOPPED"


def watch_shutdown_event():
    """Background thread: wait for another instance to signal us to exit."""
    kernel32.WaitForSingleObject(shutdown_event, INFINITE)
    if tray_icon:
        on_exit(tray_icon)


def setup(icon):
    if is_server_running():
        icon.icon = create_icon(True)


# Start shutdown watcher before icon runs
threading.Thread(target=watch_shutdown_event, daemon=True).start()

menu = pystray.Menu(
    pystray.MenuItem(get_status_text, None, enabled=False),
    pystray.Menu.SEPARATOR,
    pystray.MenuItem("Start Server", start_server),
    pystray.MenuItem("Stop Server", stop_server),
    pystray.Menu.SEPARATOR,
    pystray.MenuItem("Exit", on_exit),
)

running = is_server_running()
tray_icon = pystray.Icon("qwen35", create_icon(running), "Qwen3.5 Server", menu)
tray_icon.run(setup)
