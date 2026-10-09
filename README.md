<div align="center">

# 🧰 Q-Tools

### 27 everyday utilities in one clean desktop window

**File finder · App launcher · Encoders · Generators · Converters · Image tools · Network tools**

A fast, offline, dark-themed toolbox built with Python + CustomTkinter.
No ads, no telemetry, no internet required — double-click and work.

![version](https://img.shields.io/badge/version-2.0.1-2f6feb)
![python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![tools](https://img.shields.io/badge/tools-27-22c55e)
![platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

[Features](#-features) • [Screenshots](#-screenshots) • [Install](#-installation) • [Usage](#-usage) • [Add a tool](#-add-your-own-tool)

</div>

---

## 📸 Screenshots

<p align="center">
  <img src="assets/Screenshot%202026-10-09%20174633.png" width="31%" alt="Dashboard – all 27 tools">
  <img src="assets/Screenshot%202026-10-09%20174710.png" width="31%" alt="Category filter – Text & Codec">
  <img src="assets/Screenshot%202026-10-09%20174651.png" width="31%" alt="Single tool screen – Base64 Image">
</p>
<p align="center"><sub>Dashboard · category filter · single tool screen</sub></p>

---

## ✨ Features

**27 tools, 7 categories, all offline.**

| Category | Tools |
| --- | --- |
| 📁 **File & System** | 🔍 **File Finder** – threaded disk search with live results and “open in explorer” · ⚡ **App Launcher** – index installed apps and open one by typing its name · 📦 **Zip / Unzip** – compress folders or extract archives (zip-slip safe) · ✏️ **Batch Rename** – rename hundreds of files with `{n:03d}` patterns, preview + undo |
| 🔤 **Text & Codec** | **Base64** · **URL Encode** · **Hash** (MD5/SHA-1/SHA-256/SHA-512) · **JSON Formatter** · **UUID Generator** · **Password Generator** · **Timestamp** converter · **Regex Tester** · **Word Counter** · **Code Minifier** (HTML/CSS/JS/JSON) · **Markdown → HTML** · **Cron Explainer** · **Encoding Toolbox** (hex, binary, ROT13, unicode, HTML entities) |
| 🖼 **Image** | **Base64 Image** · **QR Generator** · **Resize Image** · **EXIF Reader** · **Color Picker** (click any pixel for HEX/RGB/HSL) |
| 📐 **Converter** | **Unit Converter** – length, mass, temperature, data, time, area, speed |
| 📡 **System** | **System Info** – CPU, RAM, disks, OS · **Ping** – live latency output |
| 🗒 **Misc** | **Quick Notes** – autosaving scratchpad (`Ctrl+S`) · **Clipboard Viewer** – live clipboard watch + history |

**App highlights**

- 🎨 Best-in-class UI — dark/light theme, rounded cards, sidebar + dashboard layout
- 🔎 Instant search across all tools (`Ctrl+F`) with relevance ranking
- 🗂 One-click category filtering — every tool is 2 clicks away
- ⌨️ Keyboard friendly — `Esc` goes back, `Enter` runs, `Ctrl+S` saves
- 📋 Every output has a **Copy** button
- 🧱 Plugin-style architecture — tools auto-register from `tools/`
- 🚀 Fast — tools are built lazily and cached the first time you open them

---

## 🚀 Installation

> **Requirements:** [Python 3.10+](https://www.python.org/downloads/) (3.13 tested) and an internet connection for the first install.
> During Python setup tick **“Add python.exe to PATH”**.

### ⚡ Method 1 — One-click `setup.bat` (recommended)

Get the code onto your Desktop:

```bat
git clone https://github.com/codersachin18/q-tools.git %USERPROFILE%\Desktop\q-tools
cd /d %USERPROFILE%\Desktop\q-tools
```

…or on GitHub click **Code → Download ZIP**, then extract the ZIP to `Desktop\q-tools`.

Then simply **double-click `setup.bat`**. It automatically:

1. finds Python on your PC
2. creates an isolated `.venv`
3. runs `pip install -r requirements.txt`
4. generates the app icon
5. puts a **Q-Tools** shortcut on your **Desktop** and **Start Menu**

Done — double-click the **Q-Tools** desktop icon to launch.

### 🍎🐧 Method 2 — One-click `setup.sh` (macOS / Linux)

Open Terminal and run:

```bash
git clone https://github.com/codersachin18/q-tools.git
cd q-tools
bash setup.sh
```

The setup script creates a `.venv`, installs the requirements, generates the app icon, and adds a **Q-Tools** launcher to your Desktop. On macOS it creates `Q-Tools.app`; on Linux it creates a `.desktop` launcher. Double-click the launcher when setup finishes.

> **Linux:** If setup reports that it cannot create the virtual environment, install `python3-venv` with your distribution's package manager and run `bash setup.sh` again.

### 🖥 Method 3 — Terminal (manual)

```powershell
git clone https://github.com/codersachin18/q-tools.git
cd q-tools

python -m venv .venv
.\.venv\Scripts\Activate.ps1        # CMD: .venv\Scripts\activate.bat

pip install -r requirements.txt
python app.py
```

<details>
<summary><b>Linux / macOS terminal</b></summary>

```bash
git clone https://github.com/codersachin18/q-tools.git
cd q-tools

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python3 app.py
```
</details>

### 📦 Method 4 — Quick launch

Already installed once? On Windows, **double-click `start.bat`**. On macOS/Linux, double-click the Q-Tools Desktop launcher or run `./start.sh` from the project folder.

---

## 🕹 Usage

| Action | How |
| --- | --- |
| Open a tool | Click **Open** on a card (or click the card itself) |
| Back to dashboard | **`Esc`** or the *← All tools* button |
| Search tools | **`Ctrl+F`**, then type |
| Filter by category | Click a category in the sidebar |
| Theme | 🌙/☀️ button at the bottom of the sidebar |
| Notes save | **`Ctrl+S`** |

---

## 📁 Project structure

```
q-tools/
├── app.py               # entry point: sidebar + dashboard + router
├── setup.bat            # one-time installer + desktop shortcut
├── start.bat            # quick launcher
├── setup.sh             # macOS/Linux installer + desktop launcher
├── start.sh             # macOS/Linux quick launcher
├── requirements.txt
├── assets/              # icon + screenshots
├── tools/               # every tool auto-discovered from here
│   ├── __init__.py      # BaseTool + ToolRegistry
│   ├── file_finder.py   ├── text_codec.py   ├── image_tools.py
│   ├── app_launcher.py  ├── file_tools.py   └── converters.py
├── ui/                  # widgets, sidebar, dashboard, router
└── utils/               # shared helpers (clipboard, file ops, sizes)
```

---

## 🧩 Add your own tool

Create `tools/my_tool.py`:

```python
from tools import BaseTool
from ui.widgets import ToolLayout, get_text, set_text

class MyTool(BaseTool):
    id = "my_tool"              # unique id
    name = "My Tool"            # shown on the card
    category = "misc"           # file | text | image | converter | system | misc
    icon = "🛠"
    description = "One line describing what it does."
    keywords = ["my", "keywords"]

    def build(self, parent):
        lay = ToolLayout(parent)
        self.inp = lay.box("Input", height=140, weight=1)
        self.out = lay.box("Output", height=140, readonly=True, weight=1)
        lay.buttons([("Run", self.run), ("Copy", ...)])
        self.status = lay.status()

    def run(self):
        set_text(self.out, get_text(self.inp).upper())
        self.status.set("Done.")
```

Restart the app — the card appears automatically in the dashboard and search.

---

## 📦 Dependencies

| Package | Why |
| --- | --- |
| [`customtkinter`](https://github.com/TomSchimansky/CustomTkinter) | modern themed UI |
| [`pillow`](https://python-pillow.org/) | image preview, resize, EXIF, icon |
| [`qrcode`](https://github.com/lincolnloop/python-qrcode) | QR code generation |
| [`pyperclip`](https://github.com/asweigart/pyperclip) | clipboard copy/paste |

---

## 📝 Changelog

- **2.0.1** — rebranded release: 27 tools, sidebar + dashboard UI, one-click `setup.bat` with desktop shortcut, README
- **1.0.0** — original single-file File Finder & App Launcher
