"""Shared widgets / layout helpers used by every tool screen."""

import customtkinter as ctk

ACCENT = "#2f6feb"
ACCENT_HOVER = "#1e4fbf"
MUTED = "#9aa0a6"
DIM = "#6b7280"
ERROR = "#ef4444"
SUCCESS = "#22c55e"
WARN = "#f59e0b"
CARD = "#232323"
BORDER = "#2a2a2a"
TEXT = "#e5e7eb"


def set_text(box, text):
    try:
        state = str(box.cget("state"))
    except Exception:
        state = "normal"
    try:
        if state == "disabled":
            box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("1.0", "" if text is None else str(text))
        if state == "disabled":
            box.configure(state="disabled")
    except Exception:
        pass


def get_text(box):
    try:
        return box.get("1.0", "end-1c")
    except Exception:
        return ""


def btn_width(text, minimum=90):
    return max(minimum, len(str(text)) * 9 + 34)


def copy_box(box, status):
    """Copy a textbox's contents to the clipboard and report it on `status`."""
    text = get_text(box)
    if not text:
        status.set("Nothing to copy.", WARN)
        return False
    from utils import copy_to_clipboard
    ok = copy_to_clipboard(text)
    status.set("Copied to clipboard." if ok else "Clipboard unavailable.",
               SUCCESS if ok else ERROR)
    return ok


class Status(ctk.CTkLabel):
    """Small muted status line with a set(text, color) helper."""

    def __init__(self, parent, text="Ready.", **kw):
        super().__init__(parent, text=text, text_color=MUTED, anchor="w",
                         font=ctk.CTkFont(size=12), **kw)

    def set(self, text, color=MUTED):
        try:
            self.configure(text=text, text_color=color)
        except Exception:
            pass


class ToolLayout:
    """Simple top-to-bottom grid layout for tool bodies.

    Tools call label()/row()/box()/buttons()/entry() in order and the rows
    stack automatically. Pass weight > 0 to make a row stretch vertically.
    """

    def __init__(self, parent):
        self.root = ctk.CTkFrame(parent, fg_color="transparent")
        self.root.pack(fill="both", expand=True, padx=22, pady=(16, 18))
        self.root.grid_columnconfigure(0, weight=1)
        self._r = 0
        self._status = None

    def _next(self, weight=0):
        r = self._r
        self._r += 1
        if weight:
            self.root.grid_rowconfigure(r, weight=weight)
        return r

    def label(self, text, size=13, color=None, bold=False, pady=(0, 4)):
        r = self._next()
        lbl = ctk.CTkLabel(
            self.root, text=text, anchor="w",
            font=ctk.CTkFont(size=size, weight="bold" if bold else "normal"),
            text_color=color or TEXT,
        )
        lbl.grid(row=r, column=0, sticky="ew", pady=pady)
        return lbl

    def note(self, text, size=12, color=MUTED):
        return self.label(text, size=size, color=color, pady=(0, 6))

    def row(self, weight=0):
        r = self._next(weight)
        fr = ctk.CTkFrame(self.root, fg_color="transparent")
        fr.grid(row=r, column=0, sticky="nsew")
        return fr

    def buttons(self, items, pady=(4, 10), side="left"):
        fr = self.row()
        for text, cmd in items:
            b = ctk.CTkButton(
                fr, text=text, width=btn_width(text), height=34,
                fg_color=ACCENT, hover_color=ACCENT_HOVER, command=cmd,
            )
            b.pack(side=side, padx=(0, 8), pady=2)
        return fr

    def box(self, label=None, height=150, readonly=False, weight=0, font_size=13):
        if label is not None:
            self.label(label, size=12, color=MUTED)
        r = self._next(weight)
        tb = ctk.CTkTextbox(
            self.root, height=height, corner_radius=10, border_width=1,
            border_color=BORDER, font=ctk.CTkFont(size=font_size),
            wrap="word",
        )
        tb.grid(row=r, column=0, sticky="nsew", pady=(0, 8))
        if readonly:
            tb.configure(state="disabled")
        return tb

    def entry(self, label=None, placeholder="", default="", width=None, height=36,
              pady=(0, 8)):
        if label is not None:
            self.label(label, size=12, color=MUTED)
        r = self._next()
        e = ctk.CTkEntry(
            self.root, placeholder_text=placeholder, height=height,
            border_width=1, border_color=BORDER, font=ctk.CTkFont(size=13),
        )
        if width:
            e.configure(width=width)
        e.grid(row=r, column=0, sticky="ew", pady=pady)
        if default:
            e.insert(0, default)
        return e

    def option_menu(self, label, values, default=None, command=None, width=180,
                    pady=(0, 8)):
        if label is not None:
            self.label(label, size=12, color=MUTED)
        r = self._next()
        om = ctk.CTkOptionMenu(
            self.root, values=list(values), width=width, height=34,
            fg_color=BORDER, button_color=ACCENT, button_hover_color=ACCENT_HOVER,
            command=command,
        )
        om.grid(row=r, column=0, sticky="w", pady=pady)
        if default and default in values:
            om.set(default)
        return om

    def checkbox(self, text, default=False, command=None, pady=(0, 8)):
        r = self._next()
        var = ctk.BooleanVar(value=default)
        cb = ctk.CTkCheckBox(
            self.root, text=text, variable=var, onvalue=True, offvalue=False,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, border_color=BORDER,
            command=command,
        )
        cb.grid(row=r, column=0, sticky="w", pady=pady)
        cb.var = var
        return cb

    def status(self, text="Ready."):
        if self._status is None:
            r = self._next()
            self._status = Status(self.root, text=text)
            self._status.grid(row=r, column=0, sticky="ew", pady=(4, 0))
        return self._status

    def clear(self):
        """Remove everything previously packed into this layout."""
        for w in self.root.winfo_children():
            w.destroy()
        self._r = 0
        self._status = None
