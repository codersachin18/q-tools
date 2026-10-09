"""File tools: Zip / Unzip and Batch Rename."""

import fnmatch
import os
import zipfile

import customtkinter as ctk
from tkinter import filedialog

from tools import BaseTool
from ui.widgets import (
    ERROR, MUTED, SUCCESS, WARN, ToolLayout, copy_box, set_text,
)
from utils import human_size


class ZipTool(BaseTool):
    id = "zip_unzip"
    name = "Zip / Unzip"
    category = "file"
    icon = "📦"
    description = "Compress files into a ZIP archive or extract one."
    keywords = ["zip", "unzip", "archive", "compress", "extract", "pack"]

    def __init__(self, app=None):
        super().__init__(app)
        self.entries = []          # (arcname, fullpath, size)

    def build(self, parent):
        lay = ToolLayout(parent)
        self.layout = lay
        holder = lay.row(weight=1)
        self.tv = ctk.CTkTabview(holder, height=360, corner_radius=10)
        self.tv.pack(fill="both", expand=True)
        self.tv.add("Zip")
        self.tv.add("Unzip")
        self._build_zip_tab(self.tv.tab("Zip"))
        self._build_unzip_tab(self.tv.tab("Unzip"))
        self.status = lay.status()

    # ---- Zip tab ----
    def _build_zip_tab(self, tab):
        btns = ctk.CTkFrame(tab, fg_color="transparent")
        btns.pack(fill="x", pady=(0, 8))
        for text, cmd in (("Add files…", self.add_files),
                          ("Add folder…", self.add_folder),
                          ("Clear", self.clear_files)):
            ctk.CTkButton(btns, text=text, width=120, height=32,
                          fg_color="#2f6feb", hover_color="#1e4fbf",
                          command=cmd).pack(side="left", padx=(0, 8))

        self.listbox = ctk.CTkTextbox(tab, height=180, corner_radius=10,
                                      border_width=1, border_color="#2a2a2a",
                                      font=ctk.CTkFont(size=12))
        self.listbox.pack(fill="both", expand=True, pady=(0, 8))
        set_text(self.listbox, "No files queued.")
        self.listbox.configure(state="disabled")

        row = ctk.CTkFrame(tab, fg_color="transparent")
        row.pack(fill="x")
        self.dest_entry = ctk.CTkEntry(
            row, placeholder_text="Output .zip path…", height=34)
        self.dest_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(row, text="Browse…", width=90, height=34,
                      fg_color="#2a2a2a", hover_color="#333333",
                      command=self.browse_dest).pack(side="left", padx=(0, 8))
        ctk.CTkButton(row, text="Create ZIP", width=120, height=34,
                      fg_color="#22c55e", hover_color="#16a34a",
                      command=self.create_zip).pack(side="left")

    def _build_unzip_tab(self, tab):
        r1 = ctk.CTkFrame(tab, fg_color="transparent")
        r1.pack(fill="x", pady=(4, 8))
        self.zip_entry = ctk.CTkEntry(r1, placeholder_text="Archive (.zip)…",
                                      height=34)
        self.zip_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(r1, text="Browse…", width=90, height=34,
                      fg_color="#2a2a2a", hover_color="#333333",
                      command=self.browse_zip).pack(side="left")

        r2 = ctk.CTkFrame(tab, fg_color="transparent")
        r2.pack(fill="x", pady=(0, 8))
        self.out_entry = ctk.CTkEntry(
            r2, placeholder_text="Destination folder…", height=34)
        self.out_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(r2, text="Browse…", width=90, height=34,
                      fg_color="#2a2a2a", hover_color="#333333",
                      command=self.browse_out).pack(side="left")
        ctk.CTkButton(r2, text="Extract", width=110, height=34,
                      fg_color="#22c55e", hover_color="#16a34a",
                      command=self.extract).pack(side="left", padx=(8, 0))

        self.out_box = ctk.CTkTextbox(tab, height=200, corner_radius=10,
                                      border_width=1, border_color="#2a2a2a",
                                      font=ctk.CTkFont(size=12))
        self.out_box.pack(fill="both", expand=True)
        set_text(self.out_box, "Choose an archive to extract.")
        self.out_box.configure(state="disabled")

    # ---- zip actions ----
    def add_files(self):
        paths = filedialog.askopenfilenames(title="Add files")
        for p in paths or ():
            p = str(p)
            self.entries.append((os.path.basename(p), p,
                                 os.path.getsize(p) if os.path.exists(p) else 0))
        self._render_list()

    def add_folder(self):
        folder = filedialog.askdirectory(title="Add folder")
        if not folder:
            return
        base = os.path.dirname(folder)
        count = 0
        for dirpath, dirnames, files in os.walk(folder):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for f in files:
                full = os.path.join(dirpath, f)
                arc = os.path.relpath(full, base).replace(os.sep, "/")
                try:
                    size = os.path.getsize(full)
                except OSError:
                    size = 0
                self.entries.append((arc, full, size))
                count += 1
        self.status.set(f"Added {count} files from {os.path.basename(folder)}",
                        SUCCESS)
        self._render_list()

    def clear_files(self):
        self.entries = []
        self._render_list()

    def _render_list(self):
        if not self.entries:
            text = "No files queued."
        else:
            total = sum(e[2] for e in self.entries)
            lines = [f"{len(self.entries)} file(s) — {human_size(total)}", ""]
            lines += [f"{human_size(size):>10}   {arc}"
                      for arc, _, size in self.entries[:500]]
            if len(self.entries) > 500:
                lines.append(f"… {len(self.entries) - 500} more")
            text = "\n".join(lines)
        set_text(self.listbox, text)

    def browse_dest(self):
        path = filedialog.asksaveasfilename(defaultextension=".zip",
                                            filetypes=[("ZIP", "*.zip")])
        if path:
            self.dest_entry.delete(0, "end")
            self.dest_entry.insert(0, path)

    def create_zip(self):
        if not self.entries:
            self.status.set("Add some files first.", ERROR)
            return
        dest = self.dest_entry.get().strip()
        if not dest:
            self.browse_dest()
            dest = self.dest_entry.get().strip()
        if not dest:
            return
        try:
            with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
                for arc, full, _ in self.entries:
                    if os.path.isfile(full):
                        zf.write(full, arc)
            size = os.path.getsize(dest)
        except Exception as e:
            self.status.set(f"Zip failed: {e}", ERROR)
            return
        self.status.set(
            f"Created {dest}  —  {len(self.entries)} entries, "
            f"{human_size(size)}", SUCCESS)

    # ---- unzip actions ----
    def browse_zip(self):
        path = filedialog.askopenfilename(
            title="Choose archive",
            filetypes=[("ZIP", "*.zip"), ("All files", "*.*")])
        if path:
            self.zip_entry.delete(0, "end")
            self.zip_entry.insert(0, path)

    def browse_out(self):
        path = filedialog.askdirectory(title="Extract to")
        if path:
            self.out_entry.delete(0, "end")
            self.out_entry.insert(0, path)

    def extract(self):
        src = self.zip_entry.get().strip()
        if not src:
            self.status.set("Choose a ZIP file first.", ERROR)
            return
        dest = self.out_entry.get().strip()
        if not dest:
            dest = os.path.splitext(src)[0]
            self.out_entry.insert(0, dest)
        dest = os.path.abspath(dest)
        try:
            with zipfile.ZipFile(src) as zf:
                names = zf.namelist()
                root = os.path.realpath(dest)
                for name in names:
                    target = os.path.realpath(os.path.join(dest, name))
                    if not (target == root or target.startswith(root + os.sep)):
                        raise ValueError(f"unsafe path in archive: {name}")
                zf.extractall(dest)
        except Exception as e:
            self.status.set(f"Extract failed: {e}", ERROR)
            return
        preview = "\n".join(names[:400])
        if len(names) > 400:
            preview += f"\n… {len(names) - 400} more"
        set_text(self.out_box, f"Extracted {len(names)} entries → {dest}\n\n"
                               f"{preview}")
        self.status.set(f"Extracted {len(names)} entries.", SUCCESS)


