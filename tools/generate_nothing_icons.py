#!/usr/bin/env python3
"""
Generate Pure Icon Pack style ("轻雨转绘风格") icons for the 4 Nothing OS ecosystem apps:
  1. nothing_x.webp               -> Nothing X (com.nothing.smartcenter)
  2. nothing_glyph.webp           -> Glyph (com.nothing.glyph)
  3. nothing_essential_space.webp -> Essential Space (com.nothing.ntessentialspace)
  4. nothing_essential_apps.webp  -> Essential Apps (com.nothing.essentialapps)

Style specification derived from Pure Icon Pack 2026 official icons:
  - Canvas: 192x192 px RGBA lossless WebP
  - Circle silhouette: center=(96,96), diameter=174px (bbox 9..183) with exact Pure Icon Pack
    ambient elevation shadow extracted from official 2026 white/amber base templates
  - Palette harmonization:
      White surface : #FAFAFA (250, 250, 250)
      Amber surface : #FFC107 (255, 193, 7)
      Dark ink      : #212121 (33, 33, 33)
      Muted ink 20% : #212121 @ 20% alpha over #FAFAFA
      Red accent    : #F44336 (244, 67, 54)
  - Rasterization: 16x supersampling (3072x3072 -> 192x192 BOX 256-sample exact area AA, zero ringing)
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
NODPI_DIR = ROOT / "app" / "src" / "main" / "res" / "drawable-nodpi"

CANVAS = 192
SS = 16  # 16x16 = 256 subpixel samples per pixel (exact 8-bit coverage, zero Lanczos ringing)
HI = CANVAS * SS  # 3072

# Official Pure Icon Pack Material palette
PURE_WHITE = (250, 250, 250)
PURE_AMBER = (255, 193, 7)
PURE_DARK = (33, 33, 33)
PURE_RED = (244, 67, 54)

TOKEN_RE = re.compile(r"[MmLlHhVvCcAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def svg_arc_to_points(
    x1: float,
    y1: float,
    rx: float,
    ry: float,
    phi_deg: float,
    fa: int,
    fs: int,
    x2: float,
    y2: float,
    steps: int = 96,
) -> list[tuple[float, float]]:
    """W3C SVG 1.1 F.6.5 endpoint-to-center elliptical arc parameterization."""
    if abs(x1 - x2) < 1e-9 and abs(y1 - y2) < 1e-9:
        return []
    rx = abs(rx)
    ry = abs(ry)
    if rx < 1e-9 or ry < 1e-9:
        return [(x2, y2)]

    phi = math.radians(phi_deg % 360.0)
    cos_p, sin_p = math.cos(phi), math.sin(phi)

    dx2 = (x1 - x2) / 2.0
    dy2 = (y1 - y2) / 2.0
    x1p = cos_p * dx2 + sin_p * dy2
    y1p = -sin_p * dx2 + cos_p * dy2

    lam = (x1p * x1p) / (rx * rx) + (y1p * y1p) / (ry * ry)
    if lam > 1.0:
        s = math.sqrt(lam)
        rx *= s
        ry *= s

    rx2, ry2 = rx * rx, ry * ry
    x1p2, y1p2 = x1p * x1p, y1p * y1p
    num = max(0.0, rx2 * ry2 - rx2 * y1p2 - ry2 * x1p2)
    den = rx2 * y1p2 + ry2 * x1p2
    rad = math.sqrt(num / den) if den > 1e-12 else 0.0
    if fa == fs:
        rad = -rad

    cxp = rad * (rx * y1p / ry)
    cyp = rad * (-ry * x1p / rx)

    cx = cos_p * cxp - sin_p * cyp + (x1 + x2) / 2.0
    cy = sin_p * cxp + cos_p * cyp + (y1 + y2) / 2.0

    def vec_angle(ux: float, uy: float, vx: float, vy: float) -> float:
        dot = ux * vx + uy * vy
        mag = math.hypot(ux, uy) * math.hypot(vx, vy)
        c = max(-1.0, min(1.0, dot / mag)) if mag > 1e-12 else 1.0
        ang = math.acos(c)
        return -ang if (ux * vy - uy * vx) < 0 else ang

    ux = (x1p - cxp) / rx
    uy = (y1p - cyp) / ry
    vx = (-x1p - cxp) / rx
    vy = (-y1p - cyp) / ry

    theta1 = vec_angle(1.0, 0.0, ux, uy)
    dtheta = vec_angle(ux, uy, vx, vy)
    if fs == 0 and dtheta > 0:
        dtheta -= 2.0 * math.pi
    elif fs == 1 and dtheta < 0:
        dtheta += 2.0 * math.pi

    pts: list[tuple[float, float]] = []
    n = max(16, int(steps * abs(dtheta) / (math.pi / 2.0)))
    for i in range(1, n + 1):
        t = theta1 + dtheta * (i / n)
        ct, st = math.cos(t), math.sin(t)
        px = cos_p * (rx * ct) - sin_p * (ry * st) + cx
        py = sin_p * (rx * ct) + cos_p * (ry * st) + cy
        pts.append((px, py))
    return pts


def parse_svg_subpaths(path_data: str, bezier_steps: int = 64) -> list[list[tuple[float, float]]]:
    """Parse SVG pathData into closed high-density polygon subpaths."""
    tokens = TOKEN_RE.findall(path_data)
    idx = 0
    cmd = ""
    cx, cy = 0.0, 0.0
    sx, sy = 0.0, 0.0
    subpaths: list[list[tuple[float, float]]] = []
    cur: list[tuple[float, float]] = []

    def next_float() -> float:
        nonlocal idx
        val = float(tokens[idx])
        idx += 1
        return val

    while idx < len(tokens):
        tok = tokens[idx]
        if tok.isalpha():
            cmd = tok
            idx += 1
            if cmd in ("Z", "z"):
                if len(cur) >= 3:
                    subpaths.append(cur)
                cur = []
                cx, cy = sx, sy
                continue

        if cmd == "M":
            cx, cy = next_float(), next_float()
            sx, sy = cx, cy
            if len(cur) >= 3:
                subpaths.append(cur)
            cur = [(cx, cy)]
            cmd = "L"
        elif cmd == "m":
            cx += next_float()
            cy += next_float()
            sx, sy = cx, cy
            if len(cur) >= 3:
                subpaths.append(cur)
            cur = [(cx, cy)]
            cmd = "l"
        elif cmd == "L":
            cx, cy = next_float(), next_float()
            cur.append((cx, cy))
        elif cmd == "l":
            cx += next_float()
            cy += next_float()
            cur.append((cx, cy))
        elif cmd == "H":
            cx = next_float()
            cur.append((cx, cy))
        elif cmd == "h":
            cx += next_float()
            cur.append((cx, cy))
        elif cmd == "V":
            cy = next_float()
            cur.append((cx, cy))
        elif cmd == "v":
            cy += next_float()
            cur.append((cx, cy))
        elif cmd in ("C", "c"):
            rel = cmd == "c"
            x1 = next_float() + (cx if rel else 0.0)
            y1 = next_float() + (cy if rel else 0.0)
            x2 = next_float() + (cx if rel else 0.0)
            y2 = next_float() + (cy if rel else 0.0)
            x3 = next_float() + (cx if rel else 0.0)
            y3 = next_float() + (cy if rel else 0.0)
            x0, y0 = cx, cy
            for step in range(1, bezier_steps + 1):
                t = step / bezier_steps
                mt = 1.0 - t
                px = mt**3 * x0 + 3 * mt**2 * t * x1 + 3 * mt * t**2 * x2 + t**3 * x3
                py = mt**3 * y0 + 3 * mt**2 * t * y1 + 3 * mt * t**2 * y2 + t**3 * y3
                cur.append((px, py))
            cx, cy = x3, y3
        elif cmd in ("A", "a"):
            rel = cmd == "a"
            rx = next_float()
            ry = next_float()
            rot = next_float()
            fa = int(round(next_float()))
            fs = int(round(next_float()))
            x2 = next_float() + (cx if rel else 0.0)
            y2 = next_float() + (cy if rel else 0.0)
            cur.extend(svg_arc_to_points(cx, cy, rx, ry, rot, fa, fs, x2, y2))
            cx, cy = x2, y2
        else:
            raise ValueError(f"Unsupported SVG path command: {cmd}")

    if len(cur) >= 3:
        subpaths.append(cur)
    return subpaths


def transform_subpaths(
    subpaths: list[list[tuple[float, float]]],
    src_cx: float,
    src_cy: float,
    scale_192: float,
) -> list[list[tuple[float, float]]]:
    """Map source coordinates centered at (src_cx, src_cy) onto the 3072x3072 supersampled canvas."""
    dst_c = (CANVAS / 2.0) * SS
    s = scale_192 * SS
    return [[((x - src_cx) * s + dst_c, (y - src_cy) * s + dst_c) for x, y in poly] for poly in subpaths]


def build_base_plate(template_name: str, fill_rgb: tuple[int, int, int]) -> Image.Image:
    """Extract Pure Icon Pack's exact 192x192 circle + ambient shadow plate from an official 2026 icon."""
    base = Image.open(NODPI_DIR / template_name).convert("RGBA")
    px = base.load()
    fill_rgba = (*fill_rgb, 255)
    for y in range(CANVAS):
        for x in range(CANVAS):
            if (x - 96) ** 2 + (y - 96) ** 2 <= 78**2:
                px[x, y] = fill_rgba
    return base


