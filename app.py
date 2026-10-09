"""Q-Tools — a CustomTkinter toolbox with a sidebar, dashboard and tool router."""

import sys

import customtkinter as ctk

from tools import CATEGORIES, discover_tools
from ui.dashboard import Dashboard
from ui.sidebar import Sidebar
from ui.tool_frame import ToolRouter

APP_NAME = "Q-Tools"
APP_VERSION = "2.0.1"


class QToolsApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(f"{APP_NAME}  ·  {APP_VERSION}")
        self.geometry("1280x800")
        self.minsize(1024, 640)

        self.registry = discover_tools()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, CATEGORIES, self.apply_filter)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.dashboard = Dashboard(self.content, self.registry, self.open_tool)
        self.dashboard.grid(row=0, column=0, sticky="nsew")

        self.router = ToolRouter(self.content, self.registry, self.back_to_dashboard)

        self.bind("<Escape>", lambda e: self.back_to_dashboard())
        self.bind("<Control-f>", lambda e: self.sidebar.focus_search())

        self.apply_filter("all", "")
        self.after(150, self.sidebar.focus_search)

    # ---- navigation ----
    def apply_filter(self, category, query):
        self.back_to_dashboard()
        self.dashboard.apply(category, query)

    def open_tool(self, tool_id):
        if self.router.show(tool_id):
            self.dashboard.grid_remove()
            self.router.grid(row=0, column=0, sticky="nsew")

    def back_to_dashboard(self):
        self.router.hide()
        self.router.grid_remove()
        self.dashboard.grid(row=0, column=0, sticky="nsew")


def main():
    app = QToolsApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