# --------------------------------------------------------------------------
class BatchRenameTool(BaseTool):
    id = "batch_rename"
    name = "Batch Rename"
    category = "file"
    icon = "✏️"
    description = "Rename hundreds of files at once with a numbering pattern."
    keywords = ["rename", "batch", "files", "bulk", "pattern", "organize"]

    def __init__(self, app=None):
        super().__init__(app)
        self.folder = None
        self._history = []

    def build(self, parent):
        lay = ToolLayout(parent)
        self.layout = lay

        row = lay.row()
        ctk.CTkButton(row, text="Load folder…", width=140, height=34,
                      fg_color="#2f6feb", hover_color="#1e4fbf",
                      command=self.load_folder).pack(side="left")
        self.folder_label = ctk.CTkLabel(row, text="no folder selected",
                                         text_color=MUTED,
                                         font=ctk.CTkFont(size=12))
        self.folder_label.pack(side="left", padx=(14, 0))

        self.filter_entry = lay.entry(
            "File filter (leave empty for all files)",
            placeholder="e.g. *.png  or  IMG_*", default="")

        prow = lay.row()
        ctk.CTkLabel(prow, text="Pattern:", font=ctk.CTkFont(size=12),
                     text_color=MUTED).pack(side="left", padx=(0, 8))
        self.pattern_entry = ctk.CTkEntry(prow, width=260, height=32)
        self.pattern_entry.insert(0, "renamed_{n:03d}")
        self.pattern_entry.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(prow, text="Start #:", font=ctk.CTkFont(size=12),
                     text_color=MUTED).pack(side="left", padx=(0, 8))
        self.start_entry = ctk.CTkEntry(prow, width=70, height=32)
        self.start_entry.insert(0, "1")
        self.start_entry.pack(side="left")

        lay.note("Tokens: {n} number  {n:03d} zero-padded  {stem} old name  "
                 "{ext} extension without dot")

        self.preview_box = lay.box("Preview (old  →  new)", height=190,
                                   readonly=True, weight=1)
        lay.buttons([
            ("Preview", lambda: self.preview()),
            ("Apply rename", self.apply),
            ("Undo last", self.undo),
            ("Copy", lambda: copy_box(self.preview_box, self.status)),
        ])
        self.status = lay.status()

        for w in (self.filter_entry, self.pattern_entry, self.start_entry):
            w.bind("<KeyRelease>", lambda e: self.preview())

    # ---- data ----
    def load_folder(self):
        folder = filedialog.askdirectory(title="Choose folder")
        if not folder:
            return
        self.folder = folder
        self.folder_label.configure(text=folder)
        self.preview()

    def _files(self):
        if not self.folder:
            return []
        pattern = self.filter_entry.get().strip()
        out = []
        for name in sorted(os.listdir(self.folder)):
            full = os.path.join(self.folder, name)
            if not os.path.isfile(full):
                continue
            if pattern and not fnmatch.fnmatch(name.lower(), pattern.lower()):
                continue
            out.append(name)
        return out

    def _plan(self):
        pattern = self.pattern_entry.get().strip() or "{stem}"
        try:
            start = int(self.start_entry.get().strip() or "1")
        except ValueError:
            start = 1
        plan, seen = [], set()
        for i, name in enumerate(self._files()):
            stem, ext = os.path.splitext(name)
            try:
                new_name = pattern.format(n=start + i, stem=stem,
                                          ext=ext.lstrip("."), name=stem)
            except (KeyError, IndexError) as e:
                return None, f"Bad pattern token: {e}"
            if not new_name or new_name in ("." , ".."):
                return None, "Pattern produced an empty name"
            if new_name in seen:
                new_name = f"{start + i}_{new_name}"
            seen.add(new_name)
            if new_name != name and os.path.exists(
                    os.path.join(self.folder, new_name)):
                return None, f"Target already exists: {new_name}"
            plan.append((name, new_name))
        return plan, None

    # ---- actions ----
    def preview(self):
        if not self.folder:
            set_text(self.preview_box, "Load a folder first.")
            return
        plan, err = self._plan()
        if err:
            set_text(self.preview_box, "")
            self.status.set(err, ERROR)
            return
        if not plan:
            set_text(self.preview_box, "No files match the filter.")
            self.status.set("No files match.", WARN)
            return
        changed = sum(1 for a, b in plan if a != b)
        lines = [f"{len(plan)} file(s), {changed} to rename", ""]
        lines += [f"{a}   →   {b}" for a, b in plan[:500]]
        if len(plan) > 500:
            lines.append(f"… {len(plan) - 500} more")
        set_text(self.preview_box, "\n".join(lines))
        self.status.set(f"{changed} file(s) will be renamed.", SUCCESS)

    def apply(self):
        if not self.folder:
            self.status.set("Load a folder first.", ERROR)
            return
        plan, err = self._plan()
        if err:
            self.status.set(err, ERROR)
            return
        done, history = 0, []
        for old, new in plan:
            if old == new:
                continue
            try:
                os.rename(os.path.join(self.folder, old),
                          os.path.join(self.folder, new))
            except OSError as e:
                self.status.set(f"Stopped at {old}: {e}", ERROR)
                break
            history.append((old, new))
            done += 1
        if history:
            self._history = history
        self.status.set(f"Renamed {done} file(s).", SUCCESS)
        self.preview()

    def undo(self):
        if not self._history:
            self.status.set("Nothing to undo.", WARN)
            return
        undone = 0
        for old, new in reversed(self._history):
            src = os.path.join(self.folder, new)
            dst = os.path.join(self.folder, old)
            if os.path.exists(src) and not os.path.exists(dst):
                try:
                    os.rename(src, dst)
                    undone += 1
                except OSError as e:
                    self.status.set(f"Undo failed: {e}", ERROR)
                    return
        self._history = []
        self.status.set(f"Reverted {undone} file(s).", SUCCESS)
        self.preview()