def composite_mask(
    canvas: Image.Image,
    hi_mask: Image.Image,
    rgb: tuple[int, int, int],
    opacity: float = 1.0,
) -> Image.Image:
    """Downsample 3072x3072 coverage mask via exact 16x16 BOX area-averaging and alpha-composite onto 192x192."""
    aa_alpha = hi_mask.resize((CANVAS, CANVAS), resample=Image.Resampling.BOX)
    if opacity < 1.0:
        aa_alpha = aa_alpha.point(lambda a: int(round(a * opacity)))
    layer = Image.new("RGBA", (CANVAS, CANVAS), (*rgb, 0))
    layer.putalpha(aa_alpha)
    return Image.alpha_composite(canvas, layer)


# ==============================================================================
# Exact Official Vector Paths from Nothing OS APKs (Nothing A059 / Android 17)
# ==============================================================================

NOTHING_X_BACK_SLASH = (
    "M287.28,204.75L204.75,287.28A42.64,42.64 90,0 1,144.45 287.28L144.45,287.28"
    "A42.64,42.64 0,0 1,144.45 226.97L226.97,144.45A42.64,42.64 0,0 1,287.28 144.45"
    "L287.28,144.45A42.64,42.64 0,0 1,287.28 204.75z"
)
NOTHING_X_MAIN_SLASH = (
    "M204.2,143.9L286.73,226.42A42.64,42.64 90,0 1,286.73 286.73L286.73,286.73"
    "A42.64,42.64 0,0 1,226.42 286.73L143.9,204.2A42.64,42.64 0,0 1,143.9 143.9"
    "L143.9,143.9A42.64,42.64 90,0 1,204.2 143.9z"
)
NOTHING_X_RED_DOT = "M257.12,257.12m-22.22,-22.22a31.42,31.42 90,1 1,44.44 44.44a31.42,31.42 90,1 1,-44.44 -44.44"

