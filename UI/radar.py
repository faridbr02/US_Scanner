import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import math
import threading
import queue
import serial
import time
from random import randint

# -------------------- CONFIGURATION --------------------
class RadarConfig:
    def __init__(self, port="COM8", min_a=0, max_a=180, min_d=2, max_d=400, step=2.0):
        self.port = port
        self.scan_min = min_a
        self.scan_max = max_a
        self.dist_min = min_d
        self.dist_max = max_d
        self.step = step

data_queue = queue.Queue()

# -------------------- INITIALIZATION --------------------
root = tk.Tk()
root.title("Pro Radar - UART Command Center")
root.geometry("1100x950")
root.configure(bg="#F8F9FA")

COLOR_NAV      = "#212529"
COLOR_ACCENT   = "#0D6EFD"
COLOR_INPUT_BG = "#343A40"
PANEL_WIDTH    = 380
FADE_COLORS    = ["#E9ECEF", "#DEE2E6", "#ADB5BD", "#6C757D"]

current_config = RadarConfig()
is_scanning    = False
serial_conn    = None
trail_lines    = []

# -------------------- ICONS --------------------
def load_icon(path, size=(20, 20)):
    try:
        img = Image.open(path).resize(size)
        return ImageTk.PhotoImage(img)
    except:
        return None

icon_menu     = load_icon("icons/Menu.png")
icon_back     = load_icon("icons/back.png")
icon_terminal = load_icon("icons/terminal.png")

# -------------------- UART TRANSMISSION --------------------
def send_config():
    global serial_conn
    if serial_conn and serial_conn.is_open:
        packet = (
                  f"{current_config.scan_min},"
                  f"{current_config.scan_max},"
                  f"{current_config.step},"
                  f"{current_config.dist_max}\n")
        try:
            serial_conn.write(packet.encode('utf-8'))
            terminal_log(f"TX (SENT): {packet.strip()}")
        except Exception as e:
            terminal_log(f"TX ERROR: {str(e)}")
    else:
        terminal_log("TX FAILED: Serial port is not open.")

# -------------------- LOGIC & THREADING --------------------
def process_raw_data(line):
    if ',' in line:
        try:
            angle, dist = map(float, line.split(','))
            data_queue.put((angle, dist))
        except ValueError:
            terminal_log(f"RX (RAW): {line}")
    else:
        # Log non-data messages from Arduino
        terminal_log(f"RX: {line}")

def uart_reader():
    global is_scanning, serial_conn
    while is_scanning:
        if serial_conn and serial_conn.is_open:
            try:
                if serial_conn.in_waiting > 0:
                    line = serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        process_raw_data(line)
            except Exception as e:
                terminal_log(f"READ ERROR: {str(e)}")
                time.sleep(0.1)
        time.sleep(0.01)

def manual_test_send(event=None):
    cmd = term_input.get().strip()
    if cmd:
        if serial_conn and serial_conn.is_open:
            try:
                serial_conn.write(f"{cmd}\n".encode('utf-8'))
                terminal_log(f"TX: {cmd}")
            except Exception as e:
                terminal_log(f"TX ERROR: {str(e)}")
        else:
            # Simulate locally if not connected
            process_raw_data(cmd)
            terminal_log(f"SIM: {cmd}")
        term_input.delete(0, tk.END)

def check_queue():
    try:
        while True:
            angle, dist = data_queue.get_nowait()
            draw_needle(angle, dist)
    except queue.Empty:
        pass
    root.after(20, check_queue)

def terminal_log(msg):
    term_output.config(state="normal")
    term_output.insert(tk.END, f"{msg}\n")
    term_output.see(tk.END)
    term_output.config(state="disabled")

# -------------------- DRAWING --------------------
def draw_needle(angle, dist):
    cx, cy, radius = 550, 450, 300
    rad = math.radians(angle)
    x_end = cx + radius * math.cos(rad)
    y_end = cy - radius * math.sin(rad)

    if len(trail_lines) >= 4:
        canvas.delete(trail_lines.pop(0))
    for i, line_id in enumerate(trail_lines):
        canvas.itemconfig(line_id, fill=FADE_COLORS[i])

    new_line = canvas.create_line(cx, cy, x_end, y_end,
                                   fill=COLOR_ACCENT, width=3, capstyle="round")
    trail_lines.append(new_line)

    if current_config.dist_min <= dist <= current_config.dist_max:
        obs_r = (dist / current_config.dist_max) * radius
        ox = cx + obs_r * math.cos(rad)
        oy = cy - obs_r * math.sin(rad)
        dot = canvas.create_oval(ox-5, oy-5, ox+5, oy+5,
                                  fill="#FD7E14", outline="#FFCA2C")
        root.after(3000, lambda d=dot: canvas.delete(d))

