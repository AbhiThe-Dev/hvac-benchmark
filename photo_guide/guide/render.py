"""Draw the model's targets on the person's own photo. One overview image with every numbered mark, and one image per step with that
step's mark bold and the rest of the photo dimmed. A step with no target gets the plain photo."""
from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from .image import to_jpeg
from .schema import GRID, Guidance, Step, Target

COLOR = (255, 106, 0)          # orange: stands out on grey metal, white walls and dark ceiling spaces
OUTLINE = (255, 255, 255)
INK = (20, 20, 20)
DIM = 0.45


@dataclass
class Rendered:
    overview: bytes
    steps: list[bytes]


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("Helvetica.ttc", "Arial Bold.ttf", "Arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def _px(t: Target, w: int, h: int) -> list[float]:
    return [v / GRID * (w if i % 2 == 0 else h) for i, v in enumerate(t.coords)]


def _badge(d: ImageDraw.ImageDraw, cx: float, cy: float, n: int, r: float, font) -> None:
    d.ellipse([cx - r - 3, cy - r - 3, cx + r + 3, cy + r + 3], fill=OUTLINE)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=COLOR)
    d.text((cx, cy), str(n), fill=(255, 255, 255), font=font, anchor="mm")


def _label(d: ImageDraw.ImageDraw, x: float, y: float, text: str, font, size: tuple[int, int]) -> None:
    if not text:
        return
    l, t, r, b = d.textbbox((0, 0), text, font=font)
    tw, th, pad = r - l, b - t, 6
    x = min(max(x, pad), size[0] - tw - 3 * pad)
    y = min(max(y, pad), size[1] - th - 3 * pad)
    d.rounded_rectangle([x, y, x + tw + 2 * pad, y + th + 2 * pad], radius=6, fill=INK)
    d.text((x + pad - l, y + pad - t), text, fill=(255, 255, 255), font=font)


def _mark(img: Image.Image, i: int, step: Step, bold: bool = True, labels: bool = True) -> None:
    """Draw step i's mark (1-based number i) on img in place. The overview draws numbers only: labels from neighbouring marks collide and clip."""
    if step.target is None:
        return
    w, h = img.size
    u = max(w, h) / 1000.0
    d = ImageDraw.Draw(img)
    f_num, f_lab = _font(max(18, int(38 * u))), _font(max(16, int(36 * u)))
    r_badge = 28 * u
    lw = max(4, int((10 if bold else 7) * u))
    p = _px(step.target, w, h)
    if step.target.kind == "point":
        x, y = p
        rr = 50 * u
        d.ellipse([x - rr - lw, y - rr - lw, x + rr + lw, y + rr + lw], outline=OUTLINE, width=lw + 4)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=COLOR, width=lw)
        bx, by = x - rr * 0.75, y - rr * 0.75
        _badge(d, bx, by, i, r_badge, f_num)
        if labels:
            _label(d, x + rr + 8 * u, y - 14 * u, step.label, f_lab, img.size)
    else:
        x0, y0, x1, y1 = p
        d.rectangle([x0 - 2, y0 - 2, x1 + 2, y1 + 2], outline=OUTLINE, width=lw + 4)
        d.rectangle([x0, y0, x1, y1], outline=COLOR, width=lw)
        _badge(d, x0 + r_badge * 0.4, y0 + r_badge * 0.4, i, r_badge, f_num)
        if labels:
            _label(d, x0 + r_badge * 1.8, y0 + 4 * u, step.label, f_lab, img.size)


def _spotlight(base: Image.Image, t: Target) -> Image.Image:
    """The photo dimmed, with the target region at full brightness."""
    w, h = base.size
    u = max(w, h) / 1000.0
    dim = ImageEnhance.Brightness(base).enhance(DIM)
    mask = Image.new("L", base.size, 0)
    md = ImageDraw.Draw(mask)
    p = _px(t, w, h)
    if t.kind == "point":
        x, y = p
        rr = 100 * u
        md.ellipse([x - rr, y - rr, x + rr, y + rr], fill=255)
    else:
        x0, y0, x1, y1 = p
        m = 8 * u
        md.rectangle([x0 - m, y0 - m, x1 + m, y1 + m], fill=255)
    dim.paste(base, (0, 0), mask)
    return dim


def render_guidance(base: Image.Image, g: Guidance) -> Rendered:
    overview = base.copy()
    for i, s in enumerate(g.steps, 1):
        _mark(overview, i, s, bold=False, labels=False)
    steps = []
    for i, s in enumerate(g.steps, 1):
        if s.target is None:
            steps.append(to_jpeg(base))
            continue
        img = _spotlight(base, s.target)
        _mark(img, i, s)
        steps.append(to_jpeg(img))
    return Rendered(overview=to_jpeg(overview), steps=steps)