GLYPH_CENTER_RED = (
    "M72.7999,81.0726C72.7999,76.5037 76.5037,72.7999 81.0726,72.7999H100.927"
    "C105.496,72.7999 109.2,76.5037 109.2,81.0726V100.927C109.2,105.496 105.496,109.2 "
    "100.927,109.2H81.0726C76.5037,109.2 72.7999,105.496 72.7999,100.927V81.0726Z"
)
GLYPH_OUTER_DOTS = (
    "M36.4,44.6729C36.4,40.104 40.1038,36.4002 44.6727,36.4002H64.5272C69.0961,36.4002 72.7999,40.104 72.7999,44.6729V64.5275C72.7999,69.0964 69.0961,72.8002 64.5272,72.8002H44.6727C40.1038,72.8002 36.4,69.0964 36.4,64.5275V44.6729Z "
    "M109.2,44.6729C109.2,40.104 112.904,36.4002 117.473,36.4002H137.327C141.896,36.4002 145.6,40.104 145.6,44.6729V64.5275C145.6,69.0964 141.896,72.8002 137.327,72.8002H117.473C112.904,72.8002 109.2,69.0964 109.2,64.5275V44.6729Z "
    "M109.2,117.473C109.2,112.904 112.904,109.2 117.473,109.2H137.327C141.896,109.2 145.6,112.904 145.6,117.473V137.327C145.6,141.896 141.896,145.6 137.327,145.6H117.473C112.904,145.6 109.2,141.896 109.2,137.327V117.473Z "
    "M72.7999,153.873C72.7999,149.304 76.5037,145.6 81.0726,145.6H100.927C105.496,145.6 109.2,149.304 109.2,153.873V173.727C109.2,178.296 105.496,182 100.927,182H81.0726C76.5037,182 72.7999,178.296 72.7999,173.727V153.873Z "
    "M72.7999,8.27273C72.7999,3.70384 76.5037,0 81.0726,0H100.927C105.496,0 109.2,3.70384 109.2,8.27274V28.1273C109.2,32.6962 105.496,36.4 100.927,36.4H81.0726C76.5037,36.4 72.7999,32.6962 72.7999,28.1273V8.27273Z "
    "M145.6,81.0726C145.6,76.5037 149.304,72.7999 153.873,72.7999H173.727C178.296,72.7999 182,76.5037 182,81.0726V100.927C182,105.496 178.296,109.2 173.727,109.2H153.873C149.304,109.2 145.6,105.496 145.6,100.927V81.0726Z "
    "M0,81.0726C0,76.5037 3.70384,72.7999 8.27274,72.7999H28.1273C32.6962,72.7999 36.4,76.5037 36.4,81.0726V100.927C36.4,105.496 32.6962,109.2 28.1273,109.2H8.27274C3.70384,109.2 0,105.496 0,100.927V81.0726Z "
    "M36.4,117.473C36.4,112.904 40.1038,109.2 44.6727,109.2H64.5272C69.0961,109.2 72.7999,112.904 72.7999,117.473V137.327C72.7999,141.896 69.0961,145.6 64.5272,145.6H44.6727C40.1038,145.6 36.4,141.896 36.4,137.327V117.473Z"
)

