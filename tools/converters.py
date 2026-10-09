"""Converter & system tools: unit converter, system info, ping, notes,
clipboard viewer."""

import os
import platform
import queue
import shutil
import socket
import subprocess
import threading
import time
from datetime import datetime

import customtkinter as ctk

from tools import BaseTool
from ui.widgets import (
    ERROR, MUTED, SUCCESS, WARN, ToolLayout, copy_box, get_text, set_text,
)
from utils import OS, human_size


# ==========================================================================
# 1. Unit converter
# ==========================================================================
_UNITS = {
    "Length": {
        "Millimeter": 0.001, "Centimeter": 0.01, "Meter": 1,
        "Kilometer": 1000, "Inch": 0.0254, "Foot": 0.3048, "Yard": 0.9144,
        "Mile": 1609.344, "Nautical mile": 1852,
    },
    "Mass": {
        "Milligram": 1e-6, "Gram": 0.001, "Kilogram": 1, "Ton": 1000,
        "Ounce": 0.028349523125, "Pound": 0.45359237, "Stone": 6.35029318,
    },
    "Temperature": {
        "Celsius": "C", "Fahrenheit": "F", "Kelvin": "K",
    },
    "Data": {
        "Bit": 1 / 8, "Byte": 1, "KB": 1024, "MB": 1024 ** 2,
        "GB": 1024 ** 3, "TB": 1024 ** 4, "PB": 1024 ** 5,
    },
    "Time": {
        "Millisecond": 0.001, "Second": 1, "Minute": 60, "Hour": 3600,
        "Day": 86400, "Week": 604800, "Year": 31557600,
    },
    "Area": {
        "Square centimeter": 1e-4, "Square meter": 1, "Hectare": 10000,
        "Square kilometer": 1e6, "Square inch": 0.00064516,
        "Square foot": 0.09290304, "Acre": 4046.8564224,
        "Square mile": 2589988.110336,
    },
    "Speed": {
        "m/s": 1, "km/h": 1 / 3.6, "mph": 0.44704, "ft/s": 0.3048,
        "knot": 0.514444444,
    },
}


def _to_celsius(value, unit):
    return {"C": value, "F": (value - 32) * 5 / 9, "K": value - 273.15}[unit]


def _from_celsius(value, unit):
    return {"C": value, "F": value * 9 / 5 + 32, "K": value + 273.15}[unit]


class UnitConverterTool(BaseTool):
    id = "unit_converter"
    name = "Unit Converter"
    category = "converter"
    icon = "📐"
    description = "Length, mass, temperature, data, time, area and speed."
    keywords = ["convert", "unit", "length", "mass", "temperature", "speed"]

    def build(self, parent):
        lay = ToolLayout(parent)
        self.layout = lay

        self.cat_menu = lay.option_menu(
            "Category", list(_UNITS), default="Length",
            command=self._category_changed, width=200)

        row1 = lay.row()
        ctk.CTkLabel(row1, text="From:", font=ctk.CTkFont(size=12),
                     text_color=MUTED).pack(side="left", padx=(0, 8))
        self.value_entry = ctk.CTkEntry(row1, width=150, height=34)
        self.value_entry.insert(0, "1")
        self.value_entry.pack(side="left", padx=(0, 10))
        self.from_menu = ctk.CTkOptionMenu(row1, width=170, height=34,
                                           fg_color="#2a2a2a",
                                           button_color="#2f6feb")
        self.from_menu.pack(side="left")

        row2 = lay.row()
        ctk.CTkLabel(row2, text="To:", font=ctk.CTkFont(size=12),
                     text_color=MUTED).pack(side="left", padx=(0, 8))
        self.to_menu = ctk.CTkOptionMenu(row2, width=150, height=34,
                                         fg_color="#2a2a2a",
                                         button_color="#2f6feb")
        self.to_menu.pack(side="left", padx=(0, 10))
        ctk.CTkButton(row2, text="Swap", width=80, height=34,
                      fg_color="#2a2a2a", hover_color="#333333",
                      command=self._swap).pack(side="left")

        out_row = lay.row()
        self.out_label = ctk.CTkLabel(
            out_row, text="—", anchor="w", height=64, corner_radius=10,
            fg_color="#232323", font=ctk.CTkFont(size=24, weight="bold"))
        self.out_label.pack(fill="x", padx=(34, 0), pady=(6, 6))

        lay.buttons([
            ("Convert", self.convert),
            ("Copy result", self.copy_result),
        ])
        self.value_entry.bind("<KeyRelease>", lambda e: self.convert())
        self.from_menu.configure(command=lambda _: self.convert())
        self.to_menu.configure(command=lambda _: self.convert())
        self.status = lay.status()
        self._category_changed("Length")
        self.convert()

    def _names(self):
        return list(_UNITS[self.cat_menu.get()])

    def _category_changed(self, _value=None):
        names = self._names()
        self.from_menu.configure(values=names)
        self.to_menu.configure(values=names)
        self.from_menu.set(names[0])
        self.to_menu.set(names[1] if len(names) > 1 else names[0])
        self.convert()

    def _swap(self):
        a, b = self.from_menu.get(), self.to_menu.get()
        self.from_menu.set(b)
        self.to_menu.set(a)
        self.convert()

    def convert(self):
        raw = self.value_entry.get().strip().replace(",", "")
        if not raw:
            self.out_label.configure(text="—")
            return
        try:
            value = float(raw)
        except ValueError:
            self.out_label.configure(text="invalid number")
            self.status.set("Enter a number.", ERROR)
            return
        cat = self.cat_menu.get()
        src, dst = self.from_menu.get(), self.to_menu.get()
        units = _UNITS[cat]

        if cat == "Temperature":
            result = _from_celsius(_to_celsius(value, units[src]), units[dst])
        else:
            result = value * units[src] / units[dst]

        text = f"{result:,.6f}".rstrip("0").rstrip(".")
        if text in ("", "-"):
            text = "0"
        if abs(result) >= 1e15 or (0 < abs(result) < 1e-6):
            text = f"{result:.6e}"
        self.out_label.configure(text=f"{text} {dst}")
        self.status.set(f"{value:g} {src} = {text} {dst}", SUCCESS)

    def copy_result(self):
        text = str(self.out_label.cget("text"))
        if text in ("—", "invalid number"):
            self.status.set("Nothing to copy.", WARN)
            return
        from utils import copy_to_clipboard
        ok = copy_to_clipboard(text)
        self.status.set("Copied." if ok else "Clipboard unavailable.",
                        SUCCESS if ok else ERROR)


