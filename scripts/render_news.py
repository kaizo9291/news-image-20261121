#!/usr/bin/env python3
"""Render an ultra-crisp, 300px-legible 1024x1024 world-news front page for Saturday 21 November 2026."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 16
CONTENT_W = W - 2 * MARGIN  # 992

# Palette — warm archival newsprint with obsidian & bright gold visual anchors
BG_PAPER = "#FAF7F0"
BG_CARD = "#FFFFFF"
BG_TINT = "#F2EDE3"
BG_DARK = "#111827"
GOLD = "#FACC15"
INK_DARK = "#0F172A"
INK_BODY = "#111827"
INK_MUTED = "#475569"
RULE = "#CFC8BA"
ACCENT_RED = "#B91C1C"

REGION_COLORS = {
    "Europe": "#1D4ED8",
    "Middle East": "#B45309",
    "Americas": "#6D28D9",
    "Africa": "#0F766E",
    "Asia": "#B91C1C",
    "Global": "#334155",
    "Oceania": "#0369A1",
}

TAG_COLORS = {
    "OFFICIAL": "#1E3A5F",
    "REPORTED": "#B45309",
    "CLAIM": "#991B1B",
}

BEAT_COLORS = {
    "Conflict": "#B91C1C",
    "Disaster": "#D97706",
    "Sport": "#15803D",
    "Diplomacy": "#1D4ED8",
    "Economy": "#6D28D9",
    "Climate": "#0F766E",
    "Justice": "#334155",
    "Health": "#0284C7",
    "Science": "#4F46E5",
    "Politics": "#9A3412",
}

FONT_CANDIDATES = {
    "serif_bold": ["C:/Windows/Fonts/georgiab.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"],
    "serif": ["C:/Windows/Fonts/georgia.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"],
    "serif_italic": ["C:/Windows/Fonts/georgiai.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"],
    "sans_bold": ["C:/Windows/Fonts/segoeuib.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    "sans": ["C:/Windows/Fonts/segoeui.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    "narrow_bold": ["C:/Windows/Fonts/ARIALNB.TTF", "C:/Windows/Fonts/segoeuib.ttf"],
    "narrow": ["C:/Windows/Fonts/ARIALN.TTF", "C:/Windows/Fonts/segoeui.ttf"],
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


def draw_art_stamp(d: ImageDraw.ImageDraw, cw: int, item: dict, is_hero: bool) -> None:
    """High-contrast 300px-legible black title banner + bright gold sub-ribbon top-left + region badge top-right."""
    if is_hero:
        f_ban = load_font("narrow_bold", 54)   # 27px effective at 1024 -> crisp 8px at 300px!
        f_sub = load_font("narrow_bold", 24)   # 12px effective at 1024
        pad_x, pad_y = 22, 14
        sub_px, sub_py = 16, 10
        ox, oy = 12, 12
        r_badge = 22
        f_num = load_font("sans_bold", 24)
    else:
        f_ban = load_font("narrow_bold", 38)   # 19px effective at 1024 -> crisp 5.6px at 300px!
        f_sub = load_font("narrow_bold", 20)   # 10px effective at 1024
        pad_x, pad_y = 16, 10
        sub_px, sub_py = 12, 7
        ox, oy = 10, 10
        r_badge = 17
        f_num = load_font("sans_bold", 19)

    bw, bh = text_size(d, item["banner"], f_ban)
    bx1 = ox + bw + pad_x
    by1 = oy + bh + pad_y
    d.rectangle([ox + 3, oy + 3, bx1 + 3, by1 + 3], fill="#020617")
    d.rectangle([ox, oy, bx1, by1], fill="#0B1120")
    draw_centered_text(d, ox, oy, bx1, by1, item["banner"], f_ban, "#FFFFFF")

    sw, sh = text_size(d, item["sub"], f_sub)
    sy0 = by1 + 3
    sy1 = sy0 + sh + sub_py
    sx1 = ox + sw + sub_px
    d.rectangle([ox + 2, sy0 + 2, sx1 + 2, sy1 + 2], fill="#020617")
    d.rectangle([ox, sy0, sx1, sy1], fill=GOLD)
    draw_centered_text(d, ox, sy0, sx1, sy1, item["sub"], f_sub, "#0F172A")

    # Top-right region-colored numbered badge
    cx = cw - oy - r_badge
    cy = oy + r_badge
    d.ellipse([cx - r_badge, cy - r_badge, cx + r_badge, cy + r_badge], fill=REGION_COLORS[item["region"]], outline="#FFFFFF", width=4 if is_hero else 3)
    draw_centered_text(d, cx - r_badge, cy - r_badge, cx + r_badge, cy + r_badge, str(item["id"]), f_num, "#FFFFFF")


def draw_hero_panel_art(item: dict, w: int, h: int) -> Image.Image:
    kind = item["art"]

    def _draw(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        if kind == "cop31":
            fill_vgrad(d, 0, 0, cw, ch, "#0E3A53", "#E8A87C")
            d.ellipse([int(cw * 0.44), int(ch * 0.14), int(cw * 0.98), int(ch * 1.15)], fill="#F59E0B")
            d.ellipse([int(cw * 0.52), int(ch * 0.24), int(cw * 0.90), int(ch * 1.02)], fill="#FDE68A")
            fill_vgrad(d, 0, int(ch * 0.72), cw, ch, "#1D4ED8", "#0F294A")
            d.polygon([(0, int(ch * 0.78)), (95, int(ch * 0.62)), (200, int(ch * 0.68)), (320, int(ch * 0.78))], fill="#1E293B")
            d.pieslice([126, int(ch * 0.52), 322, int(ch * 0.96)], 180, 360, fill="#F8FAFC", outline="#0F172A", width=4)
            for fx in (148, 182, 216, 250, 284):
                d.line([(fx, int(ch * 0.65)), (fx, int(ch * 0.77))], fill="#475569", width=3)
            flag_cols = ["#2563EB", "#16A34A", "#DC2626", "#F59E0B", "#0EA5E9", "#7C3AED"]
            for i, fc in enumerate(flag_cols):
                fx = 40 + i * 32
                d.line([(fx, int(ch * 0.70)), (fx, int(ch * 0.93))], fill="#E2E8F0", width=3)
                d.rectangle([fx, int(ch * 0.70), fx + 20, int(ch * 0.76)], fill=fc)
            gx, gy, gr = int(cw * 0.56), int(ch * 0.55), 64
            d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill="#1D4ED8", outline="#0F172A", width=5)
            d.ellipse([gx - gr + 8, gy - gr + 8, gx + gr - 16, gy + gr - 14], fill="#2563EB")
            d.polygon([(gx - 42, gy - 24), (gx - 10, gy - 40), (gx + 10, gy - 14), (gx - 12, gy + 26), (gx - 36, gy + 12)], fill="#22C55E")
            d.polygon([(gx + 16, gy - 28), (gx + 48, gy - 12), (gx + 36, gy + 24), (gx + 14, gy + 10)], fill="#16A34A")
            d.ellipse([gx - 16, gy + 28, gx + 14, gy + 50], fill="#22C55E")
            tx = int(cw * 0.74)
            d.rounded_rectangle([tx - 13, 60, tx + 13, ch - 52], radius=13, fill="#FFFFFF", outline="#0F172A", width=4)
            d.ellipse([tx - 24, ch - 70, tx + 24, ch - 22], fill="#DC2626", outline="#0F172A", width=4)
            d.rectangle([tx - 7, 84, tx + 7, ch - 44], fill="#DC2626")
            for ty in range(82, ch - 74, 16):
                d.line([(tx + 14, ty), (tx + 24, ty)], fill="#0F172A", width=3)
            kx, ky, kr = int(cw * 0.88), int(ch * 0.64), 44
            d.ellipse([kx - kr, ky - kr, kx + kr, ky + kr], fill="#FFFFFF", outline="#0F172A", width=5)
            d.pieslice([kx - kr + 6, ky - kr + 6, kx + kr - 6, ky + kr - 6], 270, 340, fill="#FCA5A5")
            for tick in range(0, 360, 30):
                rad = math.radians(tick)
                d.line(
                    [(kx + int((kr - 10) * math.cos(rad)), ky + int((kr - 10) * math.sin(rad))),
                     (kx + int((kr - 3) * math.cos(rad)), ky + int((kr - 3) * math.sin(rad)))],
                    fill="#0F172A",
                    width=3,
                )
            d.line([(kx, ky), (kx, ky - 26)], fill="#0F172A", width=5)
            d.line([(kx, ky), (kx + 22, ky - 11)], fill="#DC2626", width=5)
            d.ellipse([kx - 6, ky - 6, kx + 6, ky + 6], fill="#0F172A")

        elif kind == "mercury":
            fill_vgrad(d, 0, 0, cw, ch, "#030712", "#0F172A")
            for sr, col in [(130, "#451A03"), (92, "#9A3412"), (58, "#EA580C"), (32, "#FACC15"), (16, "#FEF9C3")]:
                d.ellipse([18 - sr, ch - 10 - sr, 18 + sr, ch - 10 + sr], fill=col)
            stars = [
                (45, 136, 2), (92, 168, 3), (140, 126, 2), (195, 152, 2), (242, 66, 3),
                (288, 112, 2), (318, 42, 2), (355, 192, 3), (390, 34, 2), (432, 212, 2),
                (260, 205, 2), (168, 198, 2), (590, 214, 3), (618, 165, 2), (336, 152, 2),
            ]
            for sx, sy, sr in stars:
                d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill="#F8FAFC")
            d.arc([244, 54, 618, 224], 165, 355, fill="#38BDF8", width=4)
            mx, my, mr = int(cw * 0.77), int(ch * 0.56), 114
            d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill="#475569", outline="#94A3B8", width=3)
            d.pieslice([mx - mr + 2, my - mr + 2, mx + mr - 2, my + mr - 2], 100, 265, fill="#B8A99A")
            d.ellipse([mx - mr + 42, my - mr + 8, mx + mr - 8, my + mr - 8], fill="#64748B")
            d.ellipse([mx - mr + 78, my - mr + 16, mx + mr - 2, my + mr - 16], fill="#334155")
            craters = [
                (mx - 62, my - 34, 18), (mx - 44, my + 24, 24), (mx - 82, my + 4, 12),
                (mx - 22, my - 58, 14), (mx - 12, my + 56, 16), (mx + 14, my - 12, 20),
                (mx - 68, my + 54, 11), (mx + 26, my + 38, 13),
            ]
            for cx0, cy0, cr in craters:
                d.ellipse([cx0 - cr, cy0 - cr, cx0 + cr, cy0 + cr], fill="#475569", outline="#CBD5E1", width=2)
                d.ellipse([cx0 - cr + 4, cy0 - cr + 3, cx0 + cr - 2, cy0 + cr - 2], fill="#7C7268" if cx0 < mx - 25 else "#3F4B5B")
            d.arc([244, 54, 618, 224], 0, 165, fill="#FACC15", width=5)
            px, py = 330, 148
            d.polygon([(px - 22, py + 2), (px - 76, py + 16), (px - 68, py + 28)], fill="#38BDF8")
            d.polygon([(px - 22, py + 4), (px - 52, py + 14), (px - 48, py + 20)], fill="#E0F2FE")
            d.polygon([(px - 10, py - 14), (px + 12, py - 74), (px + 34, py - 68), (px + 10, py - 8)], fill="#1D4ED8", outline="#93C5FD", width=2)
            d.polygon([(px - 12, py + 12), (px - 32, py + 72), (px - 10, py + 78), (px + 10, py + 16)], fill="#1D4ED8", outline="#93C5FD", width=2)
            d.rounded_rectangle([px - 22, py - 16, px + 26, py + 16], radius=6, fill="#F59E0B", outline="#FEF3C7", width=3)
            d.polygon([(px + 26, py - 14), (px + 48, py - 6), (px + 48, py + 6), (px + 26, py + 14)], fill="#E2E8F0", outline="#0F172A", width=2)
            d.arc([px - 6, py - 34, px + 26, py - 8], 180, 360, fill="#F8FAFC", width=4)

        else:  # riyadh
            fill_vgrad(d, 0, 0, cw, ch, "#060D1F", "#172554")
            d.ellipse([272, 22, 304, 54], fill="#FEF08A")
            d.ellipse([282, 18, 314, 50], fill="#0C1736")
            for sx, sy in [(218, 42), (344, 34), (476, 24), (586, 44), (312, 92), (512, 66)]:
                d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill="#E2E8F0")
            d.rectangle([0, ch - 26, cw, ch], fill="#0F172A")
            blds = [
                (14, 166, 62), (70, 146, 118), (126, 158, 172), (182, 134, 232),
                (244, 152, 294), (306, 136, 356), (368, 148, 418), (528, 144, 578), (586, 156, 636),
            ]
            for x0, y0, x1 in blds:
                d.rectangle([x0, y0, x1, ch - 26], fill="#1E3A5F", outline="#334155", width=2)
                for wy in range(y0 + 10, ch - 34, 16):
                    for wx in range(x0 + 8, x1 - 8, 14):
                        d.rectangle([wx, wy, wx + 6, wy + 8], fill="#FDE68A" if (wx + wy) % 3 == 0 else "#334155")
            d.polygon([(388, ch - 26), (414, 108), (440, ch - 26)], fill="#274C77", outline="#60A5FA", width=2)
            d.ellipse([406, 126, 422, 142], fill="#FACC15")
            d.rectangle([452, 84, 518, ch - 26], fill="#335C81", outline="#93C5FD", width=2)
            d.ellipse([464, 94, 506, 154], fill="#0E1C3D")
            d.rectangle([460, 84, 510, 96], fill="#E2E8F0")
            for ix, iy in [(320, 112), (424, 68), (554, 96)]:
                d.line([(ix + 96, 4), (ix, iy)], fill="#EF4444", width=5)
                d.line([(ix - 54, ch - 28), (ix, iy)], fill="#38BDF8", width=4)
                d.ellipse([ix - 30, iy - 30, ix + 30, iy + 30], outline="#FDE047", width=3)
                for ang in range(0, 360, 40):
                    rad = math.radians(ang)
                    d.line([(ix, iy), (ix + int(26 * math.cos(rad)), iy + int(26 * math.sin(rad)))], fill="#F97316", width=5)
                d.ellipse([ix - 13, iy - 13, ix + 13, iy + 13], fill="#FEF9C3")

        draw_art_stamp(d, cw, item, is_hero=True)

    return supersampled(w, h, "#0F172A", _draw)


def draw_card_panel_art(item: dict, w: int, h: int) -> Image.Image:
    """Wide 242x74 (484x148 at 2x) custom editorial illustrations with generous space between stamp and subject."""
    kind = item["art"]

    def _draw(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        if kind == "ship":
            fill_vgrad(d, 0, 0, cw, int(ch * 0.68), "#1E3A5F", "#64748B")
            fill_vgrad(d, 0, int(ch * 0.68), cw, ch, "#0F294A", "#08172E")
            # Smoke plume billowing upper-right
            for sx, sy, sr, col in [
                (334, 72, 24, "#334155"), (362, 52, 28, "#475569"), (396, 36, 32, "#334155"),
                (432, 22, 34, "#1E293B"), (318, 84, 18, "#475569"),
            ]:
                d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=col)
            # Cargo ship hull positioned right-center
            d.polygon([(192, 100), (434, 96), (418, 126), (212, 126)], fill="#1E293B", outline="#0F172A", width=3)
            d.polygon([(202, 112), (428, 110), (418, 126), (212, 126)], fill="#991B1B")
            # White bridge superstructure aft
            d.rectangle([376, 62, 418, 98], fill="#F1F5F9", outline="#0F172A", width=2)
            d.rectangle([384, 68, 410, 78], fill="#38BDF8")
            # Deck containers
            d.rectangle([232, 82, 276, 99], fill="#2563EB", outline="#0F172A", width=2)
            d.rectangle([278, 82, 318, 99], fill="#D97706", outline="#0F172A", width=2)
            # Bright midship fire
            d.polygon([(304, 100), (322, 52), (338, 80), (354, 44), (370, 100)], fill="#EA580C")
            d.polygon([(316, 100), (328, 66), (342, 84), (354, 64), (364, 100)], fill="#FACC15")
            # Swooping attack drone
            d.polygon([(256, 36), (288, 46), (270, 54)], fill="#F8FAFC", outline="#0F172A", width=2)
            d.line([(278, 50), (314, 70)], fill="#FDE047", width=3)
            # Orange evacuation boat & wave highlights
            d.polygon([(126, 124), (166, 124), (158, 134), (134, 134)], fill="#F97316")
            for wx in (36, 198, 298, 404):
                d.line([(wx, 136), (wx + 44, 136)], fill="#38BDF8", width=2)

        elif kind == "sinaloa":
            fill_vgrad(d, 0, 0, cw, ch, "#1E1B4B", "#C2410C")
            d.polygon([(0, ch), (94, 76), (196, ch)], fill="#431407")
            d.polygon([(140, ch), (280, 60), (416, ch)], fill="#29120A")
            d.polygon([(328, ch), (432, 76), (cw, ch)], fill="#1C0C08")
            # Bright searchlight cone sweeping mountain ridge
            d.polygon([(334, 60), (254, ch), (368, ch)], fill="#FEF08A")
            d.polygon([(0, ch), (112, 116), (242, 130), (382, 118), (cw, ch)], fill="#0F172A")
            # Red & blue tactical light bar
            d.ellipse([292, 118, 314, 134], fill="#EF4444")
            d.ellipse([314, 118, 336, 134], fill="#3B82F6")
            # Tactical helicopter centered clearly in upper-right sky
            hx, hy = 342, 54
            d.line([(hx - 62, hy - 14), (hx + 52, hy - 14)], fill="#E2E8F0", width=4)
            d.line([(hx, hy - 14), (hx, hy - 2)], fill="#94A3B8", width=4)
            d.rounded_rectangle([hx - 28, hy - 4, hx + 28, hy + 16], radius=8, fill="#0F172A", outline="#E2E8F0", width=2)
            d.line([(hx + 26, hy + 2), (hx + 68, hy - 2)], fill="#0F172A", width=5)
            d.ellipse([hx + 62, hy - 10, hx + 76, hy + 4], outline="#E2E8F0", width=2)
            d.line([(hx - 20, hy + 22), (hx + 22, hy + 22)], fill="#94A3B8", width=3)

        elif kind == "quake":
            fill_vgrad(d, 0, 0, cw, int(ch * 0.54), "#FEF3C7", "#FDE68A")
            fill_vgrad(d, 0, int(ch * 0.54), cw, ch, "#0284C7", "#0C4A6E")
            d.polygon([(0, int(ch * 0.62)), (88, int(ch * 0.44)), (182, int(ch * 0.50)), (248, int(ch * 0.62))], fill="#15803D")
            ex, ey = 368, 102
            for rr in (22, 42, 64, 86):
                d.ellipse([ex - rr, ey - rr // 2, ex + rr, ey + rr // 2], outline="#EF4444", width=4)
            d.ellipse([ex - 11, ey - 11, ex + 11, ey + 11], fill="#DC2626", outline="#FEF08A", width=3)
            pts = [
                (16, 94), (156, 94), (186, 88), (208, 106), (228, 60), (248, 124),
                (270, 42), (292, 132), (314, 54), (336, 118), (360, 82), (394, 96), (468, 94),
            ]
            d.line(pts, fill="#B91C1C", width=6)

        elif kind == "boat":
            fill_vgrad(d, 0, 0, cw, int(ch * 0.54), "#134E4A", "#D97706")
            fill_vgrad(d, 0, int(ch * 0.54), cw, ch, "#0F294A", "#082F49")
            d.rectangle([0, int(ch * 0.48), cw, int(ch * 0.56)], fill="#064E3B")
            for px in (306, 344, 388, 434):
                d.line([(px, int(ch * 0.52)), (px + 4, int(ch * 0.26))], fill="#022C22", width=4)
                for ang in (-140, -100, -50, -10, 20):
                    rad = math.radians(ang)
                    d.line([(px + 4, int(ch * 0.26)), (px + 4 + int(24 * math.cos(rad)), int(ch * 0.26) + int(18 * math.sin(rad)))], fill="#022C22", width=3)
            # High-contrast sunlit amber overturned wooden hull
            bx, by = 304, 106
            d.pieslice([bx - 96, by - 36, bx + 96, by + 38], 188, 352, fill="#B45309", outline="#FEF3C7", width=4)
            d.arc([bx - 84, by - 26, bx + 84, by + 26], 195, 345, fill="#F59E0B", width=6)
            d.line([(bx - 74, by - 12), (bx + 72, by - 14)], fill="#78350F", width=4)
            for rx, ry, rw in [(156, 114, 88), (266, 120, 126), (356, 112, 84), (218, 134, 112)]:
                d.line([(rx, ry), (rx + rw, ry)], fill="#BAE6FD", width=4)
            d.ellipse([408, 100, 442, 130], outline="#F97316", width=8)

        elif kind == "plane":
            fill_vgrad(d, 0, 0, cw, int(ch * 0.66), "#0B1530", "#1E3A5F")
            d.rectangle([0, int(ch * 0.66), cw, ch], fill="#334155")
            d.line([(16, int(ch * 0.84)), (cw - 16, int(ch * 0.84))], fill="#E2E8F0", width=3)
            for lx in range(28, cw - 20, 56):
                d.ellipse([lx - 4, int(ch * 0.68) - 4, lx + 4, int(ch * 0.68) + 4], fill="#FACC15")
            # Fire truck waiting left
            d.rounded_rectangle([42, 104, 96, 124], radius=4, fill="#DC2626", outline="#FFFFFF", width=2)
            d.ellipse([62, 94, 76, 108], fill="#38BDF8")
            # Wide-body Boeing 767 landing cleanly center-right
            px, py = 312, 84
            d.polygon([(px + 78, py + 8), (cw, py + 24), (cw, py + 50)], fill="#FEF08A")
            d.polygon([(px - 92, py - 4), (px + 64, py - 10), (px + 98, py + 4), (px + 78, py + 16), (px - 82, py + 14)], fill="#F8FAFC", outline="#0F172A", width=3)
            d.polygon([(px - 88, py - 4), (px - 114, py - 40), (px - 62, py - 40), (px - 52, py - 6)], fill="#DC2626", outline="#0F172A", width=2)
            d.polygon([(px - 94, py - 16), (px - 74, py - 32), (px - 66, py - 14)], fill="#FACC15")
            d.polygon([(px - 20, py + 4), (px + 34, py + 4), (px + 6, py + 26)], fill="#94A3B8", outline="#0F172A", width=2)
            for wx in (px - 16, px + 54):
                d.ellipse([wx - 6, py + 18, wx + 6, py + 30], fill="#0F172A", outline="#E2E8F0", width=2)

        elif kind == "fbi":
            fill_vgrad(d, 0, 0, cw, ch, "#090D1A", "#172554")
            for gy in range(20, ch, 24):
                d.line([(0, gy), (cw, gy)], fill="#1E293B", width=1)
            for gx in range(28, cw, 36):
                d.line([(gx, 0), (gx, ch)], fill="#1E293B", width=1)
            # Server rack tower (shifted cleanly right of stamp)
            d.rounded_rectangle([244, 56, 330, 138], radius=6, fill="#1E293B", outline="#60A5FA", width=3)
            for ry in (68, 86, 104, 122):
                d.rectangle([254, ry, 320, ry + 10], fill="#0F172A")
                d.ellipse([260, ry + 2, 268, ry + 8], fill="#EF4444" if ry != 104 else "#22C55E")
                d.rectangle([274, ry + 3, 312, ry + 7], fill="#38BDF8")
            # Crimson breached padlock
            d.arc([302, 46, 336, 80], 180, 360, fill="#FCA5A5", width=5)
            d.rounded_rectangle([296, 64, 342, 98], radius=5, fill="#DC2626", outline="#FFFFFF", width=2)
            d.ellipse([314, 75, 324, 85], fill="#FEF08A")
            # Green/Gold Nvidia microchip on right
            cx0, cy0 = 378, 66
            d.rounded_rectangle([cx0, cy0, cx0 + 70, cy0 + 62], radius=6, fill="#064E3B", outline="#22C55E", width=4)
            d.rectangle([cx0 + 16, cy0 + 16, cx0 + 54, cy0 + 46], fill="#10B981", outline="#FACC15", width=2)
            for pin in range(cx0 + 12, cx0 + 64, 14):
                d.line([(pin, cy0 - 12), (pin, cy0)], fill="#FACC15", width=3)
                d.line([(pin, cy0 + 62), (pin, cy0 + 74)], fill="#FACC15", width=3)

        elif kind == "bitcoin":
            fill_vgrad(d, 0, 0, cw, ch, "#090D16", "#111827")
            for gy in (48, 84, 118):
                d.line([(12, gy), (cw - 12, gy)], fill="#1F2937", width=2)
            red_pts = [(18, 92), (82, 98), (144, 86), (206, 110), (264, 130)]
            d.line(red_pts, fill="#EF4444", width=7)
            grn_pts = [(264, 130), (312, 110), (354, 116), (406, 86), (464, 60)]
            d.line(grn_pts, fill="#22C55E", width=7)
            d.ellipse([255, 121, 273, 139], fill="#EF4444", outline="#FFFFFF", width=3)
            bx, by, br = 374, 58, 34
            d.ellipse([bx - br, by - br, bx + br, by + br], fill="#F59E0B", outline="#FEF08A", width=4)
            d.ellipse([bx - br + 6, by - br + 6, bx + br - 6, by + br - 6], outline="#B45309", width=2)
            bf = load_font("sans_bold", 38)
            draw_centered_text(d, bx - br, by - br, bx + br, by + br, "B", bf, "#FFFFFF")

        else:  # cricket
            fill_vgrad(d, 0, 0, cw, 34, "#38BDF8", "#BAE6FD")
            d.rectangle([0, 34, cw, ch], fill="#15803D")
            for gx in range(0, cw, 48):
                d.rectangle([gx, 34, gx + 24, ch], fill="#16A34A")
            d.polygon([(240, 34), (324, 34), (372, ch), (192, ch)], fill="#E5D5A8", outline="#FFFFFF", width=2)
            d.line([(218, 114), (346, 114)], fill="#FFFFFF", width=3)
            sx = 282
            for ox in (-15, 0, 15):
                d.line([(sx + ox, 46), (sx + ox, 118)], fill="#92400E", width=6)
            d.line([(sx - 20, 46), (sx + 20, 46)], fill="#F59E0B", width=6)
            d.polygon([(354, 46), (376, 42), (398, 112), (374, 118)], fill="#FDE68A", outline="#78350F", width=3)
            d.ellipse([402, 64, 440, 102], fill="#B91C1C", outline="#FFFFFF", width=3)
            d.arc([405, 67, 437, 99], 20, 160, fill="#FEF3C7", width=2)
            # India & NZ flags bottom-left
            d.rectangle([16, 104, 72, 115], fill="#F97316")
            d.rectangle([16, 115, 72, 126], fill="#FFFFFF")
            d.rectangle([16, 126, 72, 137], fill="#16A34A")
            d.rectangle([82, 104, 138, 137], fill="#1E3A8A")
            d.line([(82, 113), (108, 113)], fill="#DC2626", width=3)
            d.line([(95, 104), (95, 122)], fill="#DC2626", width=3)
            for rx0, ry0 in [(122, 110), (129, 119), (117, 121), (122, 130)]:
                d.ellipse([rx0 - 2, ry0 - 2, rx0 + 2, ry0 + 2], fill="#EF4444")

        draw_art_stamp(d, cw, item, is_hero=False)

    return supersampled(w, h, "#0F172A", _draw)


def draw_world_map(lead_stories: list[dict], brief_stories: list[dict], w: int, h: int) -> Image.Image:
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
        x = (lon + 150.0) / 342.0 * (cw - 24) + 12
        y = (76.0 - lat) / 138.0 * (ch - 32) + 10
        return x, y

    def _draw(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        fill_vgrad(d, 0, 0, cw, ch, "#D8E7F3", "#C5DCF0")
        for lat in (-30, 0, 30, 60):
            _, gy = proj(lat, 0, cw, ch)
            d.line([(0, int(gy)), (cw, int(gy))], fill="#B5D0E6", width=2)
        for poly in continents:
            pts = [proj(lat, lon, cw, ch) for lon, lat in poly]
            d.polygon(pts, fill="#F3EFE6", outline="#94A3B8")

        # Plot all 22 briefs first as clean region-colored location dots
        for b in brief_stories:
            if b.get("lat") is None:
                continue
            bx, by = proj(b["lat"], b["lon"], cw, ch)
            dr = 6
            d.ellipse([bx - dr, by - dr, bx + dr, by + dr], fill=REGION_COLORS[b["region"]], outline="#FFFFFF", width=2)

        # Plot terrestrial illustrated leads as bold numbered pins with repulsion
        nodes = []
        for s in lead_stories:
            if s.get("lat") is None:
                continue
            px, py = proj(s["lat"], s["lon"], cw, ch)
            nodes.append({"id": s["id"], "region": s["region"], "x": px, "y": py})

        min_dist = 34.0
        for _ in range(60):
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
                n["x"] = max(20.0, min(cw - 20.0, n["x"]))
                n["y"] = max(20.0, min(ch - 38.0, n["y"]))

        pin_font = load_font("sans_bold", 20)
        for n in nodes:
            px, py = int(n["x"]), int(n["y"])
            r = 15
            d.ellipse([px - r, py - r, px + r, py + r], fill=REGION_COLORS[n["region"]], outline="#FFFFFF", width=3)
            draw_centered_text(d, px - r, py - r, px + r, py + r, str(n["id"]), pin_font, "#FFFFFF")

        f_off = load_font("sans_bold", 15)
        off_txt = "Pins: 1–11 · Dots: briefs · Off map: #2, #10"
        ow, oh = text_size(d, off_txt, f_off)
        d.rounded_rectangle([8, ch - oh - 12, 8 + ow + 16, ch - 4], radius=5, fill="#0F172A")
        draw_centered_text(d, 8, ch - oh - 12, 8 + ow + 16, ch - 4, off_txt, f_off, "#F8FAFC")

    return supersampled(w, h, "#D8E7F3", _draw)


def draw_source_chips(
    d: ImageDraw.ImageDraw,
    right_x: int,
    y0: int,
    y1: int,
    sources: list[str],
    font: ImageFont.ImageFont,
    tag: str | None = None,
) -> int:
    """Draw right-aligned crisp source chips (+ optional status tag) and return leftmost x used."""
    cur_x = right_x
    for src in reversed(sources):
        tw, _ = text_size(d, src, font)
        w_chip = tw + 8
        x0 = cur_x - w_chip
        d.rounded_rectangle([x0, y0, cur_x, y1], radius=2, fill="#FFFFFF", outline="#64748B", width=1)
        draw_centered_text(d, x0, y0, cur_x, y1, src, font, "#1E293B")
        cur_x = x0 - 4
    if tag:
        tw, _ = text_size(d, tag, font)
        w_chip = tw + 8
        x0 = cur_x - w_chip
        d.rounded_rectangle([x0, y0, cur_x, y1], radius=2, fill=TAG_COLORS[tag])
        draw_centered_text(d, x0, y0, cur_x, y1, tag, font, "#FFFFFF")
        cur_x = x0 - 4
    return cur_x


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    data = json.loads((root / "news" / "stories.json").read_text(encoding="utf-8"))

    img = Image.new("RGB", (W, H), BG_PAPER)
    d = ImageDraw.Draw(img)
    errors: list[str] = []

    all_stories = data["hero"] + data["cards"] + data["briefs"]

    # Fonts — upsized & ultra-crisp for zero 300px blur or OCR errors
    f_mast = load_font("narrow_bold", 70)
    f_deck = load_font("serif_italic", 12)
    f_reg = load_font("sans_bold", 10)
    f_stat_val = load_font("narrow_bold", 28)
    f_stat_lbl = load_font("sans", 10)
    f_stat_ref = load_font("sans_bold", 8)

    f_hero_k = load_font("sans_bold", 10)
    f_hero_h = load_font("serif_bold", 19)
    f_hero_b = load_font("sans", 11)
    f_chip = load_font("sans_bold", 8)

    f_card_h = load_font("serif_bold", 14)
    f_card_b = load_font("sans", 10)
    f_card_chip = load_font("sans_bold", 8)

    f_sec_hdr = load_font("sans_bold", 10)
    f_br_num = load_font("sans_bold", 8)
    f_br_loc = load_font("sans_bold", 9)
    f_br_txt = load_font("sans", 9)
    f_br_src = load_font("sans_bold", 7)

    f_beat_lbl = load_font("sans_bold", 8)
    f_beat_cnt = load_font("sans_bold", 8)

    f_dc_badge = load_font("narrow_bold", 17)
    f_dc_sub = load_font("sans_bold", 8)
    f_dc_txt = load_font("sans", 9)
    f_dc_bold = load_font("sans_bold", 9)
    f_footer = load_font("sans", 8)

    # ── 1. GIANT FULL-WIDTH MASTHEAD (y = 3..73) ──────────────────────────
    mw, _ = text_size(d, data["date_label"], f_mast)
    if mw > CONTENT_W:
        errors.append(f"Masthead too wide: {mw} > {CONTENT_W}")
    draw_centered_text(d, MARGIN, 3, W - MARGIN, 56, data["date_label"], f_mast, INK_DARK)

    dw, _ = text_size(d, data["deck"], f_deck)
    if dw > CONTENT_W:
        errors.append(f"Deck too wide: {dw} > {CONTENT_W}")
    draw_centered_text(d, MARGIN, 57, W - MARGIN, 72, data["deck"], f_deck, INK_DARK)

    # ── 2. PROPORTIONAL 7-REGION HEADER BAR (y = 75..92) ─────────────────
    reg_order = ["Europe", "Middle East", "Americas", "Africa", "Asia", "Global", "Oceania"]
    reg_short = {"Middle East": "Mid East"}
    counts = {r: sum(1 for s in all_stories if s["region"] == r) for r in reg_order}
    total = sum(counts.values())

    tag_w = 148
    d.rectangle([MARGIN, 75, MARGIN + tag_w - 2, 92], fill=BG_DARK)
    draw_centered_text(d, MARGIN, 75, MARGIN + tag_w - 2, 92, f"{total} STORIES · 7 REGIONS", f_reg, GOLD)

    rem_w = CONTENT_W - tag_w
    rx = MARGIN + tag_w
    for idx, r in enumerate(reg_order):
        cnt = counts[r]
        seg_w = (W - MARGIN - rx) if idx == len(reg_order) - 1 else round(rem_w * cnt / total)
        d.rectangle([rx, 75, rx + seg_w - 2, 92], fill=REGION_COLORS[r])
        lbl = f"{reg_short.get(r, r)} {cnt}"
        draw_centered_text(d, rx, 75, rx + seg_w - 2, 92, lbl, f_reg, "#FFFFFF")
        rx += seg_w

    # ── 3. DARK OBSIDIAN & BRIGHT GOLD KPI BAR (y = 95..145) ─────────────
    stat_y0, stat_y1 = 95, 145
    d.rectangle([MARGIN, stat_y0, W - MARGIN, stat_y1], fill=BG_DARK)
    stats = data["stats"]
    col_w = CONTENT_W / len(stats)
    for i, st in enumerate(stats):
        sx0 = int(MARGIN + i * col_w)
        sx1 = int(MARGIN + (i + 1) * col_w)
        if i > 0:
            d.line([(sx0, stat_y0 + 7), (sx0, stat_y1 - 7)], fill="#334155", width=1)
        d.text((sx0 + 9, stat_y0 + 4), st["value"], font=f_stat_val, fill=GOLD)
        ref_s = f"#{st['ref']}"
        rfw, _ = text_size(d, ref_s, f_stat_ref)
        d.text((sx1 - rfw - 8, stat_y0 + 9), ref_s, font=f_stat_ref, fill="#94A3B8")
        lbl_lines = wrap_text(d, st["label"], f_stat_lbl, sx1 - sx0 - 14)
        if len(lbl_lines) > 1:
            errors.append(f"Stat {st['value']} label wrapped > 1 line: {lbl_lines}")
        d.text((sx0 + 9, stat_y0 + 34), lbl_lines[0], font=f_stat_lbl, fill="#F8FAFC")

    # ── 4. THREE MASSIVE OPEN-EDITORIAL HERO PANELS (y = 151..389) ───────
    hero_y, hero_h = 151, 238
    hero_gap = 10
    hero_w = (CONTENT_W - 2 * hero_gap) // 3  # 324
    for i, hitem in enumerate(data["hero"]):
        hx = MARGIN + i * (hero_w + hero_gap)
        if i > 0:
            d.line([(hx - hero_gap // 2, hero_y + 126), (hx - hero_gap // 2, hero_y + hero_h - 4)], fill=RULE, width=1)
        art_h = 122
        art = draw_hero_panel_art(hitem, hero_w, art_h)
        img.paste(art, (hx, hero_y))

        ky = hero_y + art_h + 6
        d.text((hx + 2, ky + 1), hitem["kicker"], font=f_hero_k, fill=REGION_COLORS[hitem["region"]])
        draw_source_chips(d, hx + hero_w - 1, ky, ky + 14, hitem["sources"], f_chip, hitem.get("tag"))

        cy = ky + 17
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

    # ── 5. EIGHT WIDE PICTURE CARDS (2 rows x 4 cols, y = 396..696) ──────
    c_top = 396
    c_gap_x, c_gap_y = 8, 8
    c_w = (CONTENT_W - 3 * c_gap_x) // 4  # 242 exact!
    c_h = 146
    for idx, citem in enumerate(data["cards"]):
        row, col = divmod(idx, 4)
        cx = MARGIN + col * (c_w + c_gap_x)
        cy0 = c_top + row * (c_h + c_gap_y)
        if col > 0:
            d.line([(cx - c_gap_x // 2, cy0 + 76), (cx - c_gap_x // 2, cy0 + c_h - 2)], fill=RULE, width=1)

        art_h = 70
        art = draw_card_panel_art(citem, c_w, art_h)
        img.paste(art, (cx, cy0))

        ty = cy0 + art_h + 3
        h_lines = wrap_text(d, citem["headline"], f_card_h, c_w - 4)
        if len(h_lines) > 2:
            errors.append(f"Card {citem['id']} headline > 2 lines: {h_lines}")
        for line in h_lines[:2]:
            d.text((cx + 2, ty), line, font=f_card_h, fill=INK_DARK)
            ty += 16
        ty += 2

        b_lines = wrap_text(d, citem["summary"], f_card_b, c_w - 4)
        if len(b_lines) > 2:
            errors.append(f"Card {citem['id']} summary > 2 lines: {b_lines}")
        for line in b_lines[:2]:
            d.text((cx + 2, ty), line, font=f_card_b, fill=INK_BODY)
            ty += 12

        chip_y0 = cy0 + c_h - 14
        if ty > chip_y0:
            errors.append(f"Card {citem['id']} text collides with chips: {ty} > {chip_y0}")
        d.text((cx + 2, chip_y0 + 1), citem["region"].upper(), font=f_card_chip, fill=REGION_COLORS[citem["region"]])
        draw_source_chips(d, cx + c_w - 1, chip_y0, cy0 + c_h - 1, citem["sources"], f_card_chip, citem.get("tag"))

    d.line([(MARGIN, c_top + c_h + 3), (W - MARGIN, c_top + c_h + 3)], fill=RULE, width=1)
    d.line([(MARGIN, c_top + 2 * c_h + c_gap_y + 2), (W - MARGIN, c_top + 2 * c_h + c_gap_y + 2)], fill=INK_DARK, width=2)

    # ── 6. BOTTOM BAND: 22 BRIEFS (LEFT) + MAP & BEATS (RIGHT) (y = 702..944)
    band_top, band_bot = 702, 944
    left_x, left_w = MARGIN, 696
    right_x, right_w = left_x + left_w + 12, CONTENT_W - left_w - 12  # 284

    d.text((left_x, band_top), "ALSO ON SATURDAY 21 NOVEMBER — 22 MORE VERIFIED STORIES", font=f_sec_hdr, fill=INK_DARK)
    d.line([(left_x, band_top + 14), (left_x + left_w, band_top + 14)], fill=INK_DARK, width=1)

    half = len(data["briefs"]) // 2  # 11
    col_bw = (left_w - 12) // 2      # 342
    row_bh = (band_bot - (band_top + 17)) / half  # 20.45
    d.line([(left_x + col_bw + 6, band_top + 17), (left_x + col_bw + 6, band_bot)], fill=RULE, width=1)

    for idx, b in enumerate(data["briefs"]):
        col_i = 0 if idx < half else 1
        row_i = idx if idx < half else idx - half
        bx0 = left_x + col_i * (col_bw + 12)
        ry0 = int(band_top + 17 + row_i * row_bh)
        ry1 = int(band_top + 17 + (row_i + 1) * row_bh)
        if row_i % 2 == 1:
            d.rectangle([bx0, ry0, bx0 + col_bw, ry1], fill=BG_TINT)

        # Region-colored number badge
        d.ellipse([bx0 + 2, ry0 + 2, bx0 + 17, ry0 + 17], fill=REGION_COLORS[b["region"]])
        draw_centered_text(d, bx0 + 2, ry0 + 2, bx0 + 17, ry0 + 17, str(b["id"]), f_br_num, "#FFFFFF")

        # Right-aligned source chip (+ optional CLAIM/REPORTED tag)
        src_left = draw_source_chips(d, bx0 + col_bw - 2, ry0 + 3, ry0 + 16, [b["source"]], f_br_src, b.get("tag"))

        tx = bx0 + 21
        place_s = f"{b['place']}: "
        pw, _ = text_size(d, place_s, f_br_loc)
        d.text((tx, ry0 + 4), place_s, font=f_br_loc, fill=INK_DARK)
        tx += pw

        bw_txt, _ = text_size(d, b["text"], f_br_txt)
        if tx + bw_txt > src_left - 2:
            errors.append(
                f"Brief {b['id']} too wide ({tx + bw_txt} > {src_left - 2}, over by {(tx + bw_txt) - (src_left - 2)}px): {place_s}{b['text']} [{b['source']}]"
            )
        d.text((tx, ry0 + 4), b["text"], font=f_br_txt, fill=INK_BODY)

    # Right Top: Global World Map (all 31 terrestrial stories mapped!)
    d.text((right_x, band_top), "WHERE IT HAPPENED — ALL 33 STORIES", font=f_sec_hdr, fill=INK_DARK)
    d.line([(right_x, band_top + 14), (right_x + right_w, band_top + 14)], fill=INK_DARK, width=1)
    map_y0, map_y1 = band_top + 17, 858
    map_img = draw_world_map(data["hero"] + data["cards"], data["briefs"], right_w, map_y1 - map_y0)
    img.paste(map_img, (right_x, map_y0))
    d.rectangle([right_x, map_y0, right_x + right_w, map_y1], outline=RULE, width=1)

    # Right Bottom: 33 Stories by Beat
    beat_y0, beat_y1 = 864, band_bot
    d.rectangle([right_x, beat_y0, right_x + right_w, beat_y1], fill=BG_CARD, outline=RULE, width=1)
    d.rectangle([right_x, beat_y0, right_x + right_w, beat_y0 + 15], fill=BG_DARK)
    draw_centered_text(d, right_x, beat_y0, right_x + right_w, beat_y0 + 15, "33 STORIES BY BEAT", f_beat_lbl, GOLD)

    beat_counts = Counter(s["beat"] for s in all_stories).most_common()
    max_bc = beat_counts[0][1]
    b_cols = 2
    b_rows = math.ceil(len(beat_counts) / b_cols)
    cell_w = (right_w - 14) // b_cols
    cell_h = (beat_y1 - (beat_y0 + 19)) / b_rows
    for idx, (beat, cnt) in enumerate(beat_counts):
        ci, ri = divmod(idx, b_rows)
        bx0 = right_x + 7 + ci * (cell_w + 4)
        by0 = int(beat_y0 + 19 + ri * cell_h)
        d.text((bx0, by0), beat, font=f_beat_lbl, fill=INK_DARK)
        bar_x0 = bx0 + 54
        bar_max = cell_w - 72
        bar_w = max(8, int(bar_max * cnt / max_bc))
        d.rounded_rectangle([bar_x0, by0 + 2, bar_x0 + bar_w, by0 + 9], radius=2, fill=BEAT_COLORS.get(beat, "#334155"))
        d.text((bar_x0 + bar_w + 4, by0), str(cnt), font=f_beat_cnt, fill=INK_DARK)

    # ── 7. ULTRA-CRISP LIGHT EDITORIAL DATE CHECK PANEL (y = 949..1005) ──
    dc_y0, dc_y1 = 949, 1005
    d.rectangle([MARGIN, dc_y0, W - MARGIN, dc_y1], fill=BG_CARD, outline=BG_DARK, width=2)
    badge_x1 = MARGIN + 104
    d.rectangle([MARGIN, dc_y0, badge_x1, dc_y1], fill=BG_DARK)
    draw_centered_text(d, MARGIN, dc_y0 + 6, badge_x1, dc_y0 + 26, "DATE CHECK", f_dc_badge, GOLD)
    draw_centered_text(d, MARGIN, dc_y0 + 30, badge_x1, dc_y1 - 8, "9 LEFT OFF · 3 AHEAD", f_dc_sub, "#F8FAFC")

    dc_raw = data["date_check_text"]
    split_key = "Still ahead Sunday 22 Nov"
    if split_key in dc_raw:
        part_prev, part_next = dc_raw.split(split_key, 1)
        part_next = split_key + part_next
    else:
        part_prev, part_next = dc_raw, ""

    tx0 = badge_x1 + 10
    max_dc_w = W - MARGIN - tx0 - 8
    prev_lines = wrap_text(d, part_prev.strip(), f_dc_txt, max_dc_w)
    if len(prev_lines) > 3:
        errors.append(f"Date check prev lines > 3: {prev_lines}")
    cy = dc_y0 + 6
    for line in prev_lines[:3]:
        d.text((tx0, cy), line, font=f_dc_txt, fill=INK_DARK)
        cy += 13
    if part_next:
        next_lines = wrap_text(d, part_next.strip(), f_dc_bold, max_dc_w)
        if len(next_lines) > 1:
            errors.append(f"Date check next lines > 1: {next_lines}")
        d.text((tx0, cy + 2), next_lines[0], font=f_dc_bold, fill=ACCENT_RED)
        if cy + 14 > dc_y1:
            errors.append(f"Date check vertical overflow: {cy + 14} > {dc_y1}")

    # ── 8. COLOPHON (y = 1008..1021) ─────────────────────────────────────
    footer = (
        "All 33 stories occurred or broke on Saturday 21 November 2026 (full-day roundup through 00:45 UTC 22 Nov) · "
        "Tags: OFFICIAL = agency/state · REPORTED = single outlet · CLAIM = contested · Original vector art"
    )
    fw, _ = text_size(d, footer, f_footer)
    if fw > CONTENT_W:
        errors.append(f"Footer too wide: {fw} > {CONTENT_W}")
    draw_centered_text(d, MARGIN, 1008, W - MARGIN, 1021, footer, f_footer, INK_MUTED)

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