ESSENTIAL_SPACE_PATH = (
    "M196.44,135.22C208.54,128.23 223.46,128.23 235.57,135.22L276.94,159.1C289.04,166.09 296.5,179.01 296.5,192.99V240.76C296.5,254.74 289.04,267.66 276.94,274.65L235.57,298.53C223.46,305.52 208.54,305.52 196.44,298.53L155.07,274.65C142.96,267.66 135.5,254.74 135.5,240.76V192.99C135.5,179.01 142.96,166.09 155.07,159.1L196.44,135.22Z"
    "M209.48,273.52C209.48,277.57 212.77,280.86 216.82,280.86C220.87,280.86 224.16,277.57 224.16,273.52V253.96C224.16,249.9 220.87,246.62 216.82,246.62C212.77,246.62 209.48,249.9 209.48,253.96V273.52Z"
    "M164.06,238.82C160.55,240.85 159.35,245.34 161.37,248.85C163.4,252.35 167.89,253.56 171.4,251.53L188.34,241.75C191.85,239.72 193.05,235.24 191.03,231.73C189,228.22 184.51,227.01 181,229.04L164.06,238.82Z"
    "M242.62,231.73C240.59,235.23 241.79,239.72 245.3,241.75L262.24,251.53C265.75,253.56 270.24,252.35 272.27,248.85C274.29,245.34 273.09,240.85 269.58,238.82L252.64,229.04C249.13,227.01 244.64,228.22 242.62,231.73Z"
    "M216.3,203.38C208.87,203.38 202.85,209.4 202.85,216.83C202.85,224.26 208.87,230.28 216.3,230.28C223.73,230.28 229.75,224.26 229.75,216.83C229.75,209.4 223.73,203.38 216.3,203.38Z"
    "M161.37,184.82C159.35,188.33 160.55,192.82 164.06,194.84L181,204.63C184.51,206.65 189,205.45 191.02,201.94C193.05,198.43 191.85,193.94 188.34,191.92L171.4,182.13C167.89,180.11 163.4,181.31 161.37,184.82Z"
    "M245.3,191.92C241.79,193.94 240.59,198.43 242.62,201.94C244.64,205.45 249.13,206.65 252.64,204.63L269.58,194.84C273.09,192.82 274.29,188.33 272.27,184.82C270.24,181.31 265.75,180.11 262.24,182.13L245.3,191.92Z"
    "M209.48,179.71C209.48,183.76 212.77,280.86 216.82,187.05Z"
)

