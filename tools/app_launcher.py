"""App Launcher tool - index installed apps and launch them by name."""

import os
import subprocess

import customtkinter as ctk

from tools import BaseTool
from ui.widgets import ACCENT, ACCENT_HOVER, BORDER, CARD, ERROR, MUTED, SUCCESS
from utils import OS


class AppIndex:
    """Collects launchable applications for the current OS."""

    def __init__(self):
        self.apps = {}
        self._scan()

    def _scan(self):
        try:
            if OS == "Windows":
                self._scan_windows()
            elif OS == "Linux":
                self._scan_linux()
            elif OS == "Darwin":
                self._scan_mac()
        except Exception:
            pass

    def _scan_windows(self):
        roots = [
            os.path.join(os.environ.get("APPDATA", ""),
                         r"Microsoft\Windows\Start Menu\Programs"),
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
        ]
        for root in roots:
            if not os.path.isdir(root):
                continue
            for dirpath, _, files in os.walk(root):
                for f in files:
                    if f.lower().endswith((".lnk", ".url", ".exe")):
                        name = os.path.splitext(f)[0].lower()
                        self.apps.setdefault(name, os.path.join(dirpath, f))

    def _scan_linux(self):
        dirs = [
            "/usr/share/applications",
            "/usr/local/share/applications",
            os.path.expanduser("~/.local/share/applications"),
        ]
        for d in dirs:
            if not os.path.isdir(d):
                continue
            for f in os.listdir(d):
                if f.endswith(".desktop"):
                    self.apps.setdefault(f[:-8].lower(), os.path.join(d, f))

    def _scan_mac(self):
        for d in ["/Applications", "/System/Applications",
                  os.path.expanduser("~/Applications")]:
            if not os.path.isdir(d):
                continue
            for f in os.listdir(d):
                if f.endswith(".app"):
                    self.apps.setdefault(f[:-4].lower(), os.path.join(d, f))

    def find(self, query):
        q = query.strip().lower()
        if not q:
            return None
        if q in self.apps:
            return q, self.apps[q]
        for name, path in self.apps.items():
            if name.startswith(q):
                return name, path
        for name, path in self.apps.items():
            if q in name:
                return name, path
        return None

    def matches(self, query, limit=12):
        q = query.strip().lower()
        if not q:
            return []
        out = [(n, p) for n, p in self.apps.items() if q in n]
        out.sort(key=lambda x: (not x[0].startswith(q), len(x[0])))
        return out[:limit]

    def launch(self, path):
        if OS == "Windows":
            os.startfile(path)  # type: ignore
        elif OS == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["gtk-launch", os.path.basename(path)[:-8]],
                             stderr=subprocess.DEVNULL)


class AppLauncherTool(BaseTool):
    id = "app_launcher"
    name = "App Launcher"
    category = "file"
    icon = "⚡"
    description = "Find and open any installed application by typing its name."
    keywords = ["launch", "open", "app", "program", "start", "run"]

    def __init__(self, app=None):
        super().__init__(app)
        self.index = AppIndex()

    def build(self, parent):
        root = ctk.CTkFrame(parent, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=22, pady=(16, 18))
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(root, text="Type: open <app name>  and press Enter",
                     text_color=MUTED, anchor="w",
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="ew")

        self.entry = ctk.CTkEntry(
            root, placeholder_text="open whatsapp", height=38,
            border_width=1, border_color=BORDER,
        )
        self.entry.grid(row=1, column=0, sticky="ew", pady=(8, 8))
        self.entry.bind("<Return>", lambda e: self.launch())
        ctk.CTkButton(root, text="Launch", width=110, height=34,
                      fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self.launch).grid(row=2, column=0, sticky="w",
                                                pady=(0, 8))

        self.suggestions = ctk.CTkFrame(root, fg_color="transparent")
        self.suggestions.grid(row=3, column=0, sticky="ew", pady=(0, 6))
        self.entry.bind("<KeyRelease>", lambda e: self._suggest())

        self.results = ctk.CTkScrollableFrame(
            root, corner_radius=10, border_width=1, border_color=BORDER)
        self.results.grid(row=4, column=0, sticky="nsew", pady=(0, 8))
        self.results.grid_columnconfigure(0, weight=1)

        self.status = ctk.CTkLabel(
            root, text=f"{len(self.index.apps)} apps indexed on this system.",
            text_color=MUTED, anchor="w", font=ctk.CTkFont(size=12))
        self.status.grid(row=5, column=0, sticky="ew")

    # ---- suggestions ----
    def _suggest(self):
        for w in self.suggestions.winfo_children():
            w.destroy()
        q = self.entry.get().strip()
        if not q or q.lower().startswith("open "):
            return
        for name, _ in self.index.matches(q, 6):
            b = ctk.CTkButton(
                self.suggestions, text=name.title(), width=0, height=26,
                fg_color=CARD, hover_color="#2e2e2e", text_color="#e5e7eb",
                font=ctk.CTkFont(size=12),
                command=lambda n=name: self._use(n),
            )
            b.pack(side="left", padx=(0, 6))

    def _use(self, name):
        self.entry.delete(0, "end")
        self.entry.insert(0, f"open {name}")
        self.launch()

    # ---- launch ----
    def launch(self):
        raw = self.entry.get().strip()
        if not raw:
            return
        q = raw[5:].strip() if raw.lower().startswith("open ") else raw

        for w in self.results.winfo_children():
            w.destroy()
        for w in self.suggestions.winfo_children():
            w.destroy()

        match = self.index.find(q)
        if not match:
            self.status.configure(
                text=f"No app found for “{raw}” — check the spelling.",
                text_color=ERROR)
            lbl = ctk.CTkLabel(
                self.results,
                text=(f"No application named “{raw}” was found.\n"
                      "Is the application installed?"),
                text_color=ERROR, justify="left", wraplength=420,
                font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
            lbl.grid(row=0, column=0, sticky="w", padx=12, pady=14)
            return

        name, path = match
        try:
            self.index.launch(path)
        except Exception as e:
            self.status.configure(text=f"Launch failed: {e}", text_color=ERROR)
            return

        self.status.configure(text=f"Found: {name}", text_color=SUCCESS)
        card = ctk.CTkFrame(self.results, corner_radius=8, fg_color="#1f3d2a")
        card.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card, text=f"✅  Launched: {name.title()}", anchor="w",
                     font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, sticky="ew", padx=12, pady=(10, 2))
        ctk.CTkLabel(card, text=path, text_color=MUTED, anchor="w",
                     wraplength=460, justify="left",
                     font=ctk.CTkFont(size=10)).grid(
            row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
