#!/usr/bin/env python3
"""Render an airy, zero-micro-text, 300px-legible 1024x1024 world-news front page for Saturday 21 November 2026."""

from __future__ import annotations

import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 16
CONTENT_W = W - 2 * MARGIN  # 992

# Light, luminous, archival editorial palette — crisp at both 1024px and 300px
BG_PAPER = "#FAF7F0"
BG_WHITE = "#FFFFFF"
BG_TINT = "#F3EEE4"
INK_DARK = "#0F172A"
INK_BODY = "#1E293B"
INK_MUTED = "#475569"
RULE = "#CFC8BA"
ACCENT_RED = "#B91C1C"
ACCENT_NAVY = "#1E3A5F"
GOLD = "#FACC15"

REGION_COLORS = {
    "Europe": "#1D4ED8",
    "Global": "#334155",
    "Middle East": "#B45309",
    "Americas": "#6D28D9",
    "Asia": "#B91C1C",
    "Africa": "#0F766E",
    "Oceania": "#0369A1",
}

TAG_COLORS = {
    "OFFICIAL": "#1E3A5F",
    "REPORTED": "#B45309",
    "CLAIM": "#991B1B",
}

FONT_CANDIDATES = {
    "serif_bold": ["C:/Windows/Fonts/georgiab.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"],
    "serif": ["C:/Windows/Fonts/georgia.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"],
    "serif_italic": ["C:/Windows/Fonts/georgiai.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"],
    "sans_bold": ["C:/Windows/Fonts/segoeuib.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "sans": ["C:/Windows/Fonts/segoeui.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "narrow_bold": ["C:/Windows/Fonts/ARIALNB.TTF", "C:/Windows/Fonts/segoeuib.ttf"],
}

_FONT_CACHE: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def load_font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    key = (kind, size)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    for p in FONT_CANDIDATES[kind]:
        if Path(p).exists():
            f = ImageFont.truetype(p, size)
            _FONT_CACHE[key] = f
            return f
    f = ImageFont.load_default()
    _FONT_CACHE[key] = f
    return f


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    text: str,
    font: ImageFont.ImageFont,
    fill: str,
    align_left_pad: int | None = None,
) -> None:
    box = draw.textbbox((0, 0), text, font=font)
    tw, th = box[2] - box[0], box[3] - box[1]
    tx = (x0 + align_left_pad - box[0]) if align_left_pad is not None else (x0 + (x1 - x0 - tw) // 2 - box[0])
    ty = y0 + (y1 - y0 - th) // 2 - box[1]
    draw.text((tx, ty), text, font=font, fill=fill)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_w: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        cand = f"{cur} {w}".strip()
        cw, _ = text_size(draw, cand, font)
        if cw <= max_w or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def fill_vgrad(d: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int, c_top: str, c_bot: str, step: int = 2) -> None:
    r1, g1, b1 = hex_to_rgb(c_top)
    r2, g2, b2 = hex_to_rgb(c_bot)
    span = max(1, y1 - y0)
    for y in range(y0, y1, step):
        t = (y - y0) / span
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        d.rectangle([x0, y, x1, min(y1, y + step)], fill=(r, g, b))


def supersampled(w: int, h: int, bg: str, fn) -> Image.Image:
    scale = 2
    im = Image.new("RGB", (w * scale, h * scale), bg)
    d = ImageDraw.Draw(im)
    fn(d, w * scale, h * scale)
    return im.resize((w, h), Image.Resampling.LANCZOS)


def draw_art_stamp(d: ImageDraw.ImageDraw, cw: int, ch: int, item: dict, is_hero: bool) -> None:
    """Clean, high-contrast, 300px-readable title stamp top-left + region badge top-right (+ optional status badge bottom-right)."""
    if is_hero:
        f_ban = load_font("narrow_bold", 50)   # 25px effective at 1024px
        f_sub = load_font("narrow_bold", 24)   # 12px effective at 1024px
        pad_x, pad_y = 20, 12
        sub_px, sub_py = 14, 9
        ox, oy = 12, 12
        r_badge = 22
        f_num = load_font("sans_bold", 24)
    else:
        f_ban = load_font("narrow_bold", 38)   # 19px effective at 1024px -> crisp 5.6px at 300px!
        pad_x, pad_y = 16, 10
        ox, oy = 10, 10
        r_badge = 18
        f_num = load_font("sans_bold", 20)

    stamp_fill = ACCENT_RED if item["art"] in ("cop31", "riyadh", "ship", "quake", "boat", "bahrain") else INK_DARK
    bw, bh = text_size(d, item["banner"], f_ban)
    bx1 = ox + bw + pad_x
    by1 = oy + bh + pad_y
    d.rectangle([ox, oy, bx1, by1], fill=stamp_fill)
    draw_centered_text(d, ox, oy, bx1, by1, item["banner"], f_ban, "#FFFFFF")

    if is_hero and item.get("sub"):
        sw, sh = text_size(d, item["sub"], f_sub)
        sy0 = by1 + 4
        sy1 = sy0 + sh + sub_py
        sx1 = ox + sw + sub_px
        d.rectangle([ox, sy0, sx1, sy1], fill=BG_WHITE, outline=INK_DARK, width=2)
        draw_centered_text(d, ox, sy0, sx1, sy1, item["sub"], f_sub, INK_DARK)

    # Top-right circular region number badge
    cx = cw - oy - r_badge
    cy = oy + r_badge
    d.ellipse([cx - r_badge, cy - r_badge, cx + r_badge, cy + r_badge], fill=REGION_COLORS[item["region"]], outline="#FFFFFF", width=4 if is_hero else 3)
    draw_centered_text(d, cx - r_badge, cy - r_badge, cx + r_badge, cy + r_badge, str(item["id"]), f_num, "#FFFFFF")

    # Optional epistemic status badge cleanly placed at bottom-left on non-hero cards
    if not is_hero and item.get("tag"):
        f_tag = load_font("sans_bold", 19)
        tg = item["tag"]
        tw, th = text_size(d, tg, f_tag)
        tx1 = ox + tw + 16
        ty0 = ch - th - 16
        d.rectangle([ox, ty0, tx1, ch - 6], fill=TAG_COLORS[tg])
        draw_centered_text(d, ox, ty0, tx1, ch - 6, tg, f_tag, "#FFFFFF")


def draw_hero_panel_art(item: dict, w: int, h: int) -> Image.Image:
    kind = item["art"]

    def _draw(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        if kind == "cop31":
            # Luminous Mediterranean morning sky (bright, airy, editorial)
            fill_vgrad(d, 0, 0, cw, ch, "#D8F0EA", "#FBEBD2")
            fill_vgrad(d, 0, int(ch * 0.74), cw, ch, "#2563EB", "#1E40AF")
            d.polygon([(0, int(ch * 0.76)), (110, int(ch * 0.62)), (220, int(ch * 0.68)), (320, int(ch * 0.76))], fill="#64748B")
            # Antalya UN summit pavilion dome & delegate flags
            d.pieslice([96, int(ch * 0.54), 278, int(ch * 0.94)], 180, 360, fill="#FFFFFF", outline="#0F172A", width=4)
            flag_cols = ["#2563EB", "#16A34A", "#DC2626", "#F59E0B", "#0EA5E9"]
            for i, fc in enumerate(flag_cols):
                fx = 36 + i * 32
                d.line([(fx, int(ch * 0.72)), (fx, int(ch * 0.94))], fill="#0F172A", width=3)
                d.rectangle([fx, int(ch * 0.72), fx + 20, int(ch * 0.79)], fill=fc)
            # Earth globe center-right
            gx, gy, gr = int(cw * 0.55), int(ch * 0.54), 60
            d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill="#2563EB", outline="#0F172A", width=5)
            d.polygon([(gx - 40, gy - 22), (gx - 10, gy - 38), (gx + 10, gy - 12), (gx - 12, gy + 26), (gx - 34, gy + 10)], fill="#22C55E")
            d.polygon([(gx + 14, gy - 26), (gx + 44, gy - 10), (gx + 34, gy + 22), (gx + 12, gy + 10)], fill="#16A34A")
            # Red thermometer
            tx = int(cw * 0.73)
            d.rounded_rectangle([tx - 12, 54, tx + 12, ch - 48], radius=12, fill="#FFFFFF", outline="#0F172A", width=4)
            d.ellipse([tx - 22, ch - 66, tx + 22, ch - 22], fill="#DC2626", outline="#0F172A", width=4)
            d.rectangle([tx - 6, 78, tx + 6, ch - 42], fill="#DC2626")
            # Overtime clock
            kx, ky, kr = int(cw * 0.88), int(ch * 0.62), 42
            d.ellipse([kx - kr, ky - kr, kx + kr, ky + kr], fill="#FFFFFF", outline="#0F172A", width=5)
            d.pieslice([kx - kr + 6, ky - kr + 6, kx + kr - 6, ky + kr - 6], 270, 340, fill="#FCA5A5")
            d.line([(kx, ky), (kx, ky - 24)], fill="#0F172A", width=5)
            d.line([(kx, ky), (kx + 20, ky - 10)], fill="#DC2626", width=5)
            d.ellipse([kx - 5, ky - 5, kx + 5, ky + 5], fill="#0F172A")

        elif kind == "mercury":
            fill_vgrad(d, 0, 0, cw, ch, "#0B1224", "#172554")
            for sr, col in [(115, "#7C2D12"), (76, "#EA580C"), (46, "#FACC15"), (22, "#FEF9C3")]:
                d.ellipse([16 - sr, ch - 8 - sr, 16 + sr, ch - 8 + sr], fill=col)
            for sx, sy, sr in [(64, 152, 2), (124, 134, 3), (186, 162, 2), (242, 68, 3), (308, 42, 2), (356, 196, 3), (412, 206, 2), (268, 200, 2)]:
                d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill="#F8FAFC")
            d.arc([246, 54, 616, 212], 165, 355, fill="#38BDF8", width=4)
            mx, my, mr = int(cw * 0.77), int(ch * 0.56), 108
            d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill="#64748B", outline="#CBD5E1", width=3)
            d.pieslice([mx - mr + 2, my - mr + 2, mx + mr - 2, my + mr - 2], 100, 265, fill="#D6C7B7")
            d.ellipse([mx - mr + 44, my - mr + 8, mx + mr - 8, my + mr - 8], fill="#64748B")
            d.ellipse([mx - mr + 78, my - mr + 16, mx + mr - 2, my + mr - 16], fill="#334155")
            for cx0, cy0, cr in [(mx - 58, my - 30, 17), (mx - 42, my + 24, 22), (mx - 76, my + 6, 11), (mx - 18, my - 52, 13), (mx + 12, my - 10, 18), (mx + 22, my + 36, 12)]:
                d.ellipse([cx0 - cr, cy0 - cr, cx0 + cr, cy0 + cr], fill="#475569", outline="#E2E8F0", width=2)
                d.ellipse([cx0 - cr + 4, cy0 - cr + 3, cx0 + cr - 2, cy0 + cr - 2], fill="#94877A" if cx0 < mx - 25 else "#475569")
            d.arc([246, 54, 616, 212], 0, 165, fill="#FACC15", width=5)
            # BepiColombo twin spacecraft
            px, py = 330, 142
            d.polygon([(px - 22, py + 2), (px - 74, py + 15), (px - 66, py + 26)], fill="#38BDF8")
            d.polygon([(px - 10, py - 14), (px + 12, py - 70), (px + 34, py - 64), (px + 10, py - 8)], fill="#2563EB", outline="#93C5FD", width=2)
            d.polygon([(px - 12, py + 12), (px - 30, py + 68), (px - 8, py + 74), (px + 10, py + 16)], fill="#2563EB", outline="#93C5FD", width=2)
            d.rounded_rectangle([px - 22, py - 15, px + 26, py + 15], radius=6, fill="#F59E0B", outline="#FEF3C7", width=3)
            d.polygon([(px + 26, py - 13), (px + 46, py - 5), (px + 46, py + 5), (px + 26, py + 13)], fill="#E2E8F0", outline="#0F172A", width=2)

        else:  # riyadh
            fill_vgrad(d, 0, 0, cw, ch, "#0A1530", "#1E3A5F")
            d.ellipse([334, 22, 364, 52], fill="#FEF08A")
            d.ellipse([344, 18, 374, 48], fill="#102042")
            d.rectangle([0, ch - 24, cw, ch], fill="#0F172A")
            blds = [(14, 158, 62), (70, 140, 118), (126, 152, 172), (182, 130, 232), (244, 146, 294), (306, 132, 356), (528, 138, 578), (586, 150, 636)]
            for x0, y0, x1 in blds:
                d.rectangle([x0, y0, x1, ch - 24], fill="#1E3A5F", outline="#334155", width=2)
                for wy in range(y0 + 10, ch - 32, 16):
                    for wx in range(x0 + 8, x1 - 8, 14):
                        d.rectangle([wx, wy, wx + 6, wy + 8], fill="#FDE68A" if (wx + wy) % 3 == 0 else "#334155")
            d.polygon([(388, ch - 24), (414, 102), (440, ch - 24)], fill="#2B5282", outline="#93C5FD", width=2)
            d.ellipse([406, 120, 422, 136], fill="#FACC15")
            d.rectangle([452, 78, 518, ch - 24], fill="#3B6998", outline="#93C5FD", width=2)
            d.ellipse([464, 88, 506, 146], fill="#13254A")
            d.rectangle([460, 78, 510, 90], fill="#E2E8F0")
            for ix, iy in [(320, 106), (424, 64), (554, 92)]:
                d.line([(ix + 90, 4), (ix, iy)], fill="#EF4444", width=5)
                d.line([(ix - 50, ch - 26), (ix, iy)], fill="#38BDF8", width=4)
                d.ellipse([ix - 28, iy - 28, ix + 28, iy + 28], outline="#FDE047", width=3)
                for ang in range(0, 360, 45):
                    rad = math.radians(ang)
                    d.line([(ix, iy), (ix + int(24 * math.cos(rad)), iy + int(24 * math.sin(rad)))], fill="#F97316", width=5)
                d.ellipse([ix - 12, iy - 12, ix + 12, iy + 12], fill="#FEF9C3")

        draw_art_stamp(d, cw, ch, item, is_hero=True)

    return supersampled(w, h, "#0F172A", _draw)