# Re-copy exact 8th subpath of Essential Space without typo:
ESSENTIAL_SPACE_PATH = (
    "M196.44,135.22C208.54,128.23 223.46,128.23 235.57,135.22L276.94,159.1C289.04,166.09 296.5,179.01 296.5,192.99V240.76C296.5,254.74 289.04,267.66 276.94,274.65L235.57,298.53C223.46,305.52 208.54,305.52 196.44,298.53L155.07,274.65C142.96,267.66 135.5,254.74 135.5,240.76V192.99C135.5,179.01 142.96,166.09 155.07,159.1L196.44,135.22Z"
    "M209.48,273.52C209.48,277.57 212.77,280.86 216.82,280.86C220.87,280.86 224.16,277.57 224.16,273.52V253.96C224.16,249.9 220.87,246.62 216.82,246.62C212.77,246.62 209.48,249.9 209.48,253.96V273.52Z"
    "M164.06,238.82C160.55,240.85 159.35,245.34 161.37,248.85C163.4,252.35 167.89,253.56 171.4,251.53L188.34,241.75C191.85,239.72 193.05,235.24 191.03,231.73C189,228.22 184.51,227.01 181,229.04L164.06,238.82Z"
    "M242.62,231.73C240.59,235.23 241.79,239.72 245.3,241.75L262.24,251.53C265.75,253.56 270.24,252.35 272.27,248.85C274.29,245.34 273.09,240.85 269.58,238.82L252.64,229.04C249.13,227.01 244.64,228.22 242.62,231.73Z"
    "M216.3,203.38C208.87,203.38 202.85,209.4 202.85,216.83C202.85,224.26 208.87,230.28 216.3,230.28C223.73,230.28 229.75,224.26 229.75,216.83C229.75,209.4 223.73,203.38 216.3,203.38Z"
    "M161.37,184.82C159.35,188.33 160.55,192.82 164.06,194.84L181,204.63C184.51,206.65 189,205.45 191.02,201.94C193.05,198.43 191.85,193.94 188.34,191.92L171.4,182.13C167.89,180.11 163.4,181.31 161.37,184.82Z"
    "M245.3,191.92C241.79,193.94 240.59,198.43 242.62,201.94C244.64,205.45 249.13,206.65 252.64,204.63L269.58,194.84C273.09,192.82 274.29,188.33 272.27,184.82C270.24,181.31 265.75,180.11 262.24,182.13L245.3,191.92Z"
    "M209.48,179.71C209.48,183.76 212.77,187.05 216.82,187.05C220.87,187.05 224.16,183.76 224.16,179.71V160.15C224.16,156.09 220.87,152.81 216.82,152.81C212.77,152.81 209.48,156.09 209.48,160.15V179.71Z"
)