# ==========================================================================
# 2. System info
# ==========================================================================
def _memory_info():
    try:
        if OS == "Windows":
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                return stat.ullTotalPhys, stat.ullAvailPhys, stat.dwMemoryLoad
        else:
            page = os.sysconf("SC_PAGE_SIZE")
            pages = os.sysconf("SC_PHYS_PAGES")
            total = page * pages
            try:
                avail = page * os.sysconf("SC_AVPHYS_PAGES")
            except (ValueError, OSError):
                avail = 0
            return total, avail, 0
    except Exception:
        return 0, 0, 0


def _disks():
    out = []
    if OS == "Windows":
        from string import ascii_uppercase
        for letter in ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                try:
                    usage = shutil.disk_usage(drive)
                    out.append((drive, usage.total, usage.free))
                except OSError:
                    pass
    else:
        for mount in ("/", "/home", "/mnt"):
            if os.path.exists(mount):
                try:
                    usage = shutil.disk_usage(mount)
                    out.append((mount, usage.total, usage.free))
                except OSError:
                    pass
    return out


def _system_report():
    total, avail, _load = _memory_info()
    win_build = platform.win32_ver()[1] if OS == "Windows" else "-"
    lines = [
        "── System ─────────────────────────────────",
        f"OS              : {platform.system()} {platform.release()}",
        f"Version         : {platform.version()}",
        f"OS build        : {win_build}",
        f"Machine         : {platform.machine()}",
        f"Processor       : {platform.processor() or platform.machine()}",
        f"CPU cores       : {os.cpu_count()}",
        f"Hostname        : {socket.gethostname()}",
        f"User            : {os.environ.get('USERNAME') or os.environ.get('USER') or '-'}",
        f"Python          : {platform.python_version()}",
        f"Local time      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Timezone        : {time.tzname[0]} (UTC{time.timezone / -3600:+.1f})",
        "",
    ]
    if total:
        lines += [
            "── Memory ─────────────────────────────────",
            f"Total RAM       : {human_size(total)}",
            f"Available       : {human_size(avail)}",
            f"Used            : {human_size(total - avail)}",
            "",
        ]
    lines.append("── Disks ──────────────────────────────────")
    for mount, disk_total, disk_free in _disks():
        pct = (1 - disk_free / disk_total) * 100 if disk_total else 0
        lines.append(f"{mount:<16} {human_size(disk_total):>10} total   "
                     f"{human_size(disk_free):>10} free   {pct:.0f}% used")
    return "\n".join(lines)


