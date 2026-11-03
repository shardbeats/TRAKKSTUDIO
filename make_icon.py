"""Regenerate TRAKKSTUDIO icon (option C: 3 layers = 3 tools).

Dark TRAKK rounded square (#151617) + 3 amber layers (#F5A623 family).
Run:  python make_icon.py   -> writes icon.png (256) + icon.ico (multi-size)
"""
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 256
BG = (21, 22, 23, 255)
AMBER_DK = (150, 100, 20, 255)
AMBER = (245, 166, 35, 255)
AMBER_LT = (255, 201, 102, 255)

ROOT = Path(__file__).resolve().parent


def render(size: int = SIZE) -> Image.Image:
    k = size / SIZE
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([8 * k, 8 * k, size - 8 * k, size - 8 * k],
                        radius=52 * k, fill=BG)
    layers = [(AMBER_DK, 62, 158), (AMBER, 96, 132), (AMBER_LT, 130, 106)]
    for col, y, w in layers:
        y, w = y * k, w * k
        x0 = (size - w) / 2
        d.rounded_rectangle([x0, y, x0 + w, y + 34 * k], radius=17 * k,
                            fill=col)
    return img


def main() -> None:
    png = ROOT / "icon.png"
    ico = ROOT / "icon.ico"
    render().save(png)
    render().save(ico, sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                              (64, 64), (128, 128), (256, 256)])
    print(f"wrote {png} + {ico}")


if __name__ == "__main__":
    main()