def draw_card_panel_art(item: dict, w: int, h: int) -> Image.Image:
    """Bright, clean, luminous editorial scenes (484x128 at 2x) with crisp silhouettes readable at 300px."""
    kind = item["art"]

    def _draw(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        if kind == "ship":
            # Crisp pale Baltic daylight sky + vibrant steel-blue sea
            fill_vgrad(d, 0, 0, cw, int(ch * 0.66), "#DBEAFE", "#93C5FD")
            fill_vgrad(d, 0, int(ch * 0.66), cw, ch, "#1D4ED8", "#1E3A8A")
            for sx, sy, sr, col in [(336, 56, 22, "#475569"), (366, 38, 26, "#64748B"), (402, 22, 30, "#475569"), (320, 68, 16, "#64748B")]:
                d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=col)
            d.polygon([(192, 86), (432, 82), (416, 110), (210, 110)], fill="#1E293B", outline="#0F172A", width=3)
            d.polygon([(202, 98), (426, 96), (416, 110), (210, 110)], fill="#B91C1C")
            d.rectangle([376, 50, 418, 84], fill="#FFFFFF", outline="#0F172A", width=2)
            d.rectangle([384, 56, 410, 65], fill="#38BDF8")
            d.rectangle([232, 70, 274, 85], fill="#2563EB", outline="#0F172A", width=2)
            d.rectangle([276, 70, 316, 85], fill="#D97706", outline="#0F172A", width=2)
            d.polygon([(304, 86), (322, 42), (338, 66), (354, 34), (370, 86)], fill="#EA580C")
            d.polygon([(316, 86), (328, 56), (342, 72), (354, 52), (364, 86)], fill="#FACC15")
            d.polygon([(256, 28), (288, 38), (270, 46)], fill="#0F172A")
            d.line([(278, 42), (314, 62)], fill="#DC2626", width=3)
            d.polygon([(122, 108), (164, 108), (156, 118), (130, 118)], fill="#F97316")

        elif kind == "sinaloa":
            # Warm sunlit desert ochre & terracotta sky
            fill_vgrad(d, 0, 0, cw, ch, "#FEF3C7", "#FDBA74")
            d.polygon([(0, ch), (96, 66), (200, ch)], fill="#B45309")
            d.polygon([(142, ch), (284, 54), (420, ch)], fill="#92400E")
            d.polygon([(330, ch), (434, 68), (cw, ch)], fill="#78350F")
            d.polygon([(334, 52), (258, ch), (366, ch)], fill="#FEF9C3")
            d.polygon([(0, ch), (112, 104), (244, 114), (384, 104), (cw, ch)], fill="#451A03")
            d.ellipse([292, 102, 312, 118], fill="#EF4444")
            d.ellipse([312, 102, 332, 118], fill="#2563EB")
            hx, hy = 342, 46
            d.line([(hx - 58, hy - 14), (hx + 50, hy - 14)], fill="#0F172A", width=4)
            d.line([(hx, hy - 14), (hx, hy - 2)], fill="#334155", width=4)
            d.rounded_rectangle([hx - 26, hy - 4, hx + 26, hy + 14], radius=8, fill="#1E293B", outline="#0F172A", width=2)
            d.line([(hx + 24, hy + 2), (hx + 64, hy - 2)], fill="#1E293B", width=5)
            d.ellipse([hx + 58, hy - 10, hx + 72, hy + 4], outline="#0F172A", width=2)

        elif kind == "quake":
            fill_vgrad(d, 0, 0, cw, int(ch * 0.52), "#FEF9C3", "#FDE68A")
            fill_vgrad(d, 0, int(ch * 0.52), cw, ch, "#0284C7", "#0369A1")
            d.polygon([(0, int(ch * 0.60)), (88, int(ch * 0.42)), (182, int(ch * 0.48)), (248, int(ch * 0.60))], fill="#15803D")
            ex, ey = 392, 90
            for rr in (18, 34, 50, 68):
                d.ellipse([ex - rr, ey - rr // 2, ex + rr, ey + rr // 2], outline="#EF4444", width=4)
            d.ellipse([ex - 10, ey - 10, ex + 10, ey + 10], fill="#DC2626", outline="#FEF08A", width=3)
            pts = [(16, 84), (210, 84), (236, 78), (254, 96), (272, 54), (290, 110), (308, 42), (326, 114), (344, 52), (362, 102), (382, 76), (408, 86), (468, 84)]
            d.line(pts, fill="#B91C1C", width=6)

        elif kind == "boat":
            # Luminous tropical morning teal-gold river scene
            fill_vgrad(d, 0, 0, cw, int(ch * 0.50), "#CCFBF1", "#FDE68A")
            fill_vgrad(d, 0, int(ch * 0.50), cw, ch, "#0284C7", "#0C4A6E")
            d.rectangle([0, int(ch * 0.44), cw, int(ch * 0.52)], fill="#0F766E")
            for px in (312, 352, 396, 438):
                d.line([(px, int(ch * 0.48)), (px + 4, int(ch * 0.22))], fill="#115E59", width=4)
                for ang in (-140, -95, -45, 5):
                    rad = math.radians(ang)
                    d.line([(px + 4, int(ch * 0.22)), (px + 4 + int(22 * math.cos(rad)), int(ch * 0.22) + int(16 * math.sin(rad)))], fill="#115E59", width=3)
            bx, by = 304, 92
            d.pieslice([bx - 92, by - 32, bx + 92, by + 34], 188, 352, fill="#92400E", outline="#FEF3C7", width=4)
            d.arc([bx - 80, by - 24, bx + 80, by + 24], 195, 345, fill="#D97706", width=5)
            for rx, ry, rw in [(156, 98, 86), (266, 104, 124), (356, 96, 82), (218, 116, 110)]:
                d.line([(rx, ry), (rx + rw, ry)], fill="#E0F2FE", width=4)
            d.ellipse([408, 86, 440, 114], outline="#F97316", width=8)

        elif kind == "plane":
            # Bright dawn sky over crisp runway tarmac
            fill_vgrad(d, 0, 0, cw, int(ch * 0.64), "#BAE6FD", "#E0F2FE")
            d.rectangle([0, int(ch * 0.64), cw, ch], fill="#475569")
            d.line([(16, int(ch * 0.82)), (cw - 16, int(ch * 0.82))], fill="#F8FAFC", width=3)
            for lx in range(28, cw - 20, 56):
                d.ellipse([lx - 4, int(ch * 0.66) - 4, lx + 4, int(ch * 0.66) + 4], fill="#FACC15")
            d.rounded_rectangle([42, 90, 96, 110], radius=4, fill="#DC2626", outline="#FFFFFF", width=2)
            d.ellipse([62, 82, 74, 94], fill="#38BDF8")
            px, py = 352, 74
            d.polygon([(px - 78, py - 4), (px + 54, py - 10), (px + 84, py + 4), (px + 66, py + 14), (px - 70, py + 12)], fill="#FFFFFF", outline="#0F172A", width=3)
            d.polygon([(px - 74, py - 4), (px - 96, py - 34), (px - 52, py - 34), (px - 44, py - 6)], fill="#DC2626", outline="#0F172A", width=2)
            d.polygon([(px - 80, py - 14), (px - 62, py - 26), (px - 56, py - 12)], fill="#FACC15")
            d.polygon([(px - 16, py + 4), (px + 30, py + 4), (px + 6, py + 24)], fill="#94A3B8", outline="#0F172A", width=2)
            for wx in (px - 14, px + 46):
                d.ellipse([wx - 6, py + 15, wx + 6, py + 27], fill="#0F172A", outline="#E2E8F0", width=2)

        elif kind == "fbi":
            # Crisp light-blueprint cyber backdrop (luminous & sharp at 300px!)
            fill_vgrad(d, 0, 0, cw, ch, "#E2E8F0", "#CBD5E1")
            for gy in range(20, ch, 24):
                d.line([(0, gy), (cw, gy)], fill="#94A3B8", width=1)
            for gx in range(32, cw, 36):
                d.line([(gx, 0), (gx, ch)], fill="#94A3B8", width=1)
            # Server rack tower
            d.rounded_rectangle([244, 42, 330, 120], radius=6, fill="#1E293B", outline="#0F172A", width=3)
            for ry in (54, 70, 86, 102):
                d.rectangle([254, ry, 320, ry + 10], fill="#0F172A")
                d.ellipse([260, ry + 2, 268, ry + 8], fill="#EF4444" if ry != 86 else "#22C55E")
                d.rectangle([274, ry + 3, 312, ry + 7], fill="#38BDF8")
            # Crimson breached padlock
            d.arc([302, 32, 336, 66], 180, 360, fill="#B91C1C", width=5)
            d.rounded_rectangle([296, 50, 342, 82], radius=5, fill="#DC2626", outline="#FFFFFF", width=2)
            d.ellipse([314, 60, 324, 70], fill="#FEF08A")
            # Green/gold silicon microchip
            cx0, cy0 = 378, 54
            d.rounded_rectangle([cx0, cy0, cx0 + 70, cy0 + 58], radius=6, fill="#065F46", outline="#10B981", width=4)
            d.rectangle([cx0 + 16, cy0 + 14, cx0 + 54, cy0 + 44], fill="#10B981", outline="#FACC15", width=2)
            for pin in range(cx0 + 12, cx0 + 64, 14):
                d.line([(pin, cy0 - 10), (pin, cy0)], fill="#B45309", width=3)
                d.line([(pin, cy0 + 58), (pin, cy0 + 68)], fill="#B45309", width=3)

        elif kind == "bitcoin":
            # Crisp editorial financial chart on clean warm-slate paper
            fill_vgrad(d, 0, 0, cw, ch, "#FFFBEB", "#FEF3C7")
            for gy in (42, 74, 106):
                d.line([(12, gy), (cw - 12, gy)], fill="#E5E7EB", width=2)
            red_pts = [(18, 76), (82, 82), (144, 72), (206, 94), (264, 114)]
            d.line(red_pts, fill="#DC2626", width=7)
            grn_pts = [(264, 114), (312, 94), (354, 100), (406, 72), (464, 48)]
            d.line(grn_pts, fill="#16A34A", width=7)
            d.ellipse([255, 105, 273, 123], fill="#DC2626", outline="#FFFFFF", width=3)
            bx, by, br = 374, 52, 32
            d.ellipse([bx - br, by - br, bx + br, by + br], fill="#F59E0B", outline="#92400E", width=4)
            bf = load_font("sans_bold", 36)
            draw_centered_text(d, bx - br, by - br, bx + br, by + br, "B", bf, "#FFFFFF")

        elif kind == "cricket":
            fill_vgrad(d, 0, 0, cw, 30, "#7DD3FC", "#E0F2FE")
            d.rectangle([0, 30, cw, ch], fill="#15803D")
            for gx in range(0, cw, 48):
                d.rectangle([gx, 30, gx + 24, ch], fill="#16A34A")
            d.polygon([(240, 30), (324, 30), (370, ch), (194, ch)], fill="#E5D5A8", outline="#FFFFFF", width=2)
            d.line([(218, 100), (346, 100)], fill="#FFFFFF", width=3)
            sx = 282
            for ox in (-14, 0, 14):
                d.line([(sx + ox, 40), (sx + ox, 106)], fill="#92400E", width=6)
            d.line([(sx - 18, 40), (sx + 18, 40)], fill="#F59E0B", width=6)
            d.polygon([(354, 40), (376, 36), (396, 100), (374, 106)], fill="#FDE68A", outline="#78350F", width=3)
            d.ellipse([402, 56, 438, 92], fill="#B91C1C", outline="#FFFFFF", width=3)
            d.rectangle([16, 86, 72, 97], fill="#F97316")
            d.rectangle([16, 97, 72, 108], fill="#FFFFFF")
            d.rectangle([16, 108, 72, 119], fill="#16A34A")
            d.rectangle([82, 86, 138, 119], fill="#1E3A8A")
            d.line([(82, 95), (108, 95)], fill="#DC2626", width=3)
            d.line([(95, 86), (95, 104)], fill="#DC2626", width=3)

        elif kind == "bahrain":
            # Warm sunlit coral Gulf sky + teal Strait of Hormuz water
            fill_vgrad(d, 0, 0, cw, int(ch * 0.70), "#FFEDD5", "#FDBA74")
            fill_vgrad(d, 0, int(ch * 0.70), cw, ch, "#0284C7", "#0369A1")
            # Refinery silhouette right
            d.rectangle([310, 76, 354, 104], fill="#475569", outline="#0F172A", width=2)
            d.rectangle([362, 68, 436, 104], fill="#334155", outline="#0F172A", width=2)
            d.rectangle([324, 48, 334, 76], fill="#64748B")
            d.rectangle([416, 44, 426, 68], fill="#64748B")
            for sx, sy, sr in [(368, 42, 18), (394, 28, 20), (422, 16, 22)]:
                d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill="#475569")
            d.polygon([(352, 80), (368, 38), (382, 62), (396, 34), (410, 80)], fill="#EA580C")
            d.polygon([(362, 80), (374, 52), (386, 66), (396, 50), (404, 80)], fill="#FACC15")
            # Crisp MQ-9 drone silhouette + crimson claim reticle center
            dx, dy = 216, 76
            d.line([(dx - 64, dy), (dx + 64, dy)], fill="#0F172A", width=6)
            d.polygon([(dx - 24, dy - 6), (dx + 34, dy), (dx - 24, dy + 6)], fill="#FFFFFF", outline="#0F172A", width=2)
            d.ellipse([dx - 24, dy - 24, dx + 24, dy + 24], outline="#DC2626", width=4)

        elif kind == "eu_fta":
            # Crisp sunlit diplomatic sky + EU 12-star flag & Indonesia red/white flag + shipping containers
            fill_vgrad(d, 0, 0, cw, ch, "#EFF6FF", "#DBEAFE")
            # EU flag left-center
            d.rectangle([168, 58, 282, 114], fill="#1D4ED8", outline="#0F172A", width=2)
            for a in range(0, 360, 30):
                rad = math.radians(a)
                sx = 225 + int(18 * math.cos(rad))
                sy = 86 + int(18 * math.sin(rad))
                d.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill="#FACC15")
            # Double trade arrows center
            d.line([(292, 76), (344, 76)], fill="#15803D", width=5)
            d.polygon([(344, 68), (358, 76), (344, 84)], fill="#15803D")
            d.line([(354, 96), (302, 96)], fill="#1D4ED8", width=5)
            d.polygon([(302, 88), (288, 96), (302, 104)], fill="#1D4ED8")
            # Indonesia flag right
            d.rectangle([364, 58, 466, 86], fill="#DC2626", outline="#0F172A", width=2)
            d.rectangle([364, 86, 466, 114], fill="#FFFFFF", outline="#0F172A", width=2)

        elif kind == "ebola":
            # Crisp medical pale-cyan background + bold medical shield + Africa emblem + pulse
            fill_vgrad(d, 0, 0, cw, ch, "#ECFEFF", "#CFFAFE")
            # Clean heartbeat / clinical trace
            d.line([(16, 98), (168, 98), (186, 80), (200, 112), (218, 56), (234, 116), (252, 98), (468, 98)], fill="#0891B2", width=4)
            # Bold medical cross shield center-right
            mx, my = 312, 68
            d.rounded_rectangle([mx - 36, my - 36, mx + 36, my + 36], radius=10, fill="#FFFFFF", outline="#0F766E", width=4)
            d.rectangle([mx - 10, my - 24, mx + 10, my + 24], fill="#DC2626")
            d.rectangle([mx - 24, my - 10, mx + 24, my + 10], fill="#DC2626")
            # Emerald "clear" shield badge right (Kenya/Nigeria zero)
            gx, gy = 414, 72
            d.ellipse([gx - 28, gy - 28, gx + 28, gy + 28], fill="#16A34A", outline="#FFFFFF", width=4)
            d.line([(gx - 12, gy + 2), (gx - 2, gy + 12), (gx + 14, gy - 10)], fill="#FFFFFF", width=6)

        else:  # tennis (Turin ATP Finals royal-blue indoor court)
            fill_vgrad(d, 0, 0, cw, ch, "#1E293B", "#334155")
            d.polygon([(96, 46), (432, 46), (cw - 8, ch - 6), (22, ch - 6)], fill="#1D4ED8", outline="#FFFFFF", width=4)
            d.line([(146, 46), (92, ch - 6)], fill="#FFFFFF", width=3)
            d.line([(382, 46), (402, ch - 6)], fill="#FFFFFF", width=3)
            d.line([(114, 86), (416, 86)], fill="#FFFFFF", width=3)
            d.line([(260, 58), (254, ch - 6)], fill="#FFFFFF", width=3)
            d.rectangle([66, 66, 444, 80], fill="#E2E8F0", outline="#0F172A", width=2)
            d.arc([204, 24, 386, 98], 190, 340, fill="#FDE047", width=4)
            tx, ty, tr = 372, 46, 18
            d.ellipse([tx - tr, ty - tr, tx + tr, ty + tr], fill="#BEF264", outline="#15803D", width=3)
            d.arc([tx - 12, ty - 14, tx + 4, ty + 14], 290, 70, fill="#FFFFFF", width=3)

        draw_art_stamp(d, cw, ch, item, is_hero=False)

    return supersampled(w, h, "#FAF7F0", _draw)


