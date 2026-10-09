"""File Finder tool - threaded disk search with live results."""

import os
import threading
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog

from tools import BaseTool
from ui.widgets import ACCENT, ACCENT_HOVER, BORDER, CARD, DIM, MUTED
from utils import get_creation_time, human_size, open_in_file_manager

SKIP_NAMES = {
    "$recycle.bin", "system volume information", "node_modules", ".git",
    "__pycache__", "windows", "proc", "sys", "dev", ".venv", "venv",
}


def search_files(query, root, cancel_flag, on_result, on_done):
    q = query.lower()
    try:
        for dirpath, dirnames, filenames in os.walk(Path(root), topdown=True):
            if cancel_flag["stop"]:
                break
            dirnames[:] = [d for d in dirnames
                           if d.lower() not in SKIP_NAMES and not d.startswith(".")]
            for f in filenames:
                if cancel_flag["stop"]:
                    break
                if q in f.lower():
                    full = os.path.join(dirpath, f)
                    try:
                        size = os.path.getsize(full)
                    except OSError:
                        size = 0
                    on_result({
                        "name": f,
                        "path": full,
                        "size": size,
                        "created": get_creation_time(full),
                    })
    finally:
        on_done()


class FileFinderTool(BaseTool):
    id = "file_finder"
    name = "File Finder"
    category = "file"
    icon = "🔍"
    description = "Search files by name anywhere on disk and jump to them."
    keywords = ["search", "find", "locate", "disk", "filename", "lookup"]

    def __init__(self, app=None):
        super().__init__(app)
        self.search_root = str(Path.home())
        self.cancel_flag = {"stop": False}
        self._searching = False

    def build(self, parent):
        root = ctk.CTkFrame(parent, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=22, pady=(16, 18))
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(3, weight=1)

        # search row
        row = ctk.CTkFrame(root, fg_color="transparent")
        row.grid(row=0, column=0, sticky="ew")
        row.grid_columnconfigure(0, weight=1)
        self.entry = ctk.CTkEntry(
            row, placeholder_text="Search files by name…  (e.g. report.pdf)",
            height=38, border_width=1, border_color=BORDER,
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.entry.bind("<Return>", lambda e: self.start())
        self.btn = ctk.CTkButton(
            row, text="Search", width=110, height=38,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, command=self.start,
        )
        self.btn.grid(row=0, column=1)

        # folder row
        row2 = ctk.CTkFrame(root, fg_color="transparent")
        row2.grid(row=1, column=0, sticky="ew", pady=(10, 8))
        row2.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(row2, text="Folder:", text_color=MUTED,
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, padx=(0, 8))
        self.folder_label = ctk.CTkLabel(
            row2, text=self.search_root, anchor="w", text_color="#e5e7eb",
            font=ctk.CTkFont(size=12),
        )
        self.folder_label.grid(row=0, column=1, sticky="ew")
        ctk.CTkButton(
            row2, text="Change", width=86, height=28, fg_color=BORDER,
            hover_color="#333333", command=self.choose_folder,
        ).grid(row=0, column=2)

        # results
        self.results = ctk.CTkScrollableFrame(
            root, corner_radius=10, border_width=1, border_color=BORDER,
        )
        self.results.grid(row=3, column=0, sticky="nsew", pady=(4, 8))
        self.results.grid_columnconfigure(0, weight=1)

        # status
        self.status = ctk.CTkLabel(root, text="Ready.", text_color=MUTED,
                                   anchor="w", font=ctk.CTkFont(size=12))
        self.status.grid(row=4, column=0, sticky="ew", pady=(4, 0))

    # ---- actions ----
    def choose_folder(self):
        d = filedialog.askdirectory(initialdir=self.search_root)
        if d:
            self.search_root = d
            self.folder_label.configure(text=d)

    def start(self):
        query = self.entry.get().strip()
        if not query:
            return
        if self._searching:
            self.cancel_flag["stop"] = True
            return
        for w in self.results.winfo_children():
            w.destroy()

        self.cancel_flag = {"stop": False}
        self._searching = True
        self.btn.configure(text="Stop")
        self.status.configure(text=f"Searching for “{query}”…",
                              text_color="#e5e7eb")

        threading.Thread(
            target=search_files,
            args=(query, self.search_root, self.cancel_flag,
                  lambda info: self.results.after(0, self._add_row, info),
                  lambda: self.results.after(0, self._finish)),
            daemon=True,
        ).start()

    def _add_row(self, info):
        card = ctk.CTkFrame(self.results, corner_radius=8, fg_color=CARD)
        card.pack(fill="x", pady=4, padx=2)
        card.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 0))
        top.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top, text=f"📄  {info['name']}", anchor="w",
                     font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, sticky="ew")
        ctk.CTkButton(
            top, text="👁", width=38, height=28, fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            command=lambda p=info["path"]: open_in_file_manager(p),
        ).grid(row=0, column=1, padx=(6, 0))

        meta = f"{human_size(info['size'])}   •   {info['created']}"
        ctk.CTkLabel(card, text=meta, text_color=MUTED, anchor="w",
                     font=ctk.CTkFont(size=11)).grid(
            row=1, column=0, sticky="ew", padx=12, pady=(2, 0))
        ctk.CTkLabel(card, text=info["path"], text_color=DIM, anchor="w",
                     wraplength=560, justify="left",
                     font=ctk.CTkFont(size=10)).grid(
            row=2, column=0, sticky="ew", padx=12, pady=(0, 8))

    def _finish(self):
        self._searching = False
        self.btn.configure(text="Search")
        count = len(self.results.winfo_children())
        plural = "es" if count != 1 else ""
        self.status.configure(text=f"Done. {count} match{plural} found.",
                              text_color=MUTED)