class SystemInfoTool(BaseTool):
    id = "system_info"
    name = "System Info"
    category = "system"
    icon = "🖥"
    description = "Hardware, OS, memory and disk overview of this machine."
    keywords = ["system", "info", "hardware", "memory", "disk", "cpu", "specs"]

    def build(self, parent):
        lay = ToolLayout(parent)
        self.layout = lay
        lay.buttons([("Refresh", self.refresh),
                     ("Copy", lambda: copy_box(self.out, self.status))])
        self.out = lay.box("Report", height=380, readonly=True, weight=1)
        self.status = lay.status()
        self.refresh()

    def refresh(self):
        try:
            set_text(self.out, _system_report())
            self.status.set("Updated.", SUCCESS)
        except Exception as e:
            self.status.set(f"Failed: {e}", ERROR)


# ==========================================================================
# 3. Ping
# ==========================================================================
class PingTool(BaseTool):
    id = "ping"
    name = "Ping"
    category = "system"
    icon = "📡"
    description = "Measure latency to a host and watch packets in real time."
    keywords = ["ping", "latency", "network", "host", "diagnose", "connection"]

    def __init__(self, app=None):
        super().__init__(app)
        self._proc = None
        self._queue = queue.Queue()
        self._running = False

    def build(self, parent):
        lay = ToolLayout(parent)
        self.layout = lay

        row = lay.row()
        ctk.CTkLabel(row, text="Host:", font=ctk.CTkFont(size=12),
                     text_color=MUTED).pack(side="left", padx=(0, 8))
        self.host_entry = ctk.CTkEntry(row, width=240, height=34,
                                       placeholder_text="8.8.8.8  or  google.com")
        self.host_entry.insert(0, "8.8.8.8")
        self.host_entry.pack(side="left", padx=(0, 10))
        self.host_entry.bind("<Return>", lambda e: self.start())

        self.count_menu = ctk.CTkOptionMenu(
            row, values=["3", "5", "10"], width=70, height=34,
            fg_color="#2a2a2a", button_color="#2f6feb")
        self.count_menu.set("5")
        self.count_menu.pack(side="left", padx=(0, 12))

        self.run_btn = ctk.CTkButton(row, text="Start", width=100, height=34,
                                     fg_color="#22c55e", hover_color="#16a34a",
                                     command=self.start)
        self.run_btn.pack(side="left")

        lay.buttons([("Clear", lambda: set_text(self.out, "")),
                     ("Copy", lambda: copy_box(self.out, self.status))])
        self.out = lay.box("Output", height=300, readonly=True, weight=1)
        self.status = lay.status()
        self.host_entry.focus_set()

    def start(self):
        if self._running:
            self.stop()
            return
        host = self.host_entry.get().strip()
        if not host:
            self.status.set("Enter a host first.", ERROR)
            return
        count = self.count_menu.get()
        if OS == "Windows":
            cmd = ["ping", "-n", count, host]
        else:
            cmd = ["ping", "-c", count, host]

        set_text(self.out, f"$ {' '.join(cmd)}\n")
        self._running = True
        self.run_btn.configure(text="Stop", fg_color="#ef4444",
                               hover_color="#b91c1c")
        self.status.set(f"Pinging {host}…", SUCCESS)

        def worker():
            try:
                self._proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding="utf-8", errors="replace")
                assert self._proc.stdout is not None
                for line in self._proc.stdout:
                    self._queue.put(line)
                self._proc.wait()
            except Exception as e:
                self._queue.put(f"error: {e}")
            finally:
                self._queue.put(None)

        threading.Thread(target=worker, daemon=True).start()
        self.out.after(80, self._drain)

    def _drain(self):
        try:
            while True:
                line = self._queue.get_nowait()
                if line is None:
                    self._finish()
                    return
                box = self.out
                box.configure(state="normal")
                box.insert("end", line)
                box.see("end")
                box.configure(state="disabled")
        except queue.Empty:
            pass
        if self._running:
            self.out.after(120, self._drain)

    def stop(self):
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:
                pass
        self._running = False
        self.run_btn.configure(text="Start", fg_color="#22c55e",
                               hover_color="#16a34a")
        self.status.set("Stopped.", WARN)

    def _finish(self):
        self._running = False
        self.run_btn.configure(text="Start", fg_color="#22c55e",
                               hover_color="#16a34a")
        self.status.set("Done.", SUCCESS)


