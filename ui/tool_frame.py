"""Tool router: swaps the dashboard for a single tool screen."""

import customtkinter as ctk

from ui.widgets import ERROR, MUTED


class ToolRouter(ctk.CTkFrame):
    def __init__(self, master, registry, on_back, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.registry = registry
        self.on_back = on_back
        self.frames = {}            # tool id -> built widget
        self.current = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_header()
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew")
        self.body.grid_rowconfigure(0, weight=1)
        self.body.grid_columnconfigure(0, weight=1)

    def _build_header(self):
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 4))
        head.grid_columnconfigure(1, weight=1)

        self.back_btn = ctk.CTkButton(
            head, text="←  All tools", width=116, height=34, corner_radius=8,
            fg_color="#1f1f1f", hover_color="#2a2a2a", border_width=1,
            border_color="#2f2f2f",
            command=lambda: self.on_back(),
        )
        self.back_btn.grid(row=0, column=0, rowspan=2, padx=(0, 16))

        self.title_lbl = ctk.CTkLabel(head, text="", anchor="w",
                                      font=ctk.CTkFont(size=20, weight="bold"))
        self.title_lbl.grid(row=0, column=1, sticky="sew")
        self.desc_lbl = ctk.CTkLabel(head, text="", anchor="w",
                                     text_color=MUTED,
                                     font=ctk.CTkFont(size=12))
        self.desc_lbl.grid(row=1, column=1, sticky="new", pady=(2, 0))

        ctk.CTkFrame(self, height=1, fg_color="#2a2a2a").grid(
            row=2, column=0, sticky="ew", padx=20, pady=(12, 0))
        self.grid_rowconfigure(2, minsize=1)

    # ---- public API ----
    def show(self, tool_id):
        tool = self.registry.get(tool_id)
        if tool is None:
            self._show_error(tool_id)
            return False

        frame = self.frames.get(tool_id)
        if frame is None:
            try:
                frame = ctk.CTkFrame(self.body, fg_color="transparent")
                tool.build(frame)
                frame.grid(row=0, column=0, sticky="nsew")
                frame.grid_remove()
                self.frames[tool_id] = frame
            except Exception as e:
                self._show_error(tool_id, e)
                return False

        if self.current and self.current in self.frames:
            self.frames[self.current].grid_remove()
        frame.grid(row=0, column=0, sticky="nsew")
        self.current = tool_id

        self.title_lbl.configure(text=f"{tool.icon}  {tool.name}")
        self.desc_lbl.configure(text=tool.description)
        return True

    def hide(self):
        if self.current and self.current in self.frames:
            self.frames[self.current].grid_remove()
        self.current = None

    def _show_error(self, tool_id, error=None):
        for w in self.body.winfo_children():
            w.destroy()
        self.frames.clear()
        self.current = None
        msg = (f"Tool “{tool_id}” could not be loaded.\n\n{error}"
               if error else f"Unknown tool: {tool_id}")
        ctk.CTkLabel(self.body, text=msg, text_color=ERROR, justify="left",
                     anchor="w", font=ctk.CTkFont(size=14)).grid(
            row=0, column=0, sticky="nw", padx=24, pady=24)
        self.title_lbl.configure(text="⚠  Tool error")
        self.desc_lbl.configure(text="")
