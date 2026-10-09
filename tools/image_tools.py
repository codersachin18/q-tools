"""Image tools: Base64 image, QR generator, resize, EXIF reader, color picker."""

import base64
import colorsys
import io
import re

import customtkinter as ctk
from tkinter import filedialog

from tools import BaseTool
from ui.widgets import (
    ERROR, MUTED, SUCCESS, ToolLayout, copy_box, get_text, set_text,
)

try:
    from PIL import Image
    from PIL.ExifTags import GPSTAGS, TAGS
    PIL_OK = True
except Exception:                                    # pragma: no cover
    PIL_OK = False

try:
    import qrcode
    QR_OK = True
except Exception:                                    # pragma: no cover
    QR_OK = False

IMAGE_TYPES = [
    ("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.webp *.tif *.tiff *.ico"),
    ("All files", "*.*"),
]


class _ImageTool(BaseTool):
    category = "image"
    max_preview = (470, 320)

    def __init__(self, app=None):
        super().__init__(app)
        self.image = None
        self.image_path = None
        self.preview_lbl = None
        self.preview_size = (0, 0)

    def build(self, parent):
        if not PIL_OK:
            fr = ctk.CTkFrame(parent, fg_color="transparent")
            fr.pack(fill="both", expand=True, padx=24, pady=24)
            ctk.CTkLabel(
                fr, text="This tool needs Pillow.\n\npip install pillow",
                text_color=MUTED, font=ctk.CTkFont(size=14),
                justify="left", anchor="w",
            ).pack(anchor="w")
            self.status = None
            return
        lay = ToolLayout(parent)
        self.layout = lay
        self._build(lay)
        self.status = lay.status()

    def _build(self, lay):
        raise NotImplementedError

    # ---- helpers ----
    def _preview(self, lay, hint="No image loaded"):
        holder = lay.row(weight=1)
        holder.grid_columnconfigure(0, weight=1)
        holder.grid_rowconfigure(0, weight=1)
        self.preview_lbl = ctk.CTkLabel(
            holder, text=hint, text_color=MUTED, width=340, height=170,
            fg_color="#1a1a1a", corner_radius=10,
            font=ctk.CTkFont(size=13),
        )
        self.preview_lbl.grid(row=0, column=0)
        return self.preview_lbl

    def _show_preview(self, img, max_size=None):
        if self.preview_lbl is None:
            return
        max_size = max_size or self.max_preview
        disp = img.copy()
        disp.thumbnail(max_size, Image.LANCZOS)
        if disp.mode not in ("RGB", "RGBA"):
            disp = disp.convert("RGBA")
        self.preview_size = disp.size
        ctk_img = ctk.CTkImage(light_image=disp, dark_image=disp,
                               size=disp.size)
        self.preview_lbl.configure(image=ctk_img, text="",
                                   width=disp.size[0], height=disp.size[1])
        self.preview_lbl.image = ctk_img          # keep a reference

    def _pick_image(self):
        path = filedialog.askopenfilename(title="Choose an image",
                                          filetypes=IMAGE_TYPES)
        if not path:
            return None
        try:
            img = Image.open(path)
            img.load()
        except Exception as e:
            if self.status:
                self.status.set(f"Cannot open image: {e}", ERROR)
            return None
        self.image = img
        self.image_path = path
        return img

    def _save_image(self, img, title="Save image"):
        path = filedialog.asksaveasfilename(
            title=title, defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"),
                       ("WebP", "*.webp"), ("All files", "*.*")])
        if not path:
            return None
        try:
            img.save(path)
        except Exception as e:
            self.status.set(f"Save failed: {e}", ERROR)
            return None
        self.status.set(f"Saved: {path}", SUCCESS)
        return path