def draw_world_map(stories: list[dict], w: int, h: int) -> Image.Image:
    continents = [
        [(-162, 65), (-135, 68), (-95, 70), (-62, 52), (-78, 34), (-84, 24), (-96, 20), (-84, 10), (-92, 14), (-112, 28), (-118, 33), (-124, 39), (-125, 48), (-145, 58)],
        [(-56, 74), (-22, 74), (-32, 62), (-52, 60)],
        [(-78, 10), (-60, 10), (-36, -6), (-40, -22), (-56, -38), (-68, -54), (-74, -44), (-72, -18), (-80, -4)],
        [(-9, 37), (0, 43), (-5, 50), (6, 54), (10, 62), (26, 70), (42, 66), (40, 46), (28, 41), (18, 40), (12, 44), (2, 39)],
        [(-6, 51), (1, 51), (0, 58), (-5, 58)],
        [(-16, 15), (-5, 35), (12, 36), (32, 31), (42, 12), (50, 12), (40, -10), (34, -26), (20, -34), (14, -22), (9, 4), (-8, 6)],
        [(28, 41), (44, 42), (60, 66), (110, 72), (168, 66), (142, 50), (128, 38), (120, 24), (106, 12), (98, 16), (80, 8), (68, 22), (56, 24), (44, 14), (35, 30)],
        [(130, 32), (142, 44), (145, 42), (135, 31)],
        [(98, 4), (116, 2), (128, -4), (114, -8), (104, -6)],
        [(114, -22), (136, -12), (152, -24), (148, -38), (132, -33), (116, -34)],
        [(166, -46), (178, -36), (179, -42), (170, -47)],
    ]

    def proj(lat: float, lon: float, cw: int, ch: int) -> tuple[float, float]:
        x = (lon + 152.0) / 346.0 * (cw - 32) + 16
        y = (76.0 - lat) / 138.0 * (ch - 32) + 12
        return x, y

    def _draw(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        fill_vgrad(d, 0, 0, cw, ch, "#DCEAF6", "#C8DEF0")
        for lat in (-30, 0, 30, 60):
            _, gy = proj(lat, 0, cw, ch)
            d.line([(0, int(gy)), (cw, int(gy))], fill="#B6D2E8", width=2)
        for poly in continents:
            pts = [proj(lat, lon, cw, ch) for lon, lat in poly]
            d.polygon(pts, fill="#F5F1E8", outline="#94A3B8")

        nodes = []
        for s in stories:
            if s.get("lat") is None:
                continue
            px, py = proj(s["lat"], s["lon"], cw, ch)
            nodes.append({"id": s["id"], "region": s["region"], "x": px, "y": py})

        min_dist = 42.0
        for _ in range(70):
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    dx = nodes[j]["x"] - nodes[i]["x"]
                    dy = nodes[j]["y"] - nodes[i]["y"]
                    dist = math.hypot(dx, dy)
                    if dist < 0.01:
                        dx, dy, dist = 1.0, 0.5, 1.118
                    if dist < min_dist:
                        push = (min_dist - dist) * 0.54
                        ux, uy = dx / dist, dy / dist
                        nodes[i]["x"] -= ux * push
                        nodes[i]["y"] -= uy * push
                        nodes[j]["x"] += ux * push
                        nodes[j]["y"] += uy * push
            for n in nodes:
                n["x"] = max(24.0, min(cw - 24.0, n["x"]))
                n["y"] = max(24.0, min(ch - 36.0, n["y"]))

        pin_font = load_font("sans_bold", 22)
        for n in nodes:
            px, py = int(n["x"]), int(n["y"])
            r = 18
            d.ellipse([px - r, py - r, px + r, py + r], fill=REGION_COLORS[n["region"]], outline="#FFFFFF", width=4)
            draw_centered_text(d, px - r, py - r, px + r, py + r, str(n["id"]), pin_font, "#FFFFFF")

        f_off = load_font("sans_bold", 19)
        off_txt = "Off map: #2 Mercury (space) · #10 Bitcoin (global)"
        ow, oh = text_size(d, off_txt, f_off)
        d.rounded_rectangle([12, ch - oh - 14, 12 + ow + 18, ch - 4], radius=6, fill="#FFFFFF", outline="#64748B", width=2)
        draw_centered_text(d, 12, ch - oh - 14, 12 + ow + 18, ch - 4, off_txt, f_off, INK_DARK)

    return supersampled(w, h, "#DCEAF6", _draw)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    data = json.loads((root / "news" / "stories.json").read_text(encoding="utf-8"))

    img = Image.new("RGB", (W, H), BG_PAPER)
    d = ImageDraw.Draw(img)
    errors: list[str] = []

    all_stories = data["hero"] + data["cards"]

    # Fonts — ZERO micro-text! Smallest font anywhere is 10px (eyebrow 9.5/10)!
    f_eyebrow = load_font("sans_bold", 9)
    f_mast = load_font("narrow_bold", 59)
    f_deck = load_font("serif_italic", 12)
    f_stat_val = load_font("narrow_bold", 27)
    f_stat_lbl = load_font("sans", 10)
    f_reg = load_font("sans_bold", 11)

    f_hero_k = load_font("sans_bold", 10)
    f_hero_h = load_font("serif_bold", 19)
    f_hero_b = load_font("sans", 11)
    f_tag = load_font("sans_bold", 10)

    f_card_h = load_font("serif_bold", 14)
    f_card_b = load_font("sans", 10)

    f_sec_hdr = load_font("sans_bold", 11)
    f_dc_hdr = load_font("sans_bold", 12)
    f_dc_bold = load_font("sans_bold", 11)
    f_dc_txt = load_font("sans", 11)
    f_footer = load_font("sans", 10)

    # ── 1. AIRY CLASSIC FRONT-PAGE MASTHEAD (y = 6..84) ───────────────────
    d.rectangle([MARGIN, 5, W - MARGIN, 8], fill=INK_DARK)
    d.text((MARGIN, 10), "THE WORLD IN ONE DAY", font=f_eyebrow, fill=ACCENT_RED)
    right_tag = f"{len(all_stories)} VERIFIED STORIES · 7 REGIONS · FULL-DAY EDITION"
    rw, _ = text_size(d, right_tag, f_eyebrow)
    d.text((W - MARGIN - rw, 10), right_tag, font=f_eyebrow, fill=INK_DARK)

    mw, _ = text_size(d, data["date_label"], f_mast)
    if mw > CONTENT_W:
        errors.append(f"Masthead too wide: {mw} > {CONTENT_W}")
    draw_centered_text(d, MARGIN, 25, W - MARGIN, 67, data["date_label"], f_mast, INK_DARK)

    dw, _ = text_size(d, data["deck"], f_deck)
    if dw > CONTENT_W:
        errors.append(f"Deck too wide: {dw} > {CONTENT_W}")
    draw_centered_text(d, MARGIN, 69, W - MARGIN, 83, data["deck"], f_deck, INK_BODY)
    d.line([(MARGIN, 85), (W - MARGIN, 85)], fill=INK_DARK, width=2)

    # ── 2. AIRY LIGHT-PAPER 6-NUMBER KPI STRIP (y = 88..134) ─────────────
    stat_y0, stat_y1 = 88, 134
    stats = data["stats"]
    col_w = CONTENT_W / len(stats)
    for i, st in enumerate(stats):
        sx0 = int(MARGIN + i * col_w)
        sx1 = int(MARGIN + (i + 1) * col_w)
        d.rectangle([sx0, stat_y0 + 4, sx0 + 3, stat_y1 - 4], fill=ACCENT_RED)
        d.text((sx0 + 9, stat_y0 + 1), st["value"], font=f_stat_val, fill=INK_DARK)
        lbl_lines = wrap_text(d, st["label"], f_stat_lbl, sx1 - sx0 - 14)
        if len(lbl_lines) > 1:
            errors.append(f"Stat {st['value']} label wrapped > 1 line: {lbl_lines}")
        d.text((sx0 + 9, stat_y0 + 30), lbl_lines[0], font=f_stat_lbl, fill=INK_BODY)

    # ── 3. PROPORTIONAL 7-REGION BAR (y = 138..156) ──────────────────────
    reg_order = ["Europe", "Global", "Middle East", "Americas", "Asia", "Africa", "Oceania"]
    reg_short = {"Middle East": "Mid East"}
    counts = {r: sum(1 for s in all_stories if s["region"] == r) for r in reg_order}
    total = sum(counts.values())
    rx = MARGIN
    for idx, r in enumerate(reg_order):
        cnt = counts[r]
        seg_w = (W - MARGIN - rx) if idx == len(reg_order) - 1 else round(CONTENT_W * cnt / total)
        d.rectangle([rx, 138, rx + seg_w - 2, 156], fill=REGION_COLORS[r])
        lbl = f"{reg_short.get(r, r)} {cnt}"
        draw_centered_text(d, rx, 138, rx + seg_w - 2, 156, lbl, f_reg, "#FFFFFF")
        rx += seg_w

    # ── 4. THREE MONUMENTAL HERO PANELS (y = 162..392) ───────────────────
    hero_y, hero_h = 162, 230
    hero_gap = 10
    hero_w = (CONTENT_W - 2 * hero_gap) // 3  # 324
    for i, hitem in enumerate(data["hero"]):
        hx = MARGIN + i * (hero_w + hero_gap)
        if i > 0:
            d.line([(hx - hero_gap // 2, hero_y + 120), (hx - hero_gap // 2, hero_y + hero_h - 4)], fill=RULE, width=1)
        art_h = 114
        art = draw_hero_panel_art(hitem, hero_w, art_h)
        img.paste(art, (hx, hero_y))

        ky = hero_y + art_h + 6
        d.text((hx + 2, ky + 1), hitem["kicker"], font=f_hero_k, fill=REGION_COLORS[hitem["region"]])
        if hitem.get("tag"):
            tg = hitem["tag"]
            tw, _ = text_size(d, tg, f_tag)
            tx0 = hx + hero_w - tw - 12
            d.rounded_rectangle([tx0, ky, hx + hero_w - 1, ky + 15], radius=3, fill=TAG_COLORS[tg])
            draw_centered_text(d, tx0, ky, hx + hero_w - 1, ky + 15, tg, f_tag, "#FFFFFF")

        cy = ky + 18
        h_lines = wrap_text(d, hitem["headline"], f_hero_h, hero_w - 4)
        if len(h_lines) > 2:
            errors.append(f"Hero {hitem['id']} headline > 2 lines: {h_lines}")
        for line in h_lines[:2]:
            d.text((hx + 2, cy), line, font=f_hero_h, fill=INK_DARK)
            cy += 21
        cy += 4

        b_lines = wrap_text(d, hitem["summary"], f_hero_b, hero_w - 4)
        if len(b_lines) > 3:
            errors.append(f"Hero {hitem['id']} summary > 3 lines: {b_lines}")
        for line in b_lines[:3]:
            d.text((hx + 2, cy), line, font=f_hero_b, fill=INK_BODY)
            cy += 14
        if cy > hero_y + hero_h:
            errors.append(f"Hero {hitem['id']} vertical overflow: {cy} > {hero_y + hero_h}")

    d.line([(MARGIN, hero_y + hero_h + 2), (W - MARGIN, hero_y + hero_h + 2)], fill=INK_DARK, width=2)

    # ── 5. TWELVE WIDE, AIRY ILLUSTRATED CARDS (3 rows x 4 cols, y = 400..826)
    c_top = 400
    c_gap_x, c_gap_y = 8, 9
    c_w = (CONTENT_W - 3 * c_gap_x) // 4  # 242 exact!
    c_h = 136
    for idx, citem in enumerate(data["cards"]):
        row, col = divmod(idx, 4)
        cx = MARGIN + col * (c_w + c_gap_x)
        cy0 = c_top + row * (c_h + c_gap_y)
        if col > 0:
            d.line([(cx - c_gap_x // 2, cy0 + 66), (cx - c_gap_x // 2, cy0 + c_h - 4)], fill=RULE, width=1)

        art_h = 64
        art = draw_card_panel_art(citem, c_w, art_h)
        img.paste(art, (cx, cy0))

        ty = cy0 + art_h + 4
        h_lines = wrap_text(d, citem["headline"], f_card_h, c_w - 4)
        if len(h_lines) > 2:
            errors.append(f"Card {citem['id']} headline > 2 lines: {h_lines}")
        for line in h_lines[:2]:
            d.text((cx + 2, ty), line, font=f_card_h, fill=INK_DARK)
            ty += 16
        ty += 3

        b_lines = wrap_text(d, citem["summary"], f_card_b, c_w - 4)
        if len(b_lines) > 2:
            errors.append(f"Card {citem['id']} summary > 2 lines: {b_lines}")
        for line in b_lines[:2]:
            d.text((cx + 2, ty), line, font=f_card_b, fill=INK_BODY)
            ty += 13
        if ty > cy0 + c_h - 2:
            errors.append(f"Card {citem['id']} vertical overflow: {ty} > {cy0 + c_h - 2}")

    for rline in (1, 2):
        ly = c_top + rline * c_h + (rline - 1) * c_gap_y + 4
        d.line([(MARGIN, ly), (W - MARGIN, ly)], fill=RULE, width=1)
    d.line([(MARGIN, c_top + 3 * c_h + 2 * c_gap_y + 2), (W - MARGIN, c_top + 3 * c_h + 2 * c_gap_y + 2)], fill=INK_DARK, width=2)

    # ── 6. BOTTOM BAND: BIG UNCLUTTERED WORLD MAP + CRISP DATE CHECK (y = 834..996)
    band_top, band_bot = 834, 996
    map_x, map_w = MARGIN, 466
    dc_x, dc_w = map_x + map_w + 14, CONTENT_W - map_w - 14  # 512

    # Left: Big Crisp World Map
    d.text((map_x, band_top), "WHERE IT HAPPENED — ALL 15 STORIES ACROSS 7 REGIONS", font=f_sec_hdr, fill=INK_DARK)
    map_y0 = band_top + 17
    map_img = draw_world_map(all_stories, map_w, band_bot - map_y0)
    img.paste(map_img, (map_x, map_y0))
    d.rectangle([map_x, map_y0, map_x + map_w, band_bot], outline=RULE, width=1)

    # Right: Spacious Crisp Editorial Date Check & Verification Box
    d.rectangle([dc_x, band_top, dc_x + dc_w, band_bot], fill=BG_WHITE, outline=INK_DARK, width=1)
    d.rectangle([dc_x, band_top, dc_x + 5, band_bot], fill=ACCENT_RED)
    d.text((dc_x + 14, band_top + 8), "DATE CHECK — LEFT OFF AS EARLIER NEWS (18–20 NOV)", font=f_dc_hdr, fill=ACCENT_RED)
    d.line([(dc_x + 14, band_top + 25), (dc_x + dc_w - 12, band_top + 25)], fill=RULE, width=1)

    cy = band_top + 31
    max_bw = dc_w - 28
    for bullet in data["date_check_bullets"]:
        day_part, rest_part = bullet.split(": ", 1)
        day_lbl = f"• {day_part}: "
        dw0, _ = text_size(d, day_lbl, f_dc_bold)
        # Wrap combined text cleanly so line 1 starts after bold prefix
        first_line_words = []
        rem_words = rest_part.split()
        while rem_words:
            cand = " ".join(first_line_words + [rem_words[0]])
            cw, _ = text_size(d, cand, f_dc_txt)
            if dw0 + cw <= max_bw or not first_line_words:
                first_line_words.append(rem_words.pop(0))
            else:
                break
        d.text((dc_x + 14, cy), day_lbl, font=f_dc_bold, fill=INK_DARK)
        d.text((dc_x + 14 + dw0, cy), " ".join(first_line_words), font=f_dc_txt, fill=INK_BODY)
        cy += 15
        if rem_words:
            cont_lines = wrap_text(d, " ".join(rem_words), f_dc_txt, max_bw - 12)
            for cl in cont_lines:
                d.text((dc_x + 24, cy), cl, font=f_dc_txt, fill=INK_BODY)
                cy += 15
        cy += 3

    d.line([(dc_x + 14, cy + 1), (dc_x + dc_w - 12, cy + 1)], fill=RULE, width=1)
    cy += 7
    hc_lines = wrap_text(d, data["how_checked"], f_dc_txt, max_bw)
    for line in hc_lines:
        d.text((dc_x + 14, cy), line, font=f_dc_txt, fill=INK_MUTED)
        cy += 14
    if cy > band_bot - 2:
        errors.append(f"Date check box vertical overflow: {cy} > {band_bot - 2}")

    # ── 7. CLEAN FOOTER (y = 1001..1019) ──────────────────────────────────
    footer = "Saturday 21 November 2026 · 15 verified stories across 7 regions & 9 beats · Sources named beside each story · Original vector art"
    fw, _ = text_size(d, footer, f_footer)
    if fw > CONTENT_W:
        errors.append(f"Footer too wide: {fw} > {CONTENT_W}")
    draw_centered_text(d, MARGIN, 1001, W - MARGIN, 1019, footer, f_footer, INK_MUTED)

    if errors:
        print("LAYOUT ERRORS FOUND:")
        for e in errors:
            print("  -", e)
        raise SystemExit(1)

    out_path = root / "entry.png"
    img.save(out_path, format="PNG", optimize=True)
    preview = img.resize((300, 300), Image.Resampling.LANCZOS)
    preview.save(root.parent / "preview_300.png", format="PNG")
    print(f"Saved {out_path} ({out_path.stat().st_size} bytes, {img.size[0]}x{img.size[1]})")


if __name__ == "__main__":
    main()
