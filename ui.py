import tkinter as tk
import psutil
import GPUtil
from utils import format_bytes, get_network_speed
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import collections

# Try importing Windows-specific APIs for transparency effect
try:
    from ctypes import windll, Structure, sizeof, byref
    import ctypes
    IS_WINDOWS = True
except ImportError:
    IS_WINDOWS = False


class SystemMonitorUI:
    def __init__(self):
        # Base window setup
        self.root = tk.Tk()
        self.root.title("🖥️ System Monitor")
        self.root.geometry("400x600")
        self.root.configure(bg="#1e1e2f")  # dark background by default
        self.dark_mode = True
        self.refresh_rate = 1000  # default update interval in ms

        # If Windows, apply acrylic blur (glassmorphic effect)
        if IS_WINDOWS:
            self.enable_blur_effect()

        # Font styling
        self.font = ("Segoe UI", 12, "bold")
        self.label_fg = "#ffffff"
        self.label_bg = "#1e1e2f"
        self.highlight = "#00ffcc"  # neon cyan for buttons

        # Labels dictionary holds all the text displays for system info
        self.labels = {}
        for name in ["CPU", "RAM", "Disk", "GPU", "Network"]:
            label = tk.Label(self.root, font=self.font, bg=self.label_bg, fg=self.label_fg, text=f"{name}: Loading...")
            label.pack(pady=8)
            self.labels[name] = label

        # User-controlled refresh slider to change update interval
        self.slider = tk.Scale(
            self.root, from_=500, to=5000, label="Refresh Rate (ms)", orient="horizontal",
            bg=self.label_bg, fg=self.label_fg, highlightbackground=self.label_bg,
            troughcolor="#444", font=("Segoe UI", 10, "bold")
        )
        self.slider.set(self.refresh_rate)
        self.slider.pack(pady=10)

        # Button for switching between light/dark mode
        self.theme_button = tk.Button(
            self.root, text="Toggle Theme 🌓", command=self.toggle_theme,
            bg=self.highlight, fg="#000000", font=self.font, relief="flat"
        )
        self.theme_button.pack(pady=12)

        # Deques for storing 60 seconds of CPU and RAM history
        self.cpu_data = collections.deque([0]*60, maxlen=60)
        self.ram_data = collections.deque([0]*60, maxlen=60)

        # Set up live Matplotlib plot with two subplots stacked vertically
        self.fig, self.ax = plt.subplots(2, 1, figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(pady=10)

        # Start the periodic update loop
        self.update_stats()

    def enable_blur_effect(self):
        # Native Windows blur behind the window using undocumented API.
        # Applies a translucent acrylic effect on Windows 10+
        class ACCENTPOLICY(ctypes.Structure):
            _fields_ = [
                ("AccentState", ctypes.c_int),
                ("AccentFlags", ctypes.c_int),
                ("GradientColor", ctypes.c_int),
                ("AnimationId", ctypes.c_int)
            ]

        class WINCOMPATTRDATA(ctypes.Structure):
            _fields_ = [
                ("Attribute", ctypes.c_int),
                ("Data", ctypes.c_void_p),
                ("SizeOfData", ctypes.c_size_t)
            ]

        # Set blur-behind
        accent = ACCENTPOLICY()
        accent.AccentState = 3  # ACCENT_ENABLE_BLURBEHIND
        accent.GradientColor = 0x01000000  # Color alpha set to enable transparency

        # Bundle data into Windows composition structure
        data = WINCOMPATTRDATA()
        data.Attribute = 19  # WCA_ACCENT_POLICY
        data.Data = ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p)
        data.SizeOfData = sizeof(accent)

        # Apply blur to the window handle
        hwnd = windll.user32.GetParent(self.root.winfo_id())
        windll.user32.SetWindowCompositionAttribute(hwnd, byref(data))

    def get_gpu_info(self):
        # Query the first GPU using GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]
            return f"{gpu.load * 100:.0f}% | Temp: {gpu.temperature}°C"
        return "Not available"  # fallback if no GPU is detected

    def update_stats(self):
        # Pull real-time system stats
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        gpu_info = self.get_gpu_info()
        upload, download = get_network_speed()

        # Update the UI text labels with current data
        self.labels["CPU"].config(text=f"CPU Usage: {cpu}%")
        self.labels["RAM"].config(
            text=f"Memory: {ram.percent}% ({format_bytes(ram.used)} / {format_bytes(ram.total)})"
        )
        self.labels["Disk"].config(text=f"Disk Usage: {disk.percent}%")
        self.labels["GPU"].config(text=f"GPU: {gpu_info}")
        self.labels["Network"].config(
            text=f"↑ {format_bytes(upload)}/s ↓ {format_bytes(download)}/s"
        )

        # Append new data points to the graph history
        self.cpu_data.append(cpu)
        self.ram_data.append(ram.percent)

        # --- Chart Rendering ---
        # Clear the previous plots
        self.ax[0].clear()
        self.ax[1].clear()

        # Draw CPU chart
        self.ax[0].plot(self.cpu_data, color='cyan')
        self.ax[0].set_title("CPU Usage (%)", fontsize=10)
        self.ax[0].tick_params(labelsize=8)

        # Draw RAM chart
        self.ax[1].plot(self.ram_data, color='magenta')
        self.ax[1].set_title("RAM Usage (%)", fontsize=10)
        self.ax[1].tick_params(labelsize=8)

        # Adjust spacing to avoid overlap (tight_layout causes issues)
        self.fig.subplots_adjust(hspace=0.5)
        self.canvas.draw()

        # Schedule next update using current slider value
        self.refresh_rate = self.slider.get()
        self.root.after(self.refresh_rate, self.update_stats)

    def toggle_theme(self):
        # Flip theme state
        self.dark_mode = not self.dark_mode

        # Define theme colors
        if self.dark_mode:
            self.label_bg = "#1e1e2f"
            self.label_fg = "#ffffff"
            self.highlight = "#00ffcc"
        else:
            self.label_bg = "#f4f4f4"
            self.label_fg = "#000000"
            self.highlight = "#3366ff"

        # Re-apply theme to all widgets
        self.root.config(bg=self.label_bg)
        for label in self.labels.values():
            label.config(bg=self.label_bg, fg=self.label_fg)
        self.slider.config(
            bg=self.label_bg, fg=self.label_fg, highlightbackground=self.label_bg,
            troughcolor="#888"
        )
        self.theme_button.config(bg=self.highlight, fg="#000000")

    def run(self):
        # Launch the GUI event loop
        self.root.mainloop()