ESSENTIAL_APPS_PATH = (
    "M39.7014 135.757C42.7316 136.997 45.8947 138.123 49.1732 139.141L32.4862 155.799C31.5668 156.717 31.1071 157.176 30.577 157.347C30.1107 157.499 29.6084 157.498 29.1422 157.347C28.6121 157.175 28.1526 156.716 27.2335 155.798L26.053 154.618C25.1353 153.702 24.6764 153.243 24.5045 152.715C24.3533 152.25 24.3534 151.749 24.5048 151.284C24.6768 150.756 25.1359 150.298 26.054 149.381L39.7014 135.757Z"
    "M142.617 45.8967C166.405 55.7241 181.998 72.1478 182 90.7601C182 120.851 141.258 145.245 91 145.245C75.9172 145.245 61.6979 143.03 49.1732 139.141L88.3672 100.038C89.2862 99.1208 89.7457 98.6624 90.2755 98.4906C90.7416 98.3395 91.2436 98.3396 91.7096 98.4907C92.2394 98.6625 92.6988 99.1209 93.6177 100.038L117.336 123.706C118.256 124.623 118.716 125.082 119.246 125.254C119.712 125.405 120.214 125.405 120.68 125.254C121.21 125.081 121.67 124.622 122.589 123.704L123.769 122.525C124.687 121.608 125.146 121.15 125.318 120.621C125.469 120.156 125.469 119.655 125.317 119.19C125.145 118.662 124.686 118.204 123.768 117.287L108.321 101.873C106.333 99.8895 105.339 98.8976 105.271 98.0459C105.213 97.307 105.513 96.5849 106.078 96.1035C106.729 95.5487 108.134 95.5487 110.946 95.5487H132.787C134.087 95.5487 134.737 95.5487 135.233 95.2963C135.67 95.0743 136.025 94.7201 136.247 94.2844C136.5 93.7891 136.5 93.1407 136.5 91.8438V90.1789C136.5 88.8821 136.5 88.2337 136.247 87.7384C136.025 87.3027 135.67 86.9484 135.233 86.7264C134.737 86.4741 134.087 86.4741 132.787 86.4741H110.923C108.111 86.4741 106.706 86.4741 106.055 85.9193C105.49 85.438 105.19 84.7159 105.248 83.977C105.315 83.1254 106.309 82.1335 108.297 80.1497L142.617 45.8967Z"
    "M91 36.2826C106.219 36.2826 120.56 38.5353 133.167 42.49L93.6179 81.9621C92.699 82.8792 92.2395 83.3378 91.7097 83.5096C91.2436 83.6608 90.7415 83.6608 90.2754 83.5097C89.7456 83.3379 89.286 82.8794 88.367 81.9623L64.671 58.3168C63.7515 57.3994 63.2918 56.9406 62.7617 56.7689C62.2955 56.6178 61.7933 56.6179 61.3271 56.7693C60.7971 56.9413 60.3377 57.4003 59.4188 58.3183L58.2384 59.4976C57.3204 60.4146 56.8614 60.8731 56.6896 61.4017C56.5384 61.8667 56.5385 62.3674 56.69 62.8323C56.8622 63.3608 57.3214 63.819 58.2399 64.7355L73.6868 80.1494C75.6749 82.1333 76.6689 83.1252 76.7361 83.9768C76.7943 84.7158 76.4946 85.4379 75.9298 85.9193C75.2788 86.4741 73.873 86.4741 71.0614 86.4741H49.2128C47.9132 86.4741 47.2634 86.4741 46.767 86.7264C46.3304 86.9484 45.9754 87.3027 45.7529 87.7384C45.5 88.2337 45.5 88.8821 45.5 90.1789V91.8438C45.5 93.1407 45.5 93.7891 45.7529 94.2844C45.9754 94.7201 46.3304 95.0743 46.767 95.2963C47.2634 95.5487 47.9132 95.5487 49.2128 95.5487H71.038C73.8499 95.5487 75.2559 95.5487 75.9069 96.1036C76.4717 96.585 76.7714 97.3071 76.7131 98.0461C76.6459 98.8977 75.6516 99.8897 73.6631 101.874L39.7014 135.757C15.734 125.944 0 109.456 0 90.7601C0.00303545 60.6713 40.744 36.2826 91 36.2826Z"
    "M155.931 27.3809C156.849 28.2982 157.308 28.7568 157.48 29.2855C157.631 29.7505 157.631 30.2513 157.479 30.7162C157.307 31.2448 156.848 31.703 155.929 32.6195L142.617 45.8967C139.595 44.6483 136.439 43.5162 133.167 42.49L149.499 26.1998C150.418 25.2826 150.878 24.8241 151.408 24.6524C151.874 24.5014 152.377 24.5016 152.843 24.653C153.373 24.825 153.832 25.284 154.751 26.2018L155.931 27.3809Z"
)


