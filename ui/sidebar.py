"""Left sidebar: brand, search box and category filter."""

import customtkinter as ctk

from ui.widgets import ACCENT, ACCENT_HOVER, MUTED


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, categories, on_filter, **kw):
        super().__init__(master, width=248, corner_radius=0,
                         fg_color="#141414", **kw)
        self.on_filter = on_filter
        self.categories = categories
        self.category = categories[0][0]
        self.query = ""
        self._buttons = {}

        self.grid_propagate(False)
        self.grid_rowconfigure(4, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._brand()
        self._search()
        self._category_label()
        self._category_list()
        self._footer()

    # ---- pieces ----
    def _brand(self):
        fr = ctk.CTkFrame(self, fg_color="transparent")
        fr.grid(row=0, column=0, sticky="ew", padx=18, pady=(20, 14))
        ctk.CTkLabel(fr, text="Q-Tools", anchor="w",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(fr, text="everyday utilities, one window",
                     anchor="w", text_color=MUTED,
                     font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(1, 0))

    def _search(self):
        self.search = ctk.CTkEntry(
            self, placeholder_text="🔍  Search tools…", height=36,
            border_width=1, border_color="#2a2a2a", corner_radius=10)
        self.search.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 14))
        self.search.bind("<KeyRelease>", lambda e: self._search_changed())

    def _category_label(self):
        ctk.CTkLabel(self, text="CATEGORIES", anchor="w", text_color="#5f6368",
                     font=ctk.CTkFont(size=11, weight="bold")).grid(
            row=2, column=0, sticky="w", padx=20, pady=(0, 6))

    def _category_list(self):
        fr = ctk.CTkFrame(self, fg_color="transparent")
        fr.grid(row=3, column=0, sticky="new")
        fr.grid_columnconfigure(0, weight=1)
        for i, (key, label) in enumerate(self.categories):
            btn = ctk.CTkButton(
                fr, text=label, anchor="w", height=36, corner_radius=8,
                font=ctk.CTkFont(size=13),
                fg_color="transparent", hover_color="#242424",
                text_color="#cfd3d7",
                command=lambda k=key: self.select_category(k),
            )
            btn.grid(row=i, column=0, sticky="ew", padx=12, pady=1)
            self._buttons[key] = btn
        self._paint()

    def _footer(self):
        fr = ctk.CTkFrame(self, fg_color="transparent")
        fr.grid(row=5, column=0, sticky="ew", padx=16, pady=14)
        self.theme_btn = ctk.CTkButton(
            fr, text="🌙  Dark", height=32, corner_radius=8,
            fg_color="#1f1f1f", hover_color="#2a2a2a", border_width=1,
            border_color="#2f2f2f",
            command=self.toggle_theme,
        )
        self.theme_btn.pack(fill="x")

    # ---- behaviour ----
    def _paint(self):
        for key, btn in self._buttons.items():
            active = key == self.category
            btn.configure(
                fg_color=ACCENT if active else "transparent",
                hover_color=ACCENT_HOVER if active else "#242424",
                text_color="#ffffff" if active else "#cfd3d7",
                font=ctk.CTkFont(size=13,
                                 weight="bold" if active else "normal"),
            )

    def select_category(self, key):
        self.category = key
        self._paint()
        self._emit()

    def _search_changed(self):
        self.query = self.search.get()
        self._emit()

    def _emit(self):
        if self.on_filter:
            self.on_filter(self.category, self.query)

    def toggle_theme(self):
        current = ctk.get_appearance_mode()
        dark = current.lower() != "light"
        ctk.set_appearance_mode("light" if dark else "dark")
        self.theme_btn.configure(text="☀️  Light" if dark else "🌙  Dark")

    def focus_search(self):
        self.search.focus_set()