def draw_radar_background():
    canvas.delete("grid")
    cx, cy, radius =550, 450, 300
    for i in range(1, 5):
        r = (radius / 4) * i
        canvas.create_arc(cx-r, cy-r, cx+r, cy+r,
                          start=0, extent=180,
                          outline="#DEE2E6", style="arc", tags="grid")
        dist_label = int(current_config.dist_min +
                         (current_config.dist_max - current_config.dist_min) / 4 * i)
        canvas.create_text(cx+r, cy+15, text=f"{dist_label}cm",
                           fill="#ADB5BD", font=("Arial", 8), tags="grid")

# -------------------- PANEL ANIMATION --------------------
def _animate_panel(panel, target, step):
    cur = panel.winfo_x()
    if step > 0 and cur < target:
        panel.place(x=min(cur + step, target))
        root.after(10, lambda: _animate_panel(panel, target, step))
    elif step < 0 and cur > target:
        panel.place(x=max(cur + step, target))
        root.after(10, lambda: _animate_panel(panel, target, step))

def slide_settings_in():
    settings_panel.lift()
    _animate_panel(settings_panel, 0, step=40)

def slide_settings_out():
    _animate_panel(settings_panel, -PANEL_WIDTH, step=-40)

def slide_terminal_in():
    terminal_panel.lift()
    _animate_panel(terminal_panel, 0, step=40)

def slide_terminal_out():
    root_w = root.winfo_width()
    _animate_panel(terminal_panel, -PANEL_WIDTH, step=-40)

# -------------------- UI ACTIONS --------------------
def toggle_serial():
    global is_scanning, serial_conn
    if not is_scanning:
        try:
            serial_conn = serial.Serial(current_config.port, 115200, timeout=1)
            is_scanning = True
            start_btn.config(text="STOP", bg="#DC3545")
            terminal_log(f"SYSTEM: Connected to {current_config.port} @ 9600 baud")
            threading.Thread(target=uart_reader, daemon=True).start()
        except Exception as e:
            terminal_log(f"SYSTEM: Port {current_config.port} not found - {str(e)}")
            terminal_log("SYSTEM: Simulation mode active.")
            is_scanning = False
            start_btn.config(text="OPEN SERIAL", bg="#198754")
    else:
        is_scanning = False
        if serial_conn and serial_conn.is_open:
            serial_conn.close()
        start_btn.config(text="Start", bg="#198754")
        terminal_log("SYSTEM: Offline.")

def apply_settings():
    try:
        current_config.port = port_e.get()
        current_config.scan_min, current_config.scan_max = int(min_scan_e.get()), int(max_scan_e.get())
        current_config.dist_min, current_config.dist_max = int(min_dist_e.get()), int(max_dist_e.get())
        current_config.step = int(step_e.get())
        draw_radar_background()
        slide_settings_out()
        send_config()
    except ValueError:
        messagebox.showerror("Error", "Please enter valid numbers.")

# ==================== UI LAYOUT ====================

# ---- Radar canvas — centred ----
canvas = tk.Canvas(root, width=900, height=680, bg="white", highlightthickness=0)
canvas.place(relx=0.6, rely=0.46, anchor="center")

# ---- OPEN SERIAL button — centred bottom ----
start_btn = tk.Button(root, text="Start", bg="#198754", fg="white",
                      font=("Arial", 11, "bold"), bd=0,
                      padx=60, pady=15, command=toggle_serial)
start_btn.place(relx=0.6, rely=0.93, anchor="center")

# ---- MENU button — bottom LEFT ----
btn_menu = tk.Button(root, image=icon_menu, text=" MENU", compound="left",
                     bg=COLOR_ACCENT, fg="white",
                     font=("Arial", 10, "bold"), bd=0,
                     padx=20, pady=10, command=slide_settings_in)
btn_menu.place(relx=0.03, rely=0.97, anchor="sw")

# ---- TERMINAL button — bottom RIGHT ----
btn_terminal = tk.Button(root, image=icon_terminal, text="  TERMINAL ", compound="left",
                         bg="#343A40", fg="white",
                         font=("Arial", 10, "bold"), bd=0,
                         padx=20, pady=10, command=slide_terminal_in)
