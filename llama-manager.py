import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import messagebox
import tkinter as tk
import subprocess
import threading
import os
import queue
import time
import webbrowser
import urllib.request
import json
import socket

class LlamaManager:
    # Popular GGUF models with download links (HuggingFace)
    POPULAR_MODELS = [
        {
            "name": "Llama-3.3-70B-Instruct-Q4_K_M.gguf",
            "url": "https://huggingface.co/bartowski/Llama-3.3-70B-Instruct-GGUF/resolve/main/Llama-3.3-70B-Instruct-Q4_K_M.gguf",
            "size": "42 GB"
        },
        {
            "name": "Llama-3.2-3B-Instruct-Q8_0.gguf",
            "url": "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q8_0.gguf",
            "size": "3.4 GB"
        },
        {
            "name": "Mistral-7B-Instruct-v0.3-Q4_K_M.gguf",
            "url": "https://huggingface.co/bartowski/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/Mistral-7B-Instruct-v0.3-Q4_K_M.gguf",
            "size": "4.4 GB"
        },
        {
            "name": "Qwen2.5-7B-Instruct-Q4_K_M.gguf",
            "url": "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf",
            "size": "4.7 GB"
        },
        {
            "name": "Qwen2.5-14B-Instruct-Q4_K_M.gguf",
            "url": "https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF/resolve/main/qwen2.5-14b-instruct-q4_k_m.gguf",
            "size": "8.9 GB"
        },
        {
            "name": "Qwen2.5-32B-Instruct-Q4_K_M.gguf",
            "url": "https://huggingface.co/Qwen/Qwen2.5-32B-Instruct-GGUF/resolve/main/qwen2.5-32b-instruct-q4_k_m.gguf",
            "size": "19.9 GB"
        },
        {
            "name": "Phi-3.5-mini-instruct-Q4_K_M.gguf",
            "url": "https://huggingface.co/bartowski/Phi-3.5-mini-instruct-GGUF/resolve/main/Phi-3.5-mini-instruct-Q4_K_M.gguf",
            "size": "2.3 GB"
        },
        {
            "name": "gemma-2-9b-it-Q4_K_M.gguf",
            "url": "https://huggingface.co/bartowski/gemma-2-9b-it-GGUF/resolve/main/gemma-2-9b-it-Q4_K_M.gguf",
            "size": "5.8 GB"
        },
        {
            "name": "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf",
            "url": "https://huggingface.co/bartowski/DeepSeek-R1-Distill-Qwen-7B-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf",
            "size": "4.7 GB"
        },
        {
            "name": "DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf",
            "url": "https://huggingface.co/bartowski/DeepSeek-R1-Distill-Qwen-14B-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-14B-Q4_K_M.gguf",
            "size": "8.9 GB"
        },
        {
            "name": "DeepSeek-R1-Distill-Qwen-32B-Q4_K_M.gguf",
            "url": "https://huggingface.co/bartowski/DeepSeek-R1-Distill-Qwen-32B-GGUF/resolve/main/DeepSeek-R1-Distill-Qwen-32B-Q4_K_M.gguf",
            "size": "19.9 GB"
        },
    ]

    CONTEXT_LENGTHS = ["2048", "4096", "8192", "16384", "32768", "65536", "131072"]

    def __init__(self, root):
        self.root = root
        self.root.title("KoboldCpp Server Manager")
        self.root.geometry("800x750")

        self.server_process = None
        self.models_dir = r"C:\Users\cory\projects\models"
        self.koboldcpp = r"C:\Users\cory\projects\models\koboldcpp.exe"
        self.current_model = None
        self.host = "127.0.0.1"
        self.port = 8080
        self.working = False
        self.monitor_active = False
        self.monitor_failures = 0
        self.monitor_restarts = 0
        self.error_lines = []
        self.error_lines_lock = threading.Lock()

        # Queue for thread-safe UI updates
        self.ui_queue = queue.Queue()

        self.setup_styles()
        self.create_widgets()
        self.process_queue()

        # Initial tasks on background thread
        self.run_async(self.init_tasks)

    def setup_styles(self):
        # ttkbootstrap handles theming automatically
        pass

    def create_widgets(self):
        # Header
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=X, padx=20, pady=15)

        ttk.Label(header_frame, text="KoboldCpp Server Manager", font=("Segoe UI", 16, "bold")).pack(side=LEFT)

        # Theme selector
        self.theme_var = tk.StringVar(value="darkly")
        theme_combo = ttk.Combobox(header_frame, textvariable=self.theme_var, width=12, state="readonly")
        theme_combo["values"] = ["darkly", "superhero", "solar", "cyborg", "vapor", "cosmo", "flatly", "minty", "morph", "pulse", "quartz"]
        theme_combo.pack(side=RIGHT, padx=5)
        theme_combo.bind("<<ComboboxSelected>>", self.change_theme)
        ttk.Label(header_frame, text="Theme:").pack(side=RIGHT)

        # Spinner/working indicator
        self.spinner_label = ttk.Label(header_frame, text="", bootstyle="info")
        self.spinner_label.pack(side=RIGHT, padx=10)

        # Status frame
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=X, padx=20, pady=10)

        self.status_label = ttk.Label(status_frame, text="● Server: Stopped", font=("Segoe UI", 11), bootstyle="danger")
        self.status_label.pack(side=LEFT, padx=5)

        # Model selection
        model_frame = ttk.Frame(self.root)
        model_frame.pack(fill="x", padx=20, pady=10)

        ttk.Label(model_frame, text="Model:").pack(anchor="w")

        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, width=70, state="readonly")
        self.model_combo.pack(fill="x", pady=5)

        # Buttons frame
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=20, pady=10)

        self.start_btn = ttk.Button(btn_frame, text="Start Server", bootstyle="success", command=lambda: self.run_async(self.start_server))
        self.start_btn.pack(side=LEFT, padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="Stop Server", bootstyle="danger", command=lambda: self.run_async(self.stop_server), state=DISABLED)
        self.stop_btn.pack(side=LEFT, padx=5)

        ttk.Button(btn_frame, text="Refresh", bootstyle="secondary", command=lambda: self.run_async(self.refresh_models)).pack(side=LEFT, padx=5)

        # Settings frame
        settings_frame = ttk.Frame(self.root)
        settings_frame.pack(fill="x", padx=20, pady=10)

        # LAN toggle
        self.lan_var = tk.BooleanVar(value=False)
        lan_check = ttk.Checkbutton(settings_frame, text="Enable LAN (0.0.0.0)", variable=self.lan_var, command=self.toggle_lan, bootstyle="round-toggle")
        lan_check.pack(side=LEFT, padx=5)

        # Port
        ttk.Label(settings_frame, text="Port:").pack(side="left", padx=(20, 5))
        self.port_var = tk.StringVar(value="8080")
        port_entry = ttk.Entry(settings_frame, textvariable=self.port_var, width=8)
        port_entry.pack(side="left")

        # GPU layers
        ttk.Label(settings_frame, text="GPU Layers:").pack(side="left", padx=(20, 5))
        self.gpu_var = tk.StringVar(value="99")
        gpu_entry = ttk.Entry(settings_frame, textvariable=self.gpu_var, width=5)
        gpu_entry.pack(side="left")

        # Context length
        ttk.Label(settings_frame, text="Context:").pack(side="left", padx=(20, 5))
        self.context_var = tk.StringVar(value="8192")
        context_combo = ttk.Combobox(settings_frame, textvariable=self.context_var, values=self.CONTEXT_LENGTHS, width=8, state="readonly")
        context_combo.pack(side="left")

        # GPU Settings frame (second row)
        gpu_frame = ttk.Frame(self.root)
        gpu_frame.pack(fill="x", padx=20, pady=5)

        # CUDA checkbox
        self.cuda_var = tk.BooleanVar(value=True)
        cuda_check = ttk.Checkbutton(gpu_frame, text="Use CUDA", variable=self.cuda_var, command=self.toggle_cuda, bootstyle="success-round-toggle")
        cuda_check.pack(side=LEFT, padx=5)

        # Tensor split
        ttk.Label(gpu_frame, text="Tensor Split:").pack(side="left", padx=(20, 5))
        self.tensor_split_var = tk.StringVar(value="Auto")
        self.tensor_split_combo = ttk.Combobox(gpu_frame, textvariable=self.tensor_split_var, width=20, state="readonly")
        self.tensor_split_combo["values"] = [
            "Auto",
            "GPU 0 only",
            "GPU 1 only",
            "50/50",
            "40/60 (4080/3090)",
            "60/40 (4080/3090)",
            "Custom"
        ]
        self.tensor_split_combo.pack(side="left")
        self.tensor_split_combo.bind("<<ComboboxSelected>>", self.on_tensor_split_change)

        # Custom tensor split entry (hidden by default)
        self.custom_split_var = tk.StringVar(value="0.4,0.6")
        self.custom_split_entry = ttk.Entry(gpu_frame, textvariable=self.custom_split_var, width=12)
        # Don't pack yet - will be shown when "Custom" is selected

        # Monitor frame (third row)
        monitor_frame = ttk.Frame(self.root)
        monitor_frame.pack(fill="x", padx=20, pady=5)

        self.monitor_var = tk.BooleanVar(value=False)
        monitor_check = ttk.Checkbutton(
            monitor_frame, text="Monitor & Auto-Restart",
            variable=self.monitor_var, command=self.toggle_monitor,
            bootstyle="warning-round-toggle"
        )
        monitor_check.pack(side=LEFT, padx=5)

        self.monitor_status_label = ttk.Label(monitor_frame, text="", font=("Consolas", 9))
        self.monitor_status_label.pack(side=LEFT, padx=(10, 0))

        # Monitor interval
        ttk.Label(monitor_frame, text="Interval:").pack(side=LEFT, padx=(20, 5))
        self.monitor_interval_var = tk.StringVar(value="5")
        interval_combo = ttk.Combobox(
            monitor_frame, textvariable=self.monitor_interval_var,
            values=["3", "5", "10", "15", "30", "60"], width=4, state="readonly"
        )
        interval_combo.pack(side=LEFT)
        ttk.Label(monitor_frame, text="sec").pack(side=LEFT, padx=(2, 0))

        # Max restart attempts
        ttk.Label(monitor_frame, text="Max restarts:").pack(side=LEFT, padx=(20, 5))
        self.max_restarts_var = tk.StringVar(value="3")
        restarts_combo = ttk.Combobox(
            monitor_frame, textvariable=self.max_restarts_var,
            values=["1", "3", "5", "10", "0"], width=4, state="readonly"
        )
        restarts_combo.pack(side=LEFT)

        # Server info
        info_frame = ttk.Frame(self.root)
        info_frame.pack(fill="x", padx=20, pady=15)

        ttk.Label(info_frame, text="Connection Info:", font=("Segoe UI", 12, "bold")).pack(anchor=W)

        endpoint_row = ttk.Frame(info_frame)
        endpoint_row.pack(anchor="w", fill="x", pady=2)
        self.endpoint_label = ttk.Label(endpoint_row, text="API Endpoint: Not running")
        self.endpoint_label.pack(side=LEFT)
        self.copy_btn = ttk.Button(endpoint_row, text="Copy", bootstyle="info-outline", command=self.copy_endpoint, padding=(5, 1))
        # Hidden until server starts

        self.lan_endpoint_label = ttk.Label(info_frame, text="")
        self.lan_endpoint_label.pack(anchor="w", pady=2)

        self.model_label = ttk.Label(info_frame, text="Loaded Model: None")
        self.model_label.pack(anchor="w", pady=2)

        # Log area
        log_frame = ttk.Frame(self.root)
        log_frame.pack(fill="x", padx=20, pady=10)

        ttk.Label(log_frame, text="Log:").pack(anchor="w")

        self.log_text = tk.Text(log_frame, height=6, bg="#2d2d2d", fg="#cccccc", font=("Consolas", 9))
        self.log_text.pack(fill="x")

        # Download section
        download_frame = ttk.Frame(self.root)
        download_frame.pack(fill="both", expand=True, padx=20, pady=10)

        download_header = ttk.Frame(download_frame)
        download_header.pack(fill="x")

        ttk.Label(download_header, text="Available Models (click to download):", font=("Segoe UI", 12, "bold")).pack(side=LEFT)
        ttk.Button(download_header, text="Check Available", bootstyle="info-outline", command=lambda: self.run_async(self.check_available_models)).pack(side=RIGHT)

        # Create scrollable text widget for download links
        self.download_text = tk.Text(download_frame, height=8, bg="#2d2d2d", fg="#cccccc", font=("Consolas", 9), cursor="arrow")
        self.download_text.pack(fill="both", expand=True, pady=5)

        # Configure tags for clickable links
        self.download_text.tag_configure("link", foreground="#00aaff", underline=True)
        self.download_text.tag_configure("installed", foreground="#44ff44")
        self.download_text.tag_configure("size", foreground="#888888")
        self.download_text.config(state="disabled")

    def process_queue(self):
        """Process UI updates from background threads"""
        try:
            while True:
                func, args = self.ui_queue.get_nowait()
                try:
                    func(*args)
                except Exception as e:
                    print(f"UI queue error: {e}")
        except queue.Empty:
            pass
        self.root.after(50, self.process_queue)

    def ui_update(self, func, *args):
        """Queue a UI update from background thread"""
        self.ui_queue.put((func, args))

    def run_async(self, func):
        """Run function in background thread"""
        self.log(f"run_async called for {func.__name__}")
        threading.Thread(target=self._async_wrapper, args=(func,), daemon=True).start()

    def _async_wrapper(self, func):
        """Wrapper that shows spinner during async work"""
        self.working = True
        self.ui_update(self._start_spinner)
        try:
            func()
        except Exception as e:
            self.ui_update(self.log, f"Error: {e}")
        finally:
            self.working = False
            self.ui_update(self._stop_spinner)

    def _start_spinner(self):
        self._spinner_running = True
        self._animate_spinner()

    def _stop_spinner(self):
        self._spinner_running = False
        self.spinner_label.config(text="")

    def _animate_spinner(self):
        if not self._spinner_running:
            return
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        current = self.spinner_label.cget("text")
        try:
            idx = frames.index(current)
            next_idx = (idx + 1) % len(frames)
        except ValueError:
            next_idx = 0
        self.spinner_label.config(text=frames[next_idx] + " Working...")
        self.root.after(80, self._animate_spinner)

    def log(self, message):
        def _log():
            self.log_text.insert("end", f"{message}\n")
            self.log_text.see("end")
        # Schedule on main thread if called from background
        try:
            self.log_text.insert("end", f"{message}\n")
            self.log_text.see("end")
        except:
            self.ui_queue.put((_log, ()))

    def init_tasks(self):
        """Initial background tasks"""
        self.refresh_models()
        self.check_server_status()
        self.check_available_models()

    def refresh_models(self):
        self.ui_update(self.log, "Scanning for models...")
        models = []
        if os.path.exists(self.models_dir):
            for f in os.listdir(self.models_dir):
                if f.endswith(".gguf"):
                    models.append(f)

        def update_combo():
            self.model_combo["values"] = models
            if models:
                self.model_combo.current(0)
            self.log(f"Found {len(models)} GGUF model(s)")

        self.ui_update(update_combo)

    def toggle_lan(self):
        if self.lan_var.get():
            if not messagebox.askyesno("Security Warning",
                "Enabling LAN mode will expose your LLM server to all devices on your network.\n\n"
                "KoboldCpp has NO authentication. Anyone on your network can send requests.\n\n"
                "Continue?"):
                self.lan_var.set(False)
                return
            self.host = "0.0.0.0"
            self.log("WARNING: LAN access enabled - server exposed to network (no auth)")
        else:
            self.host = "127.0.0.1"
            self.log("LAN access disabled")

    def toggle_cuda(self):
        if self.cuda_var.get():
            self.log("CUDA enabled - will use NVIDIA GPU(s)")
        else:
            self.log("CUDA disabled - using CPU only")

    def change_theme(self, event=None):
        theme = self.theme_var.get()
        self.root.style.theme_use(theme)
        self.log(f"Theme changed to: {theme}")

    def on_tensor_split_change(self, event=None):
        selection = self.tensor_split_var.get()
        if selection == "Custom":
            self.custom_split_entry.pack(side="left", padx=(5, 0))
            self.log("Enter custom tensor split ratio (e.g., 0.4,0.6)")
        else:
            self.custom_split_entry.pack_forget()

    def get_tensor_split_value(self):
        """Convert tensor split selection to command line argument"""
        selection = self.tensor_split_var.get()
        if selection == "Auto" or not self.cuda_var.get():
            return None
        elif selection == "GPU 0 only":
            return "1,0"
        elif selection == "GPU 1 only":
            return "0,1"
        elif selection == "50/50":
            return "0.5,0.5"
        elif selection == "40/60 (4080/3090)":
            return "0.4,0.6"
        elif selection == "60/40 (4080/3090)":
            return "0.6,0.4"
        elif selection == "Custom":
            return self.custom_split_var.get()
        return None

    def start_server(self):
        model = self.model_var.get()
        if not model:
            self.ui_update(messagebox.showerror, "Error", "Please select a model")
            return

        if not os.path.exists(self.koboldcpp):
            self.ui_update(self.log, f"ERROR: koboldcpp.exe not found")
            self.ui_update(messagebox.showerror, "Error", f"koboldcpp.exe not found at:\n{self.koboldcpp}")
            return

        model_path = os.path.join(self.models_dir, model)
        if not os.path.exists(model_path):
            self.ui_update(self.log, f"ERROR: Model not found")
            self.ui_update(messagebox.showerror, "Error", f"Model not found")
            return

        port = self.port_var.get()
        try:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                raise ValueError
        except ValueError:
            self.ui_update(messagebox.showerror, "Error", "Port must be a number between 1 and 65535")
            return

        gpu_layers = self.gpu_var.get()
        try:
            int(gpu_layers)
        except ValueError:
            self.ui_update(messagebox.showerror, "Error", "GPU layers must be a number")
            return

        host = "0.0.0.0" if self.lan_var.get() else "127.0.0.1"
        context_len = self.context_var.get()
        use_cuda = self.cuda_var.get()
        tensor_split = self.get_tensor_split_value()

        self.ui_update(self.log, f"Starting: {model}")
        cuda_info = f"CUDA: {'ON' if use_cuda else 'OFF'}"
        if use_cuda and tensor_split:
            cuda_info += f", Split: {tensor_split}"
        self.ui_update(self.log, f"Host: {host}:{port}, GPU layers: {gpu_layers}, Context: {context_len}, {cuda_info}")

        try:
            # Build command as list for direct execution (not via shell)
            cmd_list = [
                self.koboldcpp,
                "--model", model_path,
                "--host", host,
                "--port", port,
                "--contextsize", context_len,
                "--skiplauncher"
            ]

            if use_cuda:
                cmd_list.append("--usecuda")
                cmd_list.extend(["--gpulayers", gpu_layers])
                if tensor_split:
                    cmd_list.extend(["--tensor_split", tensor_split])

            self.ui_update(self.log, f"Command: {' '.join(cmd_list)}")

            # Run with stderr capture so errors show in the log
            self.server_process = subprocess.Popen(
                cmd_list,
                cwd=self.models_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            self.current_model = model
            self.ui_update(self.log, f"Process started (PID: {self.server_process.pid})")

            # Clear error log on new server start
            with self.error_lines_lock:
                self.error_lines.clear()

            # Stream stdout/stderr in background
            def read_output(pipe, label):
                try:
                    for line in iter(pipe.readline, b''):
                        text = line.decode('utf-8', errors='replace').rstrip()
                        if text:
                            self.ui_update(self.log, f"[{label}] {text}")
                            if label == "err":
                                with self.error_lines_lock:
                                    self.error_lines.append(text)
                except Exception as e:
                    self.ui_update(self.log, f"[{label}] reader error: {e}")
                finally:
                    pipe.close()

            threading.Thread(target=read_output, args=(self.server_process.stdout, "out"), daemon=True).start()
            threading.Thread(target=read_output, args=(self.server_process.stderr, "err"), daemon=True).start()

            # Wait for server to be ready (model loading can take 30-60 seconds)
            self.ui_update(self.log, "Waiting for server to initialize (this may take 30-60 seconds)...")
            for i in range(90):  # Increased timeout to 90 seconds
                time.sleep(1)
                if self._is_server_running():
                    self.ui_update(self.log, "Server is ready!")
                    self.ui_update(self._update_status, True, host, port)
                    return
                if self.server_process.poll() is not None:
                    exit_code = self.server_process.returncode
                    self.ui_update(self.log, f"Server process exited with code: {exit_code}")
                    break

            self.ui_update(self.log, "Server failed to start")
            self.ui_update(self._update_status, False, host, port)

        except Exception as e:
            self.ui_update(self.log, f"Error: {e}")

    def stop_server(self):
        self.ui_update(self.log, "Stopping LLM server...")

        # Try graceful shutdown by PID first
        if self.server_process and self.server_process.poll() is None:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                self.ui_update(self.log, f"Server process (PID {self.server_process.pid}) terminated")
            except subprocess.TimeoutExpired:
                self.server_process.kill()
                self.ui_update(self.log, f"Server process (PID {self.server_process.pid}) killed")
            except Exception as e:
                self.ui_update(self.log, f"Error terminating process: {e}")

        # Fallback: kill any remaining kobold processes by name
        processes_to_kill = [
            "koboldcpp.exe",
            "koboldcpp_nocuda.exe",
            "koboldcpp_cu12.exe",
        ]

        killed_any = False
        for proc in processes_to_kill:
            try:
                result = subprocess.run(
                    ["taskkill", "/F", "/IM", proc],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if "SUCCESS" in result.stdout:
                    self.ui_update(self.log, f"Killed: {proc}")
                    killed_any = True
            except Exception as e:
                pass

        if not killed_any:
            self.ui_update(self.log, "No LLM server processes found")
        else:
            self.ui_update(self.log, "All LLM servers stopped")

        self.server_process = None
        self.current_model = None
        self.ui_update(self._update_status, False, self.host, self.port_var.get())

    def _is_server_running(self):
        try:
            import urllib.request
            port = self.port_var.get()
            # Try koboldcpp API endpoint (works for both koboldcpp and llama-server)
            req = urllib.request.urlopen(f"http://localhost:{port}/api/v1/model", timeout=2)
            return req.status == 200
        except:
            return False

    def check_server_status(self):
        running = self._is_server_running()
        host = "0.0.0.0" if self.lan_var.get() else "127.0.0.1"
        port = self.port_var.get()
        self.ui_update(self._update_status, running, host, port)

    def _get_local_ip(self):
        """Get the machine's LAN IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "unknown"

    def copy_endpoint(self):
        """Copy the API endpoint URL to clipboard"""
        text = self.endpoint_label.cget("text")
        url = text.replace("API Endpoint: ", "")
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        self.log(f"Copied to clipboard: {url}")

    def _update_status(self, running, host, port):
        if running:
            self.status_label.config(text="● Server: Running", bootstyle="success")
            self.start_btn.config(state=DISABLED)
            self.stop_btn.config(state=NORMAL)
            endpoint = f"http://{host}:{port}/v1/"
            self.endpoint_label.config(text=f"API Endpoint: {endpoint}")
            self.copy_btn.pack(side=LEFT, padx=(10, 0))
            # Show LAN address when server is running
            local_ip = self._get_local_ip()
            lan_url = f"http://{local_ip}:{port}/v1/"
            self.lan_endpoint_label.config(text=f"LAN Address:    {lan_url}")
            self.model_label.config(text=f"Loaded Model: {self.current_model or 'External'}")
        else:
            self.status_label.config(text="● Server: Stopped", bootstyle="danger")
            self.start_btn.config(state=NORMAL)
            self.stop_btn.config(state=DISABLED)
            self.endpoint_label.config(text="API Endpoint: Not running")
            self.copy_btn.pack_forget()
            self.lan_endpoint_label.config(text="")
            self.model_label.config(text="Loaded Model: None")

    def check_available_models(self):
        """Check which popular models are not installed and show download links"""
        self.ui_update(self.log, "Checking available models...")

        # Get list of installed models
        installed = set()
        if os.path.exists(self.models_dir):
            for f in os.listdir(self.models_dir):
                if f.endswith(".gguf"):
                    installed.add(f.lower())

        # Find models not installed
        available = []
        for model in self.POPULAR_MODELS:
            # Check if any similar named model is installed (case insensitive)
            model_name_lower = model["name"].lower()
            is_installed = any(model_name_lower in inst or inst in model_name_lower for inst in installed)
            available.append({**model, "installed": is_installed})

        self.ui_update(self._display_available_models, available)

    def _display_available_models(self, models):
        """Display available models with clickable links"""
        self.download_text.config(state="normal")
        self.download_text.delete("1.0", "end")

        for model in models:
            if model["installed"]:
                self.download_text.insert("end", "[INSTALLED] ", "installed")
                self.download_text.insert("end", f"{model['name']}\n")
            else:
                # Create clickable link
                link_tag = f"link_{model['name']}"
                self.download_text.tag_configure(link_tag, foreground="#00aaff", underline=True)

                self.download_text.insert("end", f"{model['name']} ", link_tag)
                self.download_text.insert("end", f"({model['size']})", "size")
                self.download_text.insert("end", "\n")

                # Bind click event
                url = model["url"]
                self.download_text.tag_bind(link_tag, "<Button-1>", lambda e, u=url: self._open_download(u))
                self.download_text.tag_bind(link_tag, "<Enter>", lambda e: self.download_text.config(cursor="hand2"))
                self.download_text.tag_bind(link_tag, "<Leave>", lambda e: self.download_text.config(cursor="arrow"))

        self.download_text.config(state="disabled")
        self.log(f"Found {sum(1 for m in models if not m['installed'])} models available for download")

    def _open_download(self, url):
        """Open download URL in browser"""
        self.log(f"Opening download: {url}")
        webbrowser.open(url)

    # ── Monitor & Auto-Restart ──────────────────────────────────

    def toggle_monitor(self):
        if self.monitor_var.get():
            self.monitor_active = True
            self.monitor_failures = 0
            self.monitor_restarts = 0
            self._last_error_count = 0
            self.log("Monitor ON - watching server health + stderr")
            self.ui_update(self.monitor_status_label.config,
                           text="MONITORING", bootstyle="warning")
            threading.Thread(target=self._monitor_loop, daemon=True).start()
        else:
            self.monitor_active = False
            self.log("Monitor OFF")
            self.ui_update(self.monitor_status_label.config, text="", bootstyle="secondary")

    def _drain_new_errors(self):
        """Return new stderr lines since last check"""
        with self.error_lines_lock:
            new_lines = self.error_lines[self._last_error_count:]
            self._last_error_count = len(self.error_lines)
            return new_lines

    def _monitor_loop(self):
        """Background loop that polls server health and stderr for errors"""
        while self.monitor_active:
            interval = int(self.monitor_interval_var.get())
            max_restarts_str = self.max_restarts_var.get()
            max_restarts = int(max_restarts_str) if max_restarts_str != "0" else float('inf')

            server_up = self._is_server_running()
            new_errors = self._drain_new_errors()
            error_count = len(new_errors)

            if server_up and error_count == 0:
                # All clear
                if self.monitor_failures > 0:
                    self.ui_update(self.log, f"[Monitor] Recovered after {self.monitor_failures} failure(s)")
                    self.monitor_failures = 0
                with self.error_lines_lock:
                    total_errs = len(self.error_lines)
                self.ui_update(self.monitor_status_label.config,
                               text=f"OK | errs: {total_errs} | restarts: {self.monitor_restarts}",
                               bootstyle="success")

            elif server_up and error_count > 0:
                # Server responding but stderr activity
                with self.error_lines_lock:
                    total_errs = len(self.error_lines)
                self.ui_update(self.monitor_status_label.config,
                               text=f"ERRORS +{error_count} ({total_errs} total) | restarts: {self.monitor_restarts}",
                               bootstyle="warning")
                self.ui_update(self.log,
                    f"[Monitor] {error_count} new stderr line(s) detected this cycle ({total_errs} total)")
                # Log the actual error lines
                for line in new_errors[-5:]:  # Show last 5 new lines
                    self.ui_update(self.log, f"[Monitor][err] {line[:200]}")
                if error_count > 5:
                    self.ui_update(self.log, f"[Monitor] ...and {error_count - 5} more")

            else:
                # Server DOWN
                self.monitor_failures += 1
                with self.error_lines_lock:
                    total_errs = len(self.error_lines)
                self.ui_update(self.monitor_status_label.config,
                               text=f"DOWN x{self.monitor_failures} | errs: {total_errs} | restarts: {self.monitor_restarts}",
                               bootstyle="danger")

                if new_errors:
                    self.ui_update(self.log,
                        f"[Monitor] Server DOWN + {error_count} stderr line(s):")
                    for line in new_errors[-5:]:
                        self.ui_update(self.log, f"[Monitor][err] {line[:200]}")
                elif self.monitor_failures == 1:
                    self.ui_update(self.log, "[Monitor] Server not responding, watching...")

                if self.monitor_failures >= 3:
                    # 3 consecutive health failures = confirmed down, try restart
                    if self.monitor_restarts >= max_restarts:
                        self.ui_update(self.log,
                            f"[Monitor] Max restarts ({int(max_restarts)}) reached. Stopping monitor.")
                        self.ui_update(self.monitor_status_label.config,
                                       text="HALTED (max restarts)", bootstyle="danger")
                        self.monitor_active = False
                        self.ui_update(self.monitor_var.set, False)
                        break

                    model = self.model_var.get()
                    if model:
                        self.monitor_restarts += 1
                        self.monitor_failures = 0
                        self.ui_update(self.log,
                            f"[Monitor] Auto-restart #{self.monitor_restarts}: {model}")
                        self.start_server()
                    else:
                        self.ui_update(self.log, "[Monitor] No model selected, cannot restart")

            time.sleep(interval)

def main():
    # Available themes: darkly, superhero, solar, cyborg, vapor, cosmo, flatly, journal,
    # litera, lumen, minty, morph, pulse, quartz, sandstone, simplex, sketchy, slate, united, yeti
    root = ttk.Window(themename="darkly")
    app = LlamaManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()