def render_nothing_x(white_plate: Image.Image) -> Image.Image:
    im = white_plate.copy()
    # Source glyph spans ~131.38..299.80 (width 168.42, center 215.59) in 432 viewport.
    # Scale to 78px optical X-mark inside 174px circle -> scale = 78 / 168.42 = 0.4631
    src_c = 215.59
    scale = 78.0 / 168.42

    m_back = Image.new("L", (HI, HI), 0)
    d_back = ImageDraw.Draw(m_back)
    for poly in transform_subpaths(parse_svg_subpaths(NOTHING_X_BACK_SLASH), src_c, src_c, scale):
        d_back.polygon(poly, fill=255)
    im = composite_mask(im, m_back, PURE_DARK, opacity=0.20)

    m_main = Image.new("L", (HI, HI), 0)
    d_main = ImageDraw.Draw(m_main)
    for poly in transform_subpaths(parse_svg_subpaths(NOTHING_X_MAIN_SLASH), src_c, src_c, scale):
        d_main.polygon(poly, fill=255)
    im = composite_mask(im, m_main, PURE_DARK)

    m_red = Image.new("L", (HI, HI), 0)
    d_red = ImageDraw.Draw(m_red)
    for poly in transform_subpaths(parse_svg_subpaths(NOTHING_X_RED_DOT), src_c, src_c, scale):
        d_red.polygon(poly, fill=255)
    im = composite_mask(im, m_red, PURE_RED)
    return im


def render_nothing_glyph(white_plate: Image.Image) -> Image.Image:
    im = white_plate.copy()
    # Source glyph spans 0..182 (center 91.0) in 3x3 diamond matrix.
    # Diamond shape has open corners, so 86px span (matching tiger_trade 86x86) gives balanced weight.
    src_c = 91.0
    scale = 86.0 / 182.0

    m_outer = Image.new("L", (HI, HI), 0)
    d_outer = ImageDraw.Draw(m_outer)
    for poly in transform_subpaths(parse_svg_subpaths(GLYPH_OUTER_DOTS), src_c, src_c, scale):
        d_outer.polygon(poly, fill=255)
    im = composite_mask(im, m_outer, PURE_DARK)

    m_center = Image.new("L", (HI, HI), 0)
    d_center = ImageDraw.Draw(m_center)
    for poly in transform_subpaths(parse_svg_subpaths(GLYPH_CENTER_RED), src_c, src_c, scale):
        d_center.polygon(poly, fill=255)
    im = composite_mask(im, m_center, PURE_RED)
    return im


