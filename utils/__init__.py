"""Shared utilities for Q-Tools."""

import os
import platform
import subprocess
from datetime import datetime

OS = platform.system()  # 'Windows', 'Linux', 'Darwin'


def human_size(num_bytes):
    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
        if num_bytes < 1024:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024
    return f"{num_bytes:.1f} PB"


def get_creation_time(path):
    try:
        st = os.stat(path)
        if OS == "Windows":
            ts = st.st_ctime
        else:
            ts = getattr(st, "st_birthtime", st.st_mtime)
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "—"


def open_in_file_manager(filepath):
    try:
        if OS == "Windows":
            subprocess.Popen(["explorer", "/select,", os.path.normpath(filepath)])
        elif OS == "Darwin":
            subprocess.Popen(["open", "-R", filepath])
        else:
            folder = os.path.dirname(filepath) or "."
            subprocess.Popen(["xdg-open", folder])
    except Exception as e:
        from tkinter import messagebox
        messagebox.showerror("Open failed", str(e))


def copy_to_clipboard(text):
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except Exception:
        pass
    try:
        from tkinter import Tk
        root = Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return True
    except Exception:
        return False


def open_url(url):
    try:
        if OS == "Windows":
            os.startfile(url)  # type: ignore
        elif OS == "Darwin":
            subprocess.Popen(["open", url])
        else:
            subprocess.Popen(["xdg-open", url])
    except Exception:
        pass