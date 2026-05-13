"""
Generate favicon.ico + apple-touch-icon.png from favicon.svg.
Run once: python _generate_icons.py
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io
import math

ROOT = Path(__file__).resolve().parent
INK = (3, 7, 18, 255)
GRAD_STOPS = [(34, 211, 238), (167, 139, 250), (232, 121, 249)]  # cyan, violet, fuchsia


def draw_logo(size: int) -> Image.Image:
    """Render the gradient-atom logo at given size. Background ink-950, rounded corners."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    radius = int(size * 0.18)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=INK)

    cx, cy = size / 2, size / 2
    icon_scale = size / 64
    sw = max(1, int(3.2 * icon_scale))
    r_atom = 3.5 * icon_scale

    # diagonal gradient: pre-compute color per pixel position
    # for performance, we approximate by drawing strokes in 3 segments with stop colors
    def grad_color(t: float):
        t = max(0.0, min(1.0, t))
        if t <= 0.5:
            a, b, k = GRAD_STOPS[0], GRAD_STOPS[1], t * 2
        else:
            a, b, k = GRAD_STOPS[1], GRAD_STOPS[2], (t - 0.5) * 2
        return (
            int(a[0] + (b[0] - a[0]) * k),
            int(a[1] + (b[1] - a[1]) * k),
            int(a[2] + (b[2] - a[2]) * k),
            255,
        )

    # central circle
    color_center = grad_color(0.5)
    d.ellipse(
        (cx - r_atom, cy - r_atom, cx + r_atom, cy + r_atom),
        outline=color_center,
        width=sw,
    )

    # arms — 8 directional lines, each colored by angle position along diagonal
    arm_len = 8 * icon_scale
    gap = 5.5 * icon_scale
    arms = [
        (0, -1), (0, 1), (-1, 0), (1, 0),
        (-1, -1), (1, 1), (-1, 1), (1, -1),
    ]
    for dx, dy in arms:
        norm = math.hypot(dx, dy)
        ux, uy = dx / norm, dy / norm
        x1 = cx + ux * gap
        y1 = cy + uy * gap
        x2 = cx + ux * (gap + arm_len)
        y2 = cy + uy * (gap + arm_len)
        # gradient position: diagonal from top-left to bottom-right
        t = ((x2 - 0) + (y2 - 0)) / (2 * size)
        col = grad_color(t)
        d.line((x1, y1, x2, y2), fill=col, width=sw)

    return img


def make_apple_touch():
    img = draw_logo(180)
    img.save(ROOT / "apple-touch-icon.png", "PNG")


def make_ico():
    # 16, 32, 48 sizes packed
    icons = [draw_logo(s) for s in (16, 32, 48)]
    icons[0].save(
        ROOT / "favicon.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48)],
        append_images=icons[1:],
    )


if __name__ == "__main__":
    make_apple_touch()
    make_ico()
    print("Generated apple-touch-icon.png and favicon.ico")