# --------------------------------------------------------------------------
# 1. Base64 image
# --------------------------------------------------------------------------
class Base64ImageTool(_ImageTool):
    id = "base64_image"
    name = "Base64 Image"
    icon = "🖼"
    description = "Convert an image to a Base64 string and back again."
    keywords = ["base64", "image", "encode", "decode", "data uri", "embed"]

    def _build(self, lay):
        self._preview(lay)
        lay.buttons([
            ("Load image → Base64", self.encode),
            ("Decode → file…", self.decode),
        ])
        self.out = lay.box("Base64 data (paste here to decode)", height=130)
        lay.buttons([("Copy", self.copy), ("Clear", self.clear)])

    def encode(self):
        img = self._pick_image()
        if not img:
            return
        try:
            with open(self.image_path, "rb") as fh:
                blob = fh.read()
        except OSError as e:
            self.status.set(str(e), ERROR)
            return
        data = base64.b64encode(blob).decode()
        set_text(self.out, data)
        self._show_preview(img)
        self.status.set(f"{self.image_path}  →  {len(data):,} base64 chars",
                        SUCCESS)

    def decode(self):
        raw = get_text(self.out).strip()
        if not raw:
            self.status.set("Paste Base64 data first.", ERROR)
            return
        if raw.startswith("data:"):
            raw = raw.split(",", 1)[-1]
        try:
            blob = base64.b64decode(re.sub(r"\s+", "", raw))
            img = Image.open(io.BytesIO(blob))
            img.load()
        except Exception as e:
            self.status.set(f"Decode failed: {e}", ERROR)
            return
        path = self._save_image(img, "Save decoded image")
        if path:
            self.image = img
            self._show_preview(img)

    def copy(self):
        copy_box(self.out, self.status)

    def clear(self):
        set_text(self.out, "")
        self.status.set("Cleared.")


# --------------------------------------------------------------------------
# 2. QR generator
# --------------------------------------------------------------------------
class QrGeneratorTool(_ImageTool):
    id = "qr_generator"
    name = "QR Generator"
    icon = "📱"
    description = "Turn text or a URL into a scannable QR code image."
    keywords = ["qr", "qrcode", "barcode", "scan", "url", "generate"]
    max_preview = (300, 300)

    def __init__(self, app=None):
        super().__init__(app)
        self.qr_image = None

    def _build(self, lay):
        self.text = lay.box("Text or URL", height=80)
        row = lay.row()
        ctk.CTkLabel(row, text="Box size:", font=ctk.CTkFont(size=12),
                     text_color=MUTED).pack(side="left", padx=(0, 8))
        self.size_menu = ctk.CTkOptionMenu(
            row, values=["4", "6", "8", "10", "12"], width=80, height=30,
            fg_color="#2a2a2a", button_color="#2f6feb")
        self.size_menu.set("8")
        self.size_menu.pack(side="left")
        lay.buttons([
            ("Generate", self.generate),
            ("Save PNG…", self.save),
            ("Copy text", lambda: copy_box(self.text, self.status)),
        ])
        self._preview(lay, "Your QR code will appear here")

    def generate(self):
        if not QR_OK:
            self.status.set("qrcode not installed:  pip install qrcode", ERROR)
            return
        data = get_text(self.text).strip()
        if not data:
            self.status.set("Enter some text first.", ERROR)
            return
        try:
            box = int(self.size_menu.get())
            qr = qrcode.QRCode(box_size=box, border=2,
                               error_correction=qrcode.constants.ERROR_CORRECT_M)
            qr.add_data(data)
            qr.make(fit=True)
            buf = io.BytesIO()
            qr.make_image(fill_color="black", back_color="white").save(
                buf, "PNG")
            buf.seek(0)
            self.qr_image = Image.open(buf).convert("RGB")
            self.qr_image.load()
        except Exception as e:
            self.status.set(f"QR failed: {e}", ERROR)
            return
        self._show_preview(self.qr_image, (320, 320))
        self.status.set(f"QR code for {len(data)} chars generated.",
                        SUCCESS)

    def save(self):
        if self.qr_image is None:
            self.status.set("Generate a QR code first.", ERROR)
            return
        self._save_image(self.qr_image, "Save QR code")