# ==========================================================================
# 4. Notes
# ==========================================================================
class NotesTool(BaseTool):
    id = "notes"
    name = "Quick Notes"
    category = "misc"
    icon = "🗒"
    description = "A tiny scratchpad that saves to a local notes.txt file."
    keywords = ["notes", "scratchpad", "memo", "todo", "write", "text"]

    def __init__(self, app=None):
        super().__init__(app)
        self.path = os.path.join(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))), "notes.txt")

    def build(self, parent):
        lay = ToolLayout(parent)
        self.layout = lay
        lay.buttons([
            ("Save", self.save),
            ("Load", self.load),
            ("Clear", self.clear),
            ("Copy", lambda: copy_box(self.out, self.status)),
        ])
        self.out = lay.box("Editor — Ctrl+S to save", height=380, weight=1)
        self.count_lbl = lay.label("", size=12, color=MUTED)
        self.status = lay.status()
        self.out.bind("<KeyRelease>", lambda e: self._count())
        self.out.bind("<Control-s>", lambda e: (self.save(), "break")[1])
        self.load()

    def _count(self):
        text = get_text(self.out)
        words = len(text.split())
        self.count_lbl.configure(
            text=f"{words} word(s)   •   {len(text)} character(s)   •   "
                 f"{self.path}")

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as fh:
                fh.write(get_text(self.out))
        except OSError as e:
            self.status.set(f"Save failed: {e}", ERROR)
            return
        self._count()
        self.status.set(f"Saved to {self.path}", SUCCESS)

    def load(self):
        if not os.path.exists(self.path):
            self._count()
            self.status.set("No notes file yet — write something and Save.",
                            WARN)
            return
        try:
            with open(self.path, encoding="utf-8") as fh:
                content = fh.read()
        except OSError as e:
            self.status.set(f"Load failed: {e}", ERROR)
            return
        set_text(self.out, content)
        self._count()
        self.status.set(f"Loaded {self.path}", SUCCESS)

    def clear(self):
        set_text(self.out, "")
        self._count()
        self.status.set("Editor cleared (not saved yet).", WARN)


# ==========================================================================
# 5. Clipboard viewer
# ==========================================================================
def _read_clipboard():
    try:
        import pyperclip
        return pyperclip.paste()
    except Exception:
        pass
    try:
        import tkinter
        root = tkinter._default_root
        if root is not None:
            return str(root.clipboard_get())
    except Exception:
        pass
    return None


class ClipboardTool(BaseTool):
    id = "clipboard_viewer"
    name = "Clipboard Viewer"
    category = "misc"
    icon = "📋"
    description = "Watch the system clipboard and keep a recent history."
    keywords = ["clipboard", "copy", "paste", "history", "watch"]

    def __init__(self, app=None):
        super().__init__(app)
        self._last = None
        self._history = []
        self._auto = True

    def build(self, parent):
        lay = ToolLayout(parent)
        self.layout = lay
        lay.buttons([
            ("Refresh", self.refresh),
            ("Copy current", lambda: self._copy_current()),
            ("Clear history", self._clear_history),
        ])
        self.auto_cb = lay.checkbox("Auto-refresh every second", default=True,
                                    command=self._toggle_auto)
        self.out = lay.box("Current clipboard", height=130, readonly=True)
        self.hist_box = lay.box("History (newest first)", height=180,
                                readonly=True, weight=1)
        self.status = lay.status()
        self.refresh()
        self._tick()

    def _toggle_auto(self):
        self._auto = self.auto_cb.var.get()

    def _tick(self):
        if self._auto:
            self.refresh()
        try:
            self.hist_box.after(1000, self._tick)
        except Exception:
            pass

    def refresh(self):
        text = _read_clipboard()
        if text is None:
            self.status.set("Clipboard is empty or unavailable.", WARN)
            return
        set_text(self.out, text if text else "(empty)")
        if text and text != self._last:
            self._last = text
            preview = text if len(text) <= 4000 else text[:4000] + " …"
            self._history.insert(0, preview)
            self._history = self._history[:20]
            set_text(self.hist_box,
                     "\n\n".join(f"{i + 1}. {h}"
                                 for i, h in enumerate(self._history)))
            self.status.set("Clipboard updated.", SUCCESS)

    def _copy_current(self):
        copy_box(self.out, self.status)

    def _clear_history(self):
        self._history = []
        set_text(self.hist_box, "")
        self.status.set("History cleared.", WARN)
