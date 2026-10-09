"""Dashboard: searchable grid of tool cards."""

import customtkinter as ctk

from ui.widgets import ACCENT, ACCENT_HOVER, MUTED

CARD_BG = "#1c1c1c"
CARD_BORDER = "#2a2a2a"


class Dashboard(ctk.CTkScrollableFrame):
    def __init__(self, master, registry, on_open, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.registry = registry
        self.on_open = on_open
        self.category = "all"
        self.query = ""
        self._cols = 0
        self.bind("<Configure>", self._on_resize)

    # ---- filtering ----
    def apply(self, category, query):
        self.category = category or "all"
        self.query = (query or "").strip()
        self.render()

    def _tools(self):
        if self.query:
            found = self.registry.search(self.query)
            if self.category != "all":
                found = [t for t in found if t.category == self.category]
            return found
        if self.category == "all":
            return self.registry.all()
        return self.registry.by_category(self.category)

    # ---- rendering ----
    def _on_resize(self, _event=None):
        width = self.winfo_width()
        cols = max(1, min(4, width // 340))
        if cols != self._cols:
            self._cols = cols
            self.render()

    def render(self):
        for w in self.winfo_children():
            w.destroy()
        if not self._cols:
            self._cols = max(1, min(4, self.winfo_width() // 340))

        tools = self._tools()
        self._header(len(tools))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, pady=(4, 20))
        for c in range(self._cols):
            body.grid_columnconfigure(c, weight=1, uniform="card")

        if not tools:
            ctk.CTkLabel(body, text="No tools match your search.",
                         text_color=MUTED, font=ctk.CTkFont(size=14)).grid(
                row=0, column=0, pady=40)
            return

        for i, tool in enumerate(tools):
            card = self._card(body, tool)
            card.grid(row=i // self._cols, column=i % self._cols,
                      sticky="nsew", padx=7, pady=7)

    def _header(self, count):
        names = dict(self.categories_map())
        title = names.get(self.category, "All Tools")
        if self.query:
            title = f"Search: “{self.query}”"
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", pady=(4, 8))
        ctk.CTkLabel(head, text=title, anchor="w",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(
            head,
            text=f"{count} tool{'s' if count != 1 else ''} available",
            anchor="w", text_color=MUTED, font=ctk.CTkFont(size=12),
        ).pack(anchor="w", pady=(2, 0))

    def categories_map(self):
        try:
            from tools import CATEGORIES
            return CATEGORIES
        except Exception:
            return []

    def _card(self, parent, tool):
        open_cmd = lambda tid=tool.id: self.on_open(tid)   # noqa: E731
        card = ctk.CTkFrame(
            parent, corner_radius=12, height=92, border_width=1,
            border_color=CARD_BORDER, fg_color=CARD_BG, cursor="hand2",
        )
        card.grid_columnconfigure(1, weight=1)

        icon = ctk.CTkLabel(card, text=tool.icon, font=ctk.CTkFont(size=26),
                            cursor="hand2")
        icon.grid(row=0, column=0, padx=(16, 4), pady=16, sticky="n")

        text = ctk.CTkFrame(card, fg_color="transparent")
        text.grid(row=0, column=1, sticky="nsew", pady=14)
        text.grid_columnconfigure(0, weight=1)
        title = ctk.CTkLabel(text, text=tool.name, anchor="w",
                             font=ctk.CTkFont(size=15, weight="bold"),
                             cursor="hand2")
        title.grid(row=0, column=0, sticky="ew")
        desc = ctk.CTkLabel(text, text=tool.description, anchor="w",
                            justify="left", wraplength=260, text_color=MUTED,
                            font=ctk.CTkFont(size=12), cursor="hand2")
        desc.grid(row=1, column=0, sticky="ew", pady=(3, 0))

        btn = ctk.CTkButton(
            card, text="Open", width=84, height=32, corner_radius=8,
            fg_color=ACCENT, hover_color=ACCENT_HOVER, command=open_cmd,
        )
        btn.grid(row=0, column=2, padx=(6, 14), pady=16)

        for w in (card, icon, text, title, desc):
            w.bind("<Button-1>", lambda e: open_cmd(), add="+")
        return card
