"""Generate assets/qtools.ico (used as the desktop shortcut icon).

Run automatically by setup.bat:
    .venv\Scripts\python.exe assets\make_icon.py
Safe to run any time; silently skipped if Pillow is unavailable.
"""

import os
import sys

SIZES = [16, 24, 32, 48, 64, 128, 256]


def _font(size):
    from PIL import ImageFont
    fonts = [
        os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts",
                     "segoeuib.ttf"),
        os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts",
                     "arialbd.ttf"),
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in fonts:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _centered_text(draw, xy, text, font, fill):
    try:
        draw.text(xy, text, font=font, fill=fill, anchor="mm")
        return
    except (TypeError, ValueError):
        pass
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    draw.text((xy[0] - (right - left) / 2 - left,
               xy[1] - (bottom - top) / 2 - top),
              text, font=font, fill=fill)


def main():
    try:
        from PIL import Image, ImageDraw
    except Exception as exc:
        print(f"icon skipped (Pillow missing): {exc}")
        return 0

    size = SIZES[-1]
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = 12
    draw.rounded_rectangle([pad, pad, size - pad, size - pad],
                           radius=size // 5, fill=(47, 111, 235, 255))
    draw.rounded_rectangle([pad, pad, size - pad, size - pad],
                           radius=size // 5, outline=(120, 170, 255, 255),
                           width=6)
    _centered_text(draw, (size // 2, size // 2 + 4), "Q",
                   _font(int(size * 0.60)), (255, 255, 255, 255))

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "qtools.ico")
    img.save(out, format="ICO", sizes=[(s, s) for s in SIZES])
    print(f"icon written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