# --------------------------------------------------------------------------
# 3. Resize
# --------------------------------------------------------------------------
class ResizeTool(_ImageTool):
    id = "image_resize"
    name = "Resize Image"
    icon = "⤢"
    description = "Scale an image to exact pixel dimensions."
    keywords = ["resize", "scale", "image", "dimensions", "shrink", "enlarge"]

    def _build(self, lay):
        row = lay.row()
        ctk.CTkButton(row, text="Load image…", width=130, height=34,
                      fg_color="#2f6feb", hover_color="#1e4fbf",
                      command=self.load).pack(side="left")
        self.info = ctk.CTkLabel(row, text="no image", text_color=MUTED,
                                 font=ctk.CTkFont(size=12))
        self.info.pack(side="left", padx=(12, 0))

        dims = lay.row()
        ctk.CTkLabel(dims, text="Width:", font=ctk.CTkFont(size=12),
                     text_color=MUTED).pack(side="left", padx=(0, 6))
        self.w_entry = ctk.CTkEntry(dims, width=90, height=32)
        self.w_entry.pack(side="left", padx=(0, 16))
        ctk.CTkLabel(dims, text="Height:", font=ctk.CTkFont(size=12),
                     text_color=MUTED).pack(side="left", padx=(0, 6))
        self.h_entry = ctk.CTkEntry(dims, width=90, height=32)
        self.h_entry.pack(side="left")
        self.w_entry.bind("<KeyRelease>", lambda e: self._sync("w"))
        self.h_entry.bind("<KeyRelease>", lambda e: self._sync("h"))

        self.aspect = lay.checkbox("Keep aspect ratio", default=True)
        self._preview(lay, "Load an image to resize")
        lay.buttons([("Resize & Save As…", self.apply)])

    def load(self):
        img = self._pick_image()
        if not img:
            return
        self._show_preview(img)
        self.info.configure(text=f"original: {img.width} × {img.height} px")
        for entry in (self.w_entry, self.h_entry):
            entry.delete(0, "end")
        self.w_entry.insert(0, str(img.width))
        self.h_entry.insert(0, str(img.height))
        self.status.set(f"Loaded {self.image_path}", SUCCESS)

    def _sync(self, which):
        if self.image is None or not self.aspect.var.get():
            return
        try:
            if which == "w":
                w = int(self.w_entry.get().strip())
                if w <= 0:
                    return
                h = max(1, round(w * self.image.height / self.image.width))
                self.h_entry.delete(0, "end")
                self.h_entry.insert(0, str(h))
            else:
                h = int(self.h_entry.get().strip())
                if h <= 0:
                    return
                w = max(1, round(h * self.image.width / self.image.height))
                self.w_entry.delete(0, "end")
                self.w_entry.insert(0, str(w))
        except ValueError:
            pass

    def apply(self):
        if self.image is None:
            self.status.set("Load an image first.", ERROR)
            return
        try:
            w = int(self.w_entry.get().strip())
            h = int(self.h_entry.get().strip())
            if w < 1 or h < 1:
                raise ValueError("dimensions must be positive")
            if w > 20000 or h > 20000:
                raise ValueError("max dimension is 20000 px")
        except ValueError as e:
            self.status.set(f"Invalid size: {e}", ERROR)
            return
        out = self.image.resize((w, h), Image.LANCZOS)
        if self._save_image(out, "Save resized image"):
            self._show_preview(out)


# --------------------------------------------------------------------------
# 4. EXIF reader
# --------------------------------------------------------------------------
class ExifTool(_ImageTool):
    id = "exif_reader"
    name = "EXIF Reader"
    icon = "📋"
    description = "Read camera, lens, date and GPS metadata from photos."
    keywords = ["exif", "metadata", "camera", "photo", "gps", "info"]
    max_preview = (260, 180)

    def _build(self, lay):
        self._preview(lay, "Load a photo to inspect")
        lay.buttons([("Load image…", self.load),
                     ("Copy", lambda: copy_box(self.out, self.status))])
        self.out = lay.box("Metadata", height=260, readonly=True, weight=1)

    def load(self):
        img = self._pick_image()
        if not img:
            return
        self._show_preview(img, (260, 180))
        lines = [
            f"File      : {self.image_path}",
            f"Format    : {img.format or '?'}   Mode: {img.mode}",
            f"Size      : {img.width} × {img.height} px",
        ]
        try:
            import os
            lines.append(f"Bytes     : {os.path.getsize(self.image_path):,}")
        except OSError:
            pass

        exif = {}
        try:
            exif = dict(img.getexif())
        except Exception:
            exif = {}

        if not exif:
            lines += ["", "No EXIF metadata found."]
        else:
            lines += ["", "EXIF:"]
            for tag_id, value in sorted(exif.items(), key=lambda kv: str(kv[1])):
                name = TAGS.get(tag_id, f"0x{tag_id:04X}")
                if name in ("UserComment", "MakerNote") and value:
                    value = f"<{len(str(value))} bytes>"
                text = str(value).replace("\x00", "").strip()
                if len(text) > 140:
                    text = text[:140] + " …"
                lines.append(f"  {name:<22} {text}")

            try:
                gps = dict(exif.get_ifd(0x8825))
            except Exception:
                gps = {}
            if gps:
                lines.append("")
                lines.append("GPS:")
                for tag_id, value in gps.items():
                    name = GPSTAGS.get(tag_id, str(tag_id))
                    lines.append(f"  {name:<22} {value}")

        for key in ("dpi", "gamma", "compression"):
            if hasattr(img, "info") and key in img.info:
                lines.append(f"  {key:<22} {img.info[key]}")

        set_text(self.out, "\n".join(lines))
        self.status.set("Metadata loaded.", SUCCESS)