def render_nothing_essential_space(white_plate: Image.Image) -> Image.Image:
    im = white_plate.copy()
    # Source hexagon spans x=135.5..296.5 (w=161, cx=216.0), y=129.98..303.77 (h=173.79, cy=216.875)
    # Optical height 84px (width 77.8px), matching Pure Icon Pack's obtainium (82x76) & rakuten (77x82).
    subpaths = transform_subpaths(parse_svg_subpaths(ESSENTIAL_SPACE_PATH), 216.0, 216.875, 84.0 / 173.79)

    m_hex = Image.new("L", (HI, HI), 0)
    d_hex = ImageDraw.Draw(m_hex)
    # Subpath 0 is the outer rounded hexagon; subpaths 1..7 are the 6 radial capsule cutouts + center circle
    d_hex.polygon(subpaths[0], fill=255)
    for cutout in subpaths[1:]:
        d_hex.polygon(cutout, fill=0)

    return composite_mask(im, m_hex, PURE_DARK)


def render_nothing_essential_apps(amber_plate: Image.Image) -> Image.Image:
    im = amber_plate.copy()
    # Source emblem spans x=0..182 (cx=91.0), y=24.50..157.50 (h=133.0, cy=91.0)
    # Wide oval emblem: width 100px x height 73.1px gives crisp star strokes with Pure Icon Pack's 37px side margin.
    subpaths = transform_subpaths(parse_svg_subpaths(ESSENTIAL_APPS_PATH), 91.0, 91.0, 100.0 / 182.0)

    m_emblem = Image.new("L", (HI, HI), 0)
    d_emblem = ImageDraw.Draw(m_emblem)
    for poly in subpaths:
        d_emblem.polygon(poly, fill=255)

    return composite_mask(im, m_emblem, PURE_DARK)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", type=Path, help="Optional path to save comparison preview sheet PNG")
    args = ap.parse_args()

    white_plate = build_base_plate("vpoints.webp", PURE_WHITE)
    amber_plate = build_base_plate("tiger_trade.webp", PURE_AMBER)

    icons = {
        "nothing_x": render_nothing_x(white_plate),
        "nothing_glyph": render_nothing_glyph(white_plate),
        "nothing_essential_space": render_nothing_essential_space(white_plate),
        "nothing_essential_apps": render_nothing_essential_apps(amber_plate),
    }

    for name, img in icons.items():
        out_path = NODPI_DIR / f"{name}.webp"
        img.save(out_path, format="WEBP", lossless=True, quality=100, method=6)
        print(f"Saved {out_path.relative_to(ROOT)} ({out_path.stat().st_size} bytes, size={img.size})")

    if args.preview:
        refs = [
            Image.open(NODPI_DIR / "kernelsu.webp").convert("RGBA"),
            Image.open(NODPI_DIR / "rakuten.webp").convert("RGBA"),
            Image.open(NODPI_DIR / "vpoints.webp").convert("RGBA"),
            Image.open(NODPI_DIR / "tiger_trade.webp").convert("RGBA"),
        ]
        new_list = list(icons.values())

        # Row 1: 4 official Pure Icon Pack reference icons on dark bg
        # Row 2: 4 newly redrawn Nothing icons on dark bg (#1C1D21)
        # Row 3: 4 newly redrawn Nothing icons on light bg (#F2F3F7) to inspect #FAFAFA circle & drop shadow!
        cell = 232
        sheet = Image.new("RGBA", (cell * 4, cell * 3), (28, 29, 33, 255))
        light_strip = Image.new("RGBA", (cell * 4, cell), (242, 243, 247, 255))
        sheet.paste(light_strip, (0, cell * 2))

        for c, ref_im in enumerate(refs):
            sheet.alpha_composite(ref_im, (c * cell + 20, 20))
        for c, new_im in enumerate(new_list):
            sheet.alpha_composite(new_im, (c * cell + 20, cell + 20))
            sheet.alpha_composite(new_im, (c * cell + 20, cell * 2 + 20))

        args.preview.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(args.preview)
        print(f"Saved preview sheet to {args.preview}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