btn_terminal.place(relx=0.03, rely=0.87, anchor="sw")

# ==================== SETTINGS PANEL — slides from LEFT ====================
settings_panel = tk.Frame(root, bg=COLOR_NAV, width=PANEL_WIDTH)
settings_panel.place(x=-PANEL_WIDTH, y=0, relheight=1, width=PANEL_WIDTH)

btn_back_settings = tk.Button(settings_panel, image=icon_back, text=" RETOUR",
                               compound="left", bg=COLOR_NAV, fg="white", bd=0,
                               font=("Arial", 9, "bold"), command=slide_settings_out)
btn_back_settings.place(x=15, y=15)

tk.Label(settings_panel, text="PARAMÈTRES", fg="white", bg=COLOR_NAV,
         font=("Helvetica", 14, "bold")).pack(pady=(70, 20))

def create_compact_input(label, val1, val2=None):
    c = tk.Frame(settings_panel, bg=COLOR_NAV)
    c.pack(fill="x", padx=40, pady=5)
    tk.Label(c, text=label, fg="#ADB5BD", bg=COLOR_NAV,
             font=("Arial", 8, "bold")).pack(anchor="w")
    f = tk.Frame(c, bg=COLOR_NAV)
    f.pack(fill="x")
    e1 = tk.Entry(f, bg=COLOR_INPUT_BG, fg="white", bd=0,
                  justify="center", font=("Arial", 10))
    e1.insert(0, val1)
    e1.pack(side="left", expand=True, fill="x", ipady=5)
    if val2:
        tk.Label(f, text="to", fg="white", bg=COLOR_NAV).pack(side="left", padx=5)
        e2 = tk.Entry(f, bg=COLOR_INPUT_BG, fg="white", bd=0,
                      justify="center", font=("Arial", 10))
        e2.insert(0, val2)
        e2.pack(side="left", expand=True, fill="x", ipady=5)
        return e1, e2
    return e1

port_e                 = create_compact_input("SERIAL PORT", "COM8")
min_scan_e, max_scan_e = create_compact_input("RANGE D'ANGLE (°)", "0", "180")
min_dist_e, max_dist_e = create_compact_input("RANGE DE DISTANCE (cm)", "2", "400")
step_e                 = create_compact_input("PRÉCISION DU PAS (°)", "2")

tk.Button(settings_panel, text="APPLIQUER & ENVOYER", bg=COLOR_ACCENT, fg="white",
          bd=0, pady=12, command=apply_settings).pack(
          side="bottom", fill="x", padx=40, pady=40)

# ==================== TERMINAL PANEL — slides from RIGHT ====================
root.update_idletasks()
root_w = root.winfo_width()

terminal_panel = tk.Frame(root, bg="#1E1E1E", width=PANEL_WIDTH)
terminal_panel.place(x=-PANEL_WIDTH, y=0, relheight=1, width=PANEL_WIDTH)

btn_back_terminal = tk.Button(terminal_panel, image=icon_back, text=" FERMER",
                               compound="left", bg="#1E1E1E", fg="white", bd=0,
                               font=("Arial", 9, "bold"), command=slide_terminal_out)
btn_back_terminal.place(x=15, y=15)

tk.Label(terminal_panel, text="UART TERMINAL", fg="white", bg="#1E1E1E",
         font=("Helvetica", 14, "bold")).pack(pady=(70, 10))

tk.Label(terminal_panel, text="OUTPUT", fg="#6C757D", bg="#1E1E1E",
         font=("Consolas", 8, "bold")).pack(anchor="w", padx=20)

term_output = tk.Text(terminal_panel, bg="#0D0D0D", fg="#00FF00",
                      font=("Consolas", 8), bd=0, state="disabled",
                      wrap="word", relief="flat")
term_output.pack(fill="both", expand=True, padx=15, pady=(4, 0))

tk.Label(terminal_panel, text="SEND COMMAND", fg="#6C757D", bg="#1E1E1E",
         font=("Consolas", 8, "bold")).pack(anchor="w", padx=20, pady=(10, 0))

term_input = tk.Entry(terminal_panel, bg="#2D2D2D", fg="white", bd=0,
                      font=("Consolas", 9), insertbackground="white", relief="flat")
term_input.pack(fill="x", padx=15, pady=(4, 20), ipady=8)
term_input.bind("<Return>", manual_test_send)

# -------------------- START --------------------
draw_radar_background()
check_queue()
terminal_log("SYSTEM: Radar UI initialized. Ready.")
root.mainloop()