# --------------------------------------------------------------------------
# 5. Color picker
# --------------------------------------------------------------------------
class ColorPickerTool(_ImageTool):
    id = "color_picker"
    name = "Color Picker"
    icon = "🎨"
    description = "Click any pixel of an image to get its HEX and RGB value."
    keywords = ["color", "picker", "hex", "rgb", "eyedropper", "palette"]

    def _build(self, lay):
        self.hex = "#000000"
        self.rgb = (0, 0, 0)
        row = lay.row()
        ctk.CTkButton(row, text="Load image…", width=130, height=34,
                      fg_color="#2f6feb", hover_color="#1e4fbf",
                      command=self.load).pack(side="left")
        ctk.CTkLabel(row, text="then click a pixel", text_color=MUTED,
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=(12, 0))

        self._preview(lay, "Load an image, then click a pixel")
        self.preview_lbl.bind("<Button-1>", self._on_click)

        swatch_row = lay.row()
        self.swatch = ctk.CTkLabel(swatch_row, text="", width=64, height=64,
                                   fg_color="#3a3a3a", corner_radius=10)
        self.swatch.pack(side="left", padx=(0, 16))
        self.out = ctk.CTkTextbox(swatch_row, height=80, width=360,
                                  corner_radius=10, border_width=1,
                                  border_color="#2a2a2a")
        self.out.pack(side="left", fill="both", expand=True)
        set_text(self.out, "Pick a color to see its values.")
        self.out.configure(state="disabled")

        lay.buttons([
            ("Copy HEX", lambda: self._copy_value("#" + self.hex.lstrip("#")
                                                  if self.hex else "")),
            ("Copy RGB", lambda: self._copy_value(
                f"rgb({self.rgb[0]}, {self.rgb[1]}, {self.rgb[2]})"
                if self.rgb else "")),
        ])

    def load(self):
        img = self._pick_image()
        if not img:
            return
        self._show_preview(img)
        self.status.set(f"Loaded {img.width} × {img.height} px — click to pick.",
                        SUCCESS)

    def _on_click(self, event):
        if self.image is None or not self.preview_size[0]:
            return
        lw = self.preview_lbl.winfo_width()
        lh = self.preview_lbl.winfo_height()
        ox = (lw - self.preview_size[0]) / 2
        oy = (lh - self.preview_size[1]) / 2
        x = event.x_root - self.preview_lbl.winfo_rootx() - ox
        y = event.y_root - self.preview_lbl.winfo_rooty() - oy
        if x < 0 or y < 0 or x >= self.preview_size[0] or y >= self.preview_size[1]:
            return
        px = min(int(x * self.image.width / self.preview_size[0]),
                 self.image.width - 1)
        py = min(int(y * self.image.height / self.preview_size[1]),
                 self.image.height - 1)
        rgb = self.image.convert("RGB").getpixel((px, py))
        self._set_color(rgb, px, py)

    def _set_color(self, rgb, px=None, py=None):
        self.rgb = rgb
        self.hex = "#{:02x}{:02x}{:02x}".format(*rgb)
        r, g, b = (c / 255 for c in rgb)
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        lines = [
            f"HEX   {self.hex.upper()}",
            f"RGB   {rgb[0]}, {rgb[1]}, {rgb[2]}",
            f"HSL   {round(h * 360)}°, {round(s * 100)}%, {round(v * 100)}%",
        ]
        if px is not None:
            lines.append(f"Pixel ({px}, {py}) of {self.image.width}×"
                         f"{self.image.height}")
        set_text(self.out, "\n".join(lines))
        self.swatch.configure(fg_color=self.hex)
        self.status.set(f"Color {self.hex.upper()}", SUCCESS)

    def _copy_value(self, value):
        if not value:
            self.status.set("Pick a color first.", ERROR)
            return
        from utils import copy_to_clipboard
        ok = copy_to_clipboard(value)
        self.status.set("Copied." if ok else "Clipboard unavailable.",
                        SUCCESS if ok else ERROR)
