#!/usr/bin/env python3
"""Render a visual-first, 300px-legible 1024x1024 world-news front page for Saturday 21 November 2026."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 16
CONTENT_W = W - 2 * MARGIN  # 992

# Palette — warm archival newsprint with dark obsidian & bright gold visual anchors
BG_PAPER = "#FAF7F0"
BG_CARD = "#FFFFFF"
BG_TINT = "#F2EDE3"
BG_DARK = "#111827"
BG_DARK_ALT = "#1E293B"
GOLD = "#FACC15"
GOLD_SOFT = "#FDE047"
INK_DARK = "#0F172A"
INK_BODY = "#1E293B"
INK_MUTED = "#526075"
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
    "CLAIM": "#7E22CE",
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


def draw_art_stamp(
    d: ImageDraw.ImageDraw,
    cw: int,
    item: dict,
    is_hero: bool,
) -> None:
    """High-contrast black title stamp + bright gold sub-ribbon top-left + region number badge top-right."""
    if is_hero:
        f_ban = load_font("narrow_bold", 42)
        f_sub = load_font("narrow_bold", 21)
        pad_x, pad_y = 20, 12
        sub_px, sub_py = 14, 8
        ox, oy = 14, 14
        r_badge = 22
        f_num = load_font("sans_bold", 24)
    else:
        f_ban = load_font("narrow_bold", 26)
        f_sub = load_font("narrow_bold", 15)
        pad_x, pad_y = 12, 7
        sub_px, sub_py = 10, 5
        ox, oy = 8, 8
        r_badge = 15
        f_num = load_font("sans_bold", 17)

    bw, bh = text_size(d, item["banner"], f_ban)
    bx1 = ox + bw + pad_x
    by1 = oy + bh + pad_y
    # Subtle drop shadow
    d.rectangle([ox + 3, oy + 3, bx1 + 3, by1 + 3], fill="#020617")
    d.rectangle([ox, oy, bx1, by1], fill="#0B1120")
    draw_centered_text(d, ox, oy, bx1, by1, item["banner"], f_ban, "#FFFFFF")

    sw, sh = text_size(d, item["sub"], f_sub)
    sy0 = by1 + 2
    sy1 = sy0 + sh + sub_py
    sx1 = ox + sw + sub_px
    d.rectangle([ox + 2, sy0 + 2, sx1 + 2, sy1 + 2], fill="#020617")
    d.rectangle([ox, sy0, sx1, sy1], fill=GOLD)
    draw_centered_text(d, ox, sy0, sx1, sy1, item["sub"], f_sub, "#0F172A")

    # Top-right circular number badge linked to region color & world map
    cx = cw - oy - r_badge
    cy = oy + r_badge
    d.ellipse([cx - r_badge, cy - r_badge, cx + r_badge, cy + r_badge], fill=REGION_COLORS[item["region"]], outline="#FFFFFF", width=4 if is_hero else 3)
    draw_centered_text(d, cx - r_badge, cy - r_badge, cx + r_badge, cy + r_badge, str(item["id"]), f_num, "#FFFFFF")


def draw_hero_panel_art(item: dict, w: int, h: int) -> Image.Image:
    kind = item["art"]

    def _draw(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        if kind == "cop31":
            # Mediterranean Antalya dusk sky shifting from cool teal to tense warm amber
            fill_vgrad(d, 0, 0, cw, ch, "#0E3A53", "#E8A87C")
            # Warm horizon glow right
            d.ellipse([int(cw * 0.44), int(ch * 0.14), int(cw * 0.98), int(ch * 1.15)], fill="#F59E0B")
            d.ellipse([int(cw * 0.52), int(ch * 0.24), int(cw * 0.90), int(ch * 1.02)], fill="#FDE68A")
            # Mediterranean sea band
            fill_vgrad(d, 0, int(ch * 0.72), cw, ch, "#1D4ED8", "#0F294A")
            # Summit dome & Antalya coastal ridge silhouette
            d.polygon([(0, int(ch * 0.78)), (95, int(ch * 0.62)), (200, int(ch * 0.68)), (320, int(ch * 0.78))], fill="#1E293B")
            # UN Pavilion hall center-left
            d.pieslice([130, int(ch * 0.50), 330, int(ch * 0.96)], 180, 360, fill="#F8FAFC", outline="#0F172A", width=4)
            for fx in (152, 186, 220, 254, 288):
                d.line([(fx, int(ch * 0.64)), (fx, int(ch * 0.76))], fill="#475569", width=3)
            # Row of colorful delegate flags
            flag_cols = ["#2563EB", "#16A34A", "#DC2626", "#F59E0B", "#0EA5E9", "#7C3AED"]
            for i, fc in enumerate(flag_cols):
                fx = 44 + i * 32
                d.line([(fx, int(ch * 0.68)), (fx, int(ch * 0.92))], fill="#E2E8F0", width=3)
                d.rectangle([fx, int(ch * 0.68), fx + 20, int(ch * 0.74)], fill=fc)
            # Shaded Earth globe center-right
            gx, gy, gr = int(cw * 0.56), int(ch * 0.53), 66
            d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill="#1D4ED8", outline="#0F172A", width=5)
            d.ellipse([gx - gr + 8, gy - gr + 8, gx + gr - 16, gy + gr - 14], fill="#2563EB")
            # Continents
            d.polygon([(gx - 44, gy - 26), (gx - 12, gy - 42), (gx + 10, gy - 16), (gx - 12, gy + 26), (gx - 38, gy + 12)], fill="#22C55E")
            d.polygon([(gx + 16, gy - 30), (gx + 50, gy - 12), (gx + 38, gy + 24), (gx + 14, gy + 10)], fill="#16A34A")
            d.ellipse([gx - 18, gy + 30, gx + 14, gy + 52], fill="#22C55E")
            # Thermometer in red zone
            tx = int(cw * 0.74)
            d.rounded_rectangle([tx - 13, 56, tx + 13, ch - 52], radius=13, fill="#FFFFFF", outline="#0F172A", width=4)
            d.ellipse([tx - 24, ch - 70, tx + 24, ch - 22], fill="#DC2626", outline="#0F172A", width=4)
            d.rectangle([tx - 7, 82, tx + 7, ch - 44], fill="#DC2626")
            for ty in range(80, ch - 74, 16):
                d.line([(tx + 14, ty), (tx + 24, ty)], fill="#0F172A", width=3)
            # Midnight overtime clock (past 12!)
            kx, ky, kr = int(cw * 0.88), int(ch * 0.62), 46
            d.ellipse([kx - kr, ky - kr, kx + kr, ky + kr], fill="#FFFFFF", outline="#0F172A", width=5)
            # Red overtime wedge (12 to 2 o'clock)
            d.pieslice([kx - kr + 6, ky - kr + 6, kx + kr - 6, ky + kr - 6], 270, 340, fill="#FCA5A5")
            for tick in range(0, 360, 30):
                rad = math.radians(tick)
                d.line(
                    [(kx + int((kr - 10) * math.cos(rad)), ky + int((kr - 10) * math.sin(rad))),
                     (kx + int((kr - 3) * math.cos(rad)), ky + int((kr - 3) * math.sin(rad)))],
                    fill="#0F172A",
                    width=3,
                )
            d.line([(kx, ky), (kx, ky - 28)], fill="#0F172A", width=5)
            d.line([(kx, ky), (kx + 24, ky - 12)], fill="#DC2626", width=5)
            d.ellipse([kx - 6, ky - 6, kx + 6, ky + 6], fill="#0F172A")

        elif kind == "mercury":
            # Deep space gradient + golden solar flare at bottom-left
            fill_vgrad(d, 0, 0, cw, ch, "#030712", "#0F172A")
            # Subtle solar glow bottom-left
            for sr, col in [(130, "#451A03"), (92, "#9A3412"), (58, "#EA580C"), (32, "#FACC15"), (16, "#FEF9C3")]:
                d.ellipse([18 - sr, ch - 10 - sr, 18 + sr, ch - 10 + sr], fill=col)
            # Starfield
            stars = [
                (45, 130, 2), (92, 165, 3), (140, 120, 2), (195, 148, 2), (242, 62, 3),
                (288, 108, 2), (318, 42, 2), (355, 192, 3), (390, 34, 2), (432, 212, 2),
                (260, 205, 2), (168, 198, 2), (590, 214, 3), (618, 165, 2), (336, 152, 2),
            ]
            for sx, sy, sr in stars:
                d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill="#F8FAFC")
            # Back half of cyan orbital capture track
            d.arc([244, 52, 616, 224], 165, 355, fill="#38BDF8", width=4)
            # Huge cratered Mercury globe on right
            mx, my, mr = int(cw * 0.77), int(ch * 0.56), 116
            d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill="#475569", outline="#94A3B8", width=3)
            # Sunlit bronze-silver crescent on left side of Mercury
            d.pieslice([mx - mr + 2, my - mr + 2, mx + mr - 2, my + mr - 2], 100, 265, fill="#B8A99A")
            d.ellipse([mx - mr + 42, my - mr + 8, mx + mr - 8, my + mr - 8], fill="#64748B")
            d.ellipse([mx - mr + 78, my - mr + 16, mx + mr - 2, my + mr - 16], fill="#334155")
            # Detailed craters
            craters = [
                (mx - 62, my - 34, 18), (mx - 44, my + 24, 24), (mx - 82, my + 4, 12),
                (mx - 22, my - 58, 14), (mx - 12, my + 56, 16), (mx + 14, my - 12, 20),
                (mx - 68, my + 54, 11), (mx + 26, my + 38, 13),
            ]
            for cx0, cy0, cr in craters:
                d.ellipse([cx0 - cr, cy0 - cr, cx0 + cr, cy0 + cr], fill="#475569", outline="#CBD5E1", width=2)
                d.ellipse([cx0 - cr + 4, cy0 - cr + 3, cx0 + cr - 2, cy0 + cr - 2], fill="#7C7268" if cx0 < mx - 25 else "#3F4B5B")
            # Front half of orbital capture trajectory
            d.arc([244, 52, 616, 224], 0, 165, fill="#FACC15", width=5)
            # BepiColombo spacecraft gliding along orbit center-left/mid!
            px, py = 330, 146
            # Ion thruster blue plume
            d.polygon([(px - 22, py + 2), (px - 76, py + 16), (px - 68, py + 28)], fill="#38BDF8")
            d.polygon([(px - 22, py + 4), (px - 52, py + 14), (px - 48, py + 20)], fill="#E0F2FE")
            # Solar array wings (angled blue panels with grid lines)
            d.polygon([(px - 10, py - 14), (px + 12, py - 74), (px + 34, py - 68), (px + 10, py - 8)], fill="#1D4ED8", outline="#93C5FD", width=2)
            d.polygon([(px - 12, py + 12), (px - 32, py + 72), (px - 10, py + 78), (px + 10, py + 16)], fill="#1D4ED8", outline="#93C5FD", width=2)
            # Gold foil spacecraft bus + twin Mio sunshield nose
            d.rounded_rectangle([px - 22, py - 16, px + 26, py + 16], radius=6, fill="#F59E0B", outline="#FEF3C7", width=3)
            d.polygon([(px + 26, py - 14), (px + 48, py - 6), (px + 48, py + 6), (px + 26, py + 14)], fill="#E2E8F0", outline="#0F172A", width=2)
            # High-gain dish antenna
            d.arc([px - 6, py - 34, px + 26, py - 8], 180, 360, fill="#F8FAFC", width=4)

        else:  # riyadh
            fill_vgrad(d, 0, 0, cw, ch, "#060D1F", "#172554")
            # Crescent moon & stars
            d.ellipse([272, 26, 304, 58], fill="#FEF08A")
            d.ellipse([282, 22, 314, 54], fill="#0C1736")
            for sx, sy in [(218, 42), (344, 34), (476, 24), (586, 44), (312, 92), (512, 66)]:
                d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill="#E2E8F0")
            # Desert base ground
            d.rectangle([0, ch - 26, cw, ch], fill="#0F172A")
            # Riyadh skyline with iconic Kingdom Centre skybridge & Al Faisaliah spire
            blds = [
                (14, 166, 62), (70, 146, 118), (126, 158, 172), (182, 134, 232),
                (244, 152, 294), (306, 136, 356), (368, 148, 418), (528, 144, 578), (586, 156, 636),
            ]
            for x0, y0, x1 in blds:
                d.rectangle([x0, y0, x1, ch - 26], fill="#1E3A5F", outline="#334155", width=2)
                for wy in range(y0 + 10, ch - 34, 16):
                    for wx in range(x0 + 8, x1 - 8, 14):
                        d.rectangle([wx, wy, wx + 6, wy + 8], fill="#FDE68A" if (wx + wy) % 3 == 0 else "#334155")
            # Iconic Al Faisaliah Pyramid Tower + golden globe
            d.polygon([(388, ch - 26), (414, 108), (440, ch - 26)], fill="#274C77", outline="#60A5FA", width=2)
            d.ellipse([406, 126, 422, 142], fill="#FACC15")
            # Iconic Kingdom Centre Tower with skybridge cutout
            d.rectangle([452, 84, 518, ch - 26], fill="#335C81", outline="#93C5FD", width=2)
            d.ellipse([464, 94, 506, 154], fill="#0E1C3D")
            d.rectangle([460, 84, 510, 96], fill="#E2E8F0")
            # Incoming red missile arcs + blue Patriot interceptors + 3 glowing aerial starbursts
            bursts = [(294, 108), (416, 66), (554, 94)]
            for ix, iy in bursts:
                # Incoming red trail
                d.line([(ix + 96, 4), (ix, iy)], fill="#EF4444", width=5)
                # Patriot blue-white trail from city
                d.line([(ix - 54, ch - 28), (ix, iy)], fill="#38BDF8", width=4)
                # Shockwave ring
                d.ellipse([ix - 30, iy - 30, ix + 30, iy + 30], outline="#FDE047", width=3)
                for ang in range(0, 360, 40):
                    rad = math.radians(ang)
                    d.line([(ix, iy), (ix + int(26 * math.cos(rad)), iy + int(26 * math.sin(rad)))], fill="#F97316", width=5)
                d.ellipse([ix - 13, iy - 13, ix + 13, iy + 13], fill="#FEF9C3")

        draw_art_stamp(d, cw, item, is_hero=True)

    return supersampled(w, h, "#0F172A", _draw)


def draw_card_panel_art(item: dict, w: int, h: int) -> Image.Image:
    kind = item["art"]

    def _draw(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        if kind == "ship":
            # Baltic twilight sky + choppy sea + burning Russian cargo ship
            fill_vgrad(d, 0, 0, cw, int(ch * 0.68), "#1E3A5F", "#64748B")
            fill_vgrad(d, 0, int(ch * 0.68), cw, ch, "#0F294A", "#08172E")
            # Smoke plume billowing upper-right
            for sx, sy, sr, col in [
                (260, 74, 24, "#334155"), (284, 54, 28, "#475569"), (316, 36, 32, "#334155"),
                (348, 22, 34, "#1E293B"), (246, 84, 18, "#475569"),
            ]:
                d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=col)
            # Cargo ship hull (tilted dark red & charcoal)
            d.polygon([(126, 98), (336, 94), (322, 122), (144, 122)], fill="#1E293B", outline="#0F172A", width=3)
            d.polygon([(134, 110), (330, 108), (322, 122), (144, 122)], fill="#991B1B")
            # Aft white bridge superstructure
            d.rectangle([282, 64, 320, 96], fill="#F1F5F9", outline="#0F172A", width=2)
            d.rectangle([290, 70, 314, 78], fill="#38BDF8")
            # Deck containers
            d.rectangle([160, 82, 198, 97], fill="#2563EB", outline="#0F172A", width=2)
            d.rectangle([200, 82, 236, 97], fill="#D97706", outline="#0F172A", width=2)
            # Vivid orange/yellow fire midship
            d.polygon([(226, 98), (242, 56), (256, 80), (268, 48), (282, 98)], fill="#EA580C")
            d.polygon([(236, 98), (248, 68), (260, 84), (268, 66), (276, 98)], fill="#FACC15")
            # Attack drone silhouette swooping in from upper-center
            d.polygon([(186, 36), (214, 46), (198, 52)], fill="#F8FAFC", outline="#0F172A", width=2)
            d.line([(204, 48), (236, 68)], fill="#FDE047", width=2)
            # Small orange rescue boat in water + sea ripples
            d.polygon([(82, 122), (114, 122), (108, 130), (88, 130)], fill="#F97316")
            for wx in (26, 152, 240, 326):
                d.line([(wx, 132), (wx + 34, 132)], fill="#38BDF8", width=2)

        elif kind == "sinaloa":
            # Sierra Madre sunset sky + rugged peaks + tactical searchlight helicopter
            fill_vgrad(d, 0, 0, cw, ch, "#1E1B4B", "#C2410C")
            # Desert mountains
            d.polygon([(0, ch), (72, 74), (156, ch)], fill="#431407")
            d.polygon([(110, ch), (222, 62), (334, ch)], fill="#29120A")
            d.polygon([(256, ch), (344, 78), (cw, ch)], fill="#1C0C08")
            # Searchlight cone from helicopter onto ridge
            d.polygon([(238, 62), (168, ch), (266, ch)], fill="#FEF08A")
            # Dark hill foreground overlay for drama
            d.polygon([(0, ch), (90, 114), (198, 128), (300, 116), (cw, ch)], fill="#0F172A")
            # Police red/blue light flare on road
            d.ellipse([204, 118, 222, 132], fill="#EF4444")
            d.ellipse([222, 118, 240, 132], fill="#3B82F6")
            # Tactical helicopter silhouette centered cleanly away from badge 5
            hx, hy = 248, 56
            d.line([(hx - 54, hy - 14), (hx + 46, hy - 14)], fill="#E2E8F0", width=4)
            d.line([(hx, hy - 14), (hx, hy - 2)], fill="#94A3B8", width=4)
            d.rounded_rectangle([hx - 24, hy - 4, hx + 24, hy + 14], radius=8, fill="#0F172A", outline="#E2E8F0", width=2)
            d.line([(hx + 22, hy + 2), (hx + 58, hy - 2)], fill="#0F172A", width=5)
            d.ellipse([hx + 52, hy - 10, hx + 66, hy + 4], outline="#E2E8F0", width=2)
            d.line([(hx - 18, hy + 20), (hx + 20, hy + 20)], fill="#94A3B8", width=3)

        elif kind == "bahrain":
            # Persian Gulf dusk + industrial plant blaze + crisp bright MQ-9 drone with red reticle
            fill_vgrad(d, 0, 0, cw, int(ch * 0.72), "#1E1B4B", "#9A3412")
            fill_vgrad(d, 0, int(ch * 0.72), cw, ch, "#0F294A", "#091A32")
            # Industrial refinery tanks & towers on right
            d.rectangle([232, 92, 272, 118], fill="#334155", outline="#0F172A", width=2)
            d.rectangle([280, 84, 344, 118], fill="#1E293B", outline="#0F172A", width=2)
            d.rectangle([244, 62, 254, 92], fill="#475569")
            d.rectangle([326, 56, 336, 84], fill="#475569")
            # Smoke + orange flame burst from refinery
            for sx, sy, sr in [(286, 56, 20), (308, 40, 22), (334, 24, 24)]:
                d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill="#1E293B")
            d.polygon([(268, 94), (284, 52), (296, 76), (308, 48), (322, 94)], fill="#EA580C")
            d.polygon([(278, 94), (290, 64), (302, 78), (312, 64), (318, 94)], fill="#FACC15")
            # Crisp bright MQ-9 drone silhouette center-left + bold crimson target reticle
            dx, dy = 148, 80
            d.line([(dx - 64, dy), (dx + 64, dy)], fill="#F1F5F9", width=6)
            d.polygon([(dx - 26, dy - 7), (dx + 34, dy), (dx - 26, dy + 7)], fill="#F8FAFC", outline="#0F172A", width=2)
            d.ellipse([dx - 24, dy - 24, dx + 24, dy + 24], outline="#EF4444", width=4)
            d.line([(dx - 32, dy), (dx - 16, dy)], fill="#EF4444", width=4)
            d.line([(dx + 16, dy), (dx + 32, dy)], fill="#EF4444", width=4)

        elif kind == "quake":
            # Banda Sea teal ocean + Timor island ridge + radiating seismic waves + seismograph
            fill_vgrad(d, 0, 0, cw, int(ch * 0.54), "#FEF3C7", "#FDE68A")
            fill_vgrad(d, 0, int(ch * 0.54), cw, ch, "#0284C7", "#0C4A6E")
            # Timor coastal hills left
            d.polygon([(0, int(ch * 0.62)), (68, int(ch * 0.44)), (144, int(ch * 0.50)), (196, int(ch * 0.62))], fill="#15803D")
            # Concentric crimson shockwaves in Banda Sea right
            ex, ey = 282, 98
            for rr in (20, 38, 56, 74):
                d.ellipse([ex - rr, ey - rr // 2, ex + rr, ey + rr // 2], outline="#EF4444", width=4)
            d.ellipse([ex - 10, ey - 10, ex + 10, ey + 10], fill="#DC2626", outline="#FEF08A", width=3)
            # Bold crimson seismograph spike trace across mid-band
            pts = [
                (12, 88), (112, 88), (138, 84), (156, 98), (174, 62), (192, 118),
                (210, 44), (228, 126), (246, 56), (264, 112), (284, 78), (312, 90), (368, 88),
            ]
            d.line(pts, fill="#B91C1C", width=5)

        elif kind == "plane":
            # Davao night airport runway + Air Niugini 767 safe landing + waiting fire lights
            fill_vgrad(d, 0, 0, cw, int(ch * 0.66), "#0B1530", "#1E3A5F")
            # Runway tarmac
            d.rectangle([0, int(ch * 0.66), cw, ch], fill="#334155")
            # Perspective runway centerline & glowing amber edge lights
            d.line([(16, int(ch * 0.84)), (cw - 16, int(ch * 0.84))], fill="#E2E8F0", width=3)
            for lx in range(28, cw - 20, 46):
                d.ellipse([lx - 4, int(ch * 0.68) - 4, lx + 4, int(ch * 0.68) + 4], fill="#FACC15")
            # Emergency fire-truck strobe lights far-left bottom
            d.rounded_rectangle([32, 102, 76, 120], radius=4, fill="#DC2626", outline="#FFFFFF", width=2)
            d.ellipse([48, 94, 60, 106], fill="#38BDF8")
            # Wide-body Boeing 767 touching down cleanly center-right
            px, py = 232, 82
            # Landing headlight beam
            d.polygon([(px + 68, py + 8), (cw, py + 24), (cw, py + 48)], fill="#FEF08A")
            # Fuselage
            d.polygon([(px - 78, py - 4), (px + 54, py - 10), (px + 84, py + 4), (px + 66, py + 14), (px - 70, py + 12)], fill="#F8FAFC", outline="#0F172A", width=3)
            # Red & gold Air Niugini tail fin
            d.polygon([(px - 76, py - 4), (px - 98, py - 36), (px - 52, py - 36), (px - 44, py - 6)], fill="#DC2626", outline="#0F172A", width=2)
            d.polygon([(px - 80, py - 14), (px - 62, py - 28), (px - 56, py - 12)], fill="#FACC15")
            # Wing & landing wheels
            d.polygon([(px - 16, py + 4), (px + 28, py + 4), (px + 4, py + 24)], fill="#94A3B8", outline="#0F172A", width=2)
            for wx in (px - 12, px + 46):
                d.ellipse([wx - 6, py + 16, wx + 6, py + 28], fill="#0F172A", outline="#E2E8F0", width=2)

        elif kind == "boat":
            # Bayelsa, Nigeria river at dusk — mangrove bank + overturned wooden vessel + ripples
            fill_vgrad(d, 0, 0, cw, int(ch * 0.56), "#134E4A", "#D97706")
            fill_vgrad(d, 0, int(ch * 0.56), cw, ch, "#0F294A", "#082F49")
            # Far riverbank & dark mangrove palm silhouettes
            d.rectangle([0, int(ch * 0.50), cw, int(ch * 0.58)], fill="#064E3B")
            for px in (242, 274, 314, 348):
                d.line([(px, int(ch * 0.54)), (px + 4, int(ch * 0.30))], fill="#022C22", width=4)
                for ang in (-140, -100, -50, -10, 20):
                    rad = math.radians(ang)
                    d.line([(px + 4, int(ch * 0.30)), (px + 4 + int(22 * math.cos(rad)), int(ch * 0.30) + int(16 * math.sin(rad)))], fill="#022C22", width=3)
            # Overturned wooden boat hull center-right with sunlit warm timber highlight
            bx, by = 222, 102
            d.pieslice([bx - 84, by - 32, bx + 84, by + 34], 188, 352, fill="#B45309", outline="#FEF3C7", width=3)
            d.arc([bx - 74, by - 24, bx + 74, by + 24], 195, 345, fill="#F59E0B", width=5)
            d.line([(bx - 64, by - 12), (bx + 62, by - 14)], fill="#78350F", width=4)
            # Bright white-cyan water foam & orange rescue lifebuoy
            for rx, ry, rw in [(114, 108, 72), (198, 114, 104), (268, 106, 68), (160, 126, 94)]:
                d.line([(rx, ry), (rx + rw, ry)], fill="#BAE6FD", width=4)
            d.ellipse([306, 98, 336, 124], outline="#F97316", width=7)

        elif kind == "fbi":
            # Cyber investigation grid + server towers with breach alert + golden microchip
            fill_vgrad(d, 0, 0, cw, ch, "#090D1A", "#172554")
            # Subtle cyber matrix grid lines
            for gy in range(20, ch, 24):
                d.line([(0, gy), (cw, gy)], fill="#1E293B", width=1)
            for gx in range(24, cw, 32):
                d.line([(gx, 0), (gx, ch)], fill="#1E293B", width=1)
            # Server rack tower center
            d.rounded_rectangle([146, 50, 232, 134], radius=6, fill="#1E293B", outline="#60A5FA", width=3)
            for ry in (62, 82, 102, 120):
                d.rectangle([156, ry, 222, ry + 10], fill="#0F172A")
                d.ellipse([162, ry + 2, 170, ry + 8], fill="#EF4444" if ry != 102 else "#22C55E")
                d.rectangle([176, ry + 3, 214, ry + 7], fill="#38BDF8")
            # Breached crimson padlock overlay
            d.arc([204, 42, 236, 76], 180, 360, fill="#FCA5A5", width=5)
            d.rounded_rectangle([198, 60, 242, 92], radius=5, fill="#DC2626", outline="#FFFFFF", width=2)
            d.ellipse([215, 70, 225, 80], fill="#FEF08A")
            # Nvidia / SEC silicon chip on right
            cx0, cy0 = 278, 68
            d.rounded_rectangle([cx0, cy0, cx0 + 62, cy0 + 58], radius=6, fill="#064E3B", outline="#22C55E", width=4)
            d.rectangle([cx0 + 14, cy0 + 14, cx0 + 48, cy0 + 44], fill="#10B981", outline="#FACC15", width=2)
            for pin in range(cx0 + 10, cx0 + 56, 12):
                d.line([(pin, cy0 - 10), (pin, cy0)], fill="#FACC15", width=3)
                d.line([(pin, cy0 + 58), (pin, cy0 + 68)], fill="#FACC15", width=3)

        elif kind == "bitcoin":
            # Dark crypto terminal + red plunge to $55.8k + bright emerald rebound past $60k + gold coin
            fill_vgrad(d, 0, 0, cw, ch, "#090D16", "#111827")
            for gy in (44, 78, 112):
                d.line([(12, gy), (cw - 12, gy)], fill="#1F2937", width=2)
            # Red drop leg
            red_pts = [(16, 78), (64, 86), (112, 74), (160, 102), (206, 124)]
            d.line(red_pts, fill="#EF4444", width=6)
            # Green V-rebound leg
            grn_pts = [(206, 124), (242, 106), (274, 112), (314, 84), (364, 62)]
            d.line(grn_pts, fill="#22C55E", width=6)
            # Trough highlight dot
            d.ellipse([198, 116, 214, 132], fill="#EF4444", outline="#FFFFFF", width=3)
            # Gleaming golden Bitcoin coin with generous clearance from badge 11
            bx, by, br = 286, 56, 30
            d.ellipse([bx - br, by - br, bx + br, by + br], fill="#F59E0B", outline="#FEF08A", width=4)
            d.ellipse([bx - br + 6, by - br + 6, bx + br - 6, by + br - 6], outline="#B45309", width=2)
            bf = load_font("sans_bold", 34)
            draw_centered_text(d, bx - br, by - br, bx + br, by + br, "B", bf, "#FFFFFF")

        elif kind == "cricket":
            # Wellington Basin Reserve sunlit emerald outfield + central pitch + stumps + red ball
            fill_vgrad(d, 0, 0, cw, 34, "#38BDF8", "#BAE6FD")
            d.rectangle([0, 34, cw, ch], fill="#15803D")
            # Mowed grass stripes
            for gx in range(0, cw, 44):
                d.rectangle([gx, 34, gx + 22, ch], fill="#16A34A")
            # Sandy central cricket pitch in perspective
            d.polygon([(176, 34), (248, 34), (288, ch), (136, ch)], fill="#E5D5A8", outline="#FFFFFF", width=2)
            d.line([(160, 110), (264, 110)], fill="#FFFFFF", width=3)
            # Wooden 3 stumps + bails
            sx = 212
            for ox in (-13, 0, 13):
                d.line([(sx + ox, 46), (sx + ox, 114)], fill="#92400E", width=6)
            d.line([(sx - 17, 46), (sx + 17, 46)], fill="#F59E0B", width=5)
            # Cricket bat & gleaming red leather ball right
            d.polygon([(276, 46), (294, 42), (314, 108), (292, 114)], fill="#FDE68A", outline="#78350F", width=3)
            d.ellipse([312, 62, 346, 96], fill="#B91C1C", outline="#FFFFFF", width=3)
            d.arc([314, 64, 344, 94], 20, 160, fill="#FEF3C7", width=2)
            # Crisp India & NZ mini flags bottom-left
            d.rectangle([16, 100, 64, 110], fill="#F97316")
            d.rectangle([16, 110, 64, 120], fill="#FFFFFF")
            d.rectangle([16, 120, 64, 130], fill="#16A34A")
            d.rectangle([72, 100, 120, 130], fill="#1E3A8A")
            d.line([(72, 108), (94, 108)], fill="#DC2626", width=3)
            d.line([(83, 100), (83, 116)], fill="#DC2626", width=3)
            for rx0, ry0 in [(106, 106), (112, 114), (102, 116), (106, 124)]:
                d.ellipse([rx0 - 2, ry0 - 2, rx0 + 2, ry0 + 2], fill="#EF4444")

        else:  # tennis (Turin ATP Finals blue indoor court)
            fill_vgrad(d, 0, 0, cw, ch, "#090D1A", "#1E293B")
            # Arena spotlight beams
            d.polygon([(200, 0), (124, ch), (242, ch)], fill="#172554")
            d.polygon([(310, 0), (240, ch), (366, ch)], fill="#172554")
            # Perspective royal-blue Turin indoor hard court
            d.polygon([(92, 54), (350, 54), (cw - 8, ch - 6), (22, ch - 6)], fill="#1D4ED8", outline="#FFFFFF", width=4)
            # Inner court service lines
            d.line([(134, 54), (82, ch - 6)], fill="#FFFFFF", width=3)
            d.line([(308, 54), (322, ch - 6)], fill="#FFFFFF", width=3)
            d.line([(106, 98), (336, 98)], fill="#FFFFFF", width=3)
            d.line([(212, 68), (206, ch - 6)], fill="#FFFFFF", width=3)
            # White net stretching across center
            d.rectangle([62, 74, 360, 90], fill="#E2E8F0", outline="#0F172A", width=2)
            for nx in range(74, 356, 18):
                d.line([(nx, 74), (nx, 90)], fill="#94A3B8", width=1)
            # Glowing optic-yellow tennis ball + sweeping motion arc
            d.arc([168, 32, 316, 112], 190, 340, fill="#FDE047", width=4)
            tx, ty, tr = 304, 54, 18
            d.ellipse([tx - tr, ty - tr, tx + tr, ty + tr], fill="#BEF264", outline="#15803D", width=3)
            d.arc([tx - 12, ty - 14, tx + 4, ty + 14], 290, 70, fill="#FFFFFF", width=3)
            d.arc([tx - 4, ty - 14, tx + 12, ty + 14], 110, 250, fill="#FFFFFF", width=3)

        draw_art_stamp(d, cw, item, is_hero=False)

    return supersampled(w, h, "#0F172A", _draw)


def draw_world_map(lead_stories: list[dict], w: int, h: int) -> Image.Image:
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
        y = (76.0 - lat) / 138.0 * (ch - 26) + 10
        return x, y

    def _draw(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        fill_vgrad(d, 0, 0, cw, ch, "#D8E7F3", "#C5DCF0")
        for lat in (-30, 0, 30, 60):
            _, gy = proj(lat, 0, cw, ch)
            d.line([(0, int(gy)), (cw, int(gy))], fill="#B5D0E6", width=2)
        for poly in continents:
            pts = [proj(lat, lon, cw, ch) for lon, lat in poly]
            d.polygon(pts, fill="#F3EFE6", outline="#94A3B8")

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
                n["y"] = max(20.0, min(ch - 36.0, n["y"]))

        pin_font = load_font("sans_bold", 19)
        for n in nodes:
            px, py = int(n["x"]), int(n["y"])
            r = 15
            d.ellipse([px - r, py - r, px + r, py + r], fill=REGION_COLORS[n["region"]], outline="#FFFFFF", width=3)
            draw_centered_text(d, px - r, py - r, px + r, py + r, str(n["id"]), pin_font, "#FFFFFF")

        # Clean bottom-left legend pill for non-terrestrial/global stories
        f_off = load_font("sans_bold", 15)
        off_txt = "Off map: #2 Mercury · #11 Bitcoin"
        ow, oh = text_size(d, off_txt, f_off)
        d.rounded_rectangle([8, ch - oh - 14, 8 + ow + 16, ch - 6], radius=6, fill="#0F172A")
        draw_centered_text(d, 8, ch - oh - 14, 8 + ow + 16, ch - 6, off_txt, f_off, "#F8FAFC")

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
    """Draw right-aligned outlined source chips (+ optional status tag) and return leftmost x used."""
    cur_x = right_x
    for src in reversed(sources):
        tw, _ = text_size(d, src, font)
        w_chip = tw + 8
        x0 = cur_x - w_chip
        d.rounded_rectangle([x0, y0, cur_x, y1], radius=2, fill="#F8FAFC", outline="#94A3B8", width=1)
        draw_centered_text(d, x0, y0, cur_x, y1, src, font, "#334155")
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

    # Fonts
    f_eyebrow = load_font("sans_bold", 9)
    f_mast = load_font("narrow_bold", 62)
    f_deck = load_font("serif_italic", 11)
    f_stat_val = load_font("narrow_bold", 26)
    f_stat_lbl = load_font("sans", 9)
    f_stat_ref = load_font("sans_bold", 8)
    f_reg = load_font("sans_bold", 10)

    f_hero_k = load_font("sans_bold", 9)
    f_hero_h = load_font("serif_bold", 16)
    f_hero_b = load_font("sans", 10)
    f_chip = load_font("sans_bold", 8)

    f_card_h = load_font("serif_bold", 12)
    f_card_b = load_font("sans", 9)
    f_card_chip = load_font("sans_bold", 7)

    f_sec_hdr = load_font("sans_bold", 10)
    f_br_num = load_font("sans_bold", 8)
    f_br_loc = load_font("sans_bold", 9)
    f_br_txt = load_font("sans", 9)
    f_br_src = load_font("sans_bold", 7)

    f_beat_lbl = load_font("sans_bold", 8)
    f_beat_cnt = load_font("sans_bold", 8)

    f_dc_badge = load_font("narrow_bold", 14)
    f_dc_txt = load_font("sans", 9)
    f_dc_bold = load_font("sans_bold", 9)
    f_footer = load_font("sans", 8)

    # ── 1. GIANT FULL-WIDTH MASTHEAD (y = 4..84) ──────────────────────────
    d.rectangle([MARGIN, 4, W - MARGIN, 7], fill=BG_DARK)
    d.text((MARGIN, 9), "WORLD EDITION · FULL-DAY ROUNDUP", font=f_eyebrow, fill=ACCENT_RED)
    right_tag = f"{len(all_stories)} VERIFIED STORIES · 7 REGIONS · EVERY ONE DATED 21 NOV 2026"
    rw, _ = text_size(d, right_tag, f_eyebrow)
    d.text((W - MARGIN - rw, 9), right_tag, font=f_eyebrow, fill=INK_BODY)

    # Full-width bold condensed date masthead
    mw, mh = text_size(d, data["date_label"], f_mast)
    if mw > CONTENT_W:
        errors.append(f"Masthead too wide: {mw} > {CONTENT_W}")
    draw_centered_text(d, MARGIN, 23, W - MARGIN, 67, data["date_label"], f_mast, INK_DARK)

    dw, _ = text_size(d, data["deck"], f_deck)
    if dw > CONTENT_W:
        errors.append(f"Deck too wide: {dw} > {CONTENT_W}")
    draw_centered_text(d, MARGIN, 69, W - MARGIN, 83, data["deck"], f_deck, INK_BODY)

    # ── 2. DARK CHARCOAL & BRIGHT GOLD STAT BAR (y = 86..135) ────────────
    stat_y0, stat_y1 = 86, 135
    d.rectangle([MARGIN, stat_y0, W - MARGIN, stat_y1], fill=BG_DARK)
    d.rectangle([MARGIN, stat_y0, W - MARGIN, stat_y0 + 3], fill=GOLD)
    stats = data["stats"]
    col_w = CONTENT_W / len(stats)
    for i, st in enumerate(stats):
        sx0 = int(MARGIN + i * col_w)
        sx1 = int(MARGIN + (i + 1) * col_w)
        if i > 0:
            d.line([(sx0, stat_y0 + 7), (sx0, stat_y1 - 6)], fill="#334155", width=1)
        # Bright gold headline figure
        d.text((sx0 + 9, stat_y0 + 5), st["value"], font=f_stat_val, fill=GOLD)
        # Small story reference pill top-right
        ref_s = f"#{st['ref']}"
        rfw, _ = text_size(d, ref_s, f_stat_ref)
        d.text((sx1 - rfw - 8, stat_y0 + 10), ref_s, font=f_stat_ref, fill="#94A3B8")
        # Crisp white 1-line (or 2-line) caption
        lbl_lines = wrap_text(d, st["label"], f_stat_lbl, sx1 - sx0 - 16)
        if len(lbl_lines) > 2:
            errors.append(f"Stat {st['value']} label > 2 lines: {lbl_lines}")
        start_y = stat_y0 + (34 if len(lbl_lines) == 1 else 30)
        for li, line in enumerate(lbl_lines[:2]):
            d.text((sx0 + 9, start_y + li * 9), line, font=f_stat_lbl, fill="#E2E8F0")

    # ── 3. PROPORTIONAL 7-REGION BAR (y = 139..156) ──────────────────────
    reg_order = ["Europe", "Middle East", "Americas", "Africa", "Asia", "Global", "Oceania"]
    reg_short = {"Middle East": "Mid East"}
    counts = {r: sum(1 for s in all_stories if s["region"] == r) for r in reg_order}
    total = sum(counts.values())
    rx = MARGIN
    for idx, r in enumerate(reg_order):
        cnt = counts[r]
        seg_w = (W - MARGIN - rx) if idx == len(reg_order) - 1 else round(CONTENT_W * cnt / total)
        d.rectangle([rx, 139, rx + seg_w - 2, 156], fill=REGION_COLORS[r])
        lbl = f"{reg_short.get(r, r)} {cnt}"
        draw_centered_text(d, rx, 139, rx + seg_w - 2, 156, lbl, f_reg, "#FFFFFF")
        rx += seg_w

    # ── 4. THREE TALL ILLUSTRATED HERO PANELS (y = 161..392) ─────────────
    hero_y, hero_h = 161, 231
    hero_gap = 10
    hero_w = (CONTENT_W - 2 * hero_gap) // 3  # 324
    for i, hitem in enumerate(data["hero"]):
        hx = MARGIN + i * (hero_w + hero_gap)
        d.rectangle([hx, hero_y, hx + hero_w, hero_y + hero_h], fill=BG_CARD, outline=RULE, width=1)
        art_h = 122
        art = draw_hero_panel_art(hitem, hero_w - 2, art_h)
        img.paste(art, (hx + 1, hero_y + 1))

        # Kicker + source chips row
        ky = hero_y + art_h + 5
        d.text((hx + 9, ky + 1), hitem["kicker"], font=f_hero_k, fill=REGION_COLORS[hitem["region"]])
        draw_source_chips(d, hx + hero_w - 8, ky, ky + 13, hitem["sources"], f_chip, hitem.get("tag"))

        # Headline
        cy = ky + 16
        h_lines = wrap_text(d, hitem["headline"], f_hero_h, hero_w - 18)
        if len(h_lines) > 2:
            errors.append(f"Hero {hitem['id']} headline > 2 lines: {h_lines}")
        for line in h_lines[:2]:
            d.text((hx + 9, cy), line, font=f_hero_h, fill=INK_DARK)
            cy += 18
        cy += 3

        # Summary
        b_lines = wrap_text(d, hitem["summary"], f_hero_b, hero_w - 18)
        if len(b_lines) > 4:
            errors.append(f"Hero {hitem['id']} summary > 4 lines: {b_lines}")
        for line in b_lines[:4]:
            d.text((hx + 9, cy), line, font=f_hero_b, fill=INK_BODY)
            cy += 12
        if cy > hero_y + hero_h - 2:
            errors.append(f"Hero {hitem['id']} vertical overflow: {cy} > {hero_y + hero_h - 2}")

    # ── 5. TEN ILLUSTRATED STORY CARDS (2 rows x 5 cols, y = 398..690) ───
    c_top = 398
    c_gap_x, c_gap_y = 8, 8
    c_w = (CONTENT_W - 4 * c_gap_x) // 5  # 192 exact!
    c_h = 142
    for idx, citem in enumerate(data["cards"]):
        row, col = divmod(idx, 5)
        cx = MARGIN + col * (c_w + c_gap_x)
        cy0 = c_top + row * (c_h + c_gap_y)
        d.rectangle([cx, cy0, cx + c_w, cy0 + c_h], fill=BG_CARD, outline=RULE, width=1)

        art_h = 70
        art = draw_card_panel_art(citem, c_w - 2, art_h)
        img.paste(art, (cx + 1, cy0 + 1))

        # Headline (up to 2 lines)
        ty = cy0 + art_h + 3
        h_lines = wrap_text(d, citem["headline"], f_card_h, c_w - 12)
        if len(h_lines) > 2:
            errors.append(f"Card {citem['id']} headline > 2 lines: {h_lines}")
        for line in h_lines[:2]:
            d.text((cx + 6, ty), line, font=f_card_h, fill=INK_DARK)
            ty += 14
        ty += 1

        # Summary (up to 2 lines)
        b_lines = wrap_text(d, citem["summary"], f_card_b, c_w - 12)
        if len(b_lines) > 2:
            errors.append(f"Card {citem['id']} summary > 2 lines: {b_lines}")
        for line in b_lines[:2]:
            d.text((cx + 6, ty), line, font=f_card_b, fill=INK_BODY)
            ty += 11

        # Bottom source chip + optional tag bar
        chip_y0 = cy0 + c_h - 15
        if ty > chip_y0 - 1:
            errors.append(f"Card {citem['id']} text collides with chips: {ty} > {chip_y0 - 1}")
        d.text((cx + 6, chip_y0 + 1), citem["region"].upper(), font=f_card_chip, fill=REGION_COLORS[citem["region"]])
        draw_source_chips(d, cx + c_w - 6, chip_y0, cy0 + c_h - 3, citem["sources"], f_card_chip, citem.get("tag"))

    # ── 6. BOTTOM BAND: 20 BRIEFS (LEFT) + MAP & BEATS (RIGHT) (y = 696..936)
    band_top, band_bot = 696, 936
    left_x, left_w = MARGIN, 694
    right_x, right_w = left_x + left_w + 12, CONTENT_W - left_w - 12  # 286

    # Left: 20 Briefs in 2 crisp columns (10 rows x 2 cols)
    d.text((left_x, band_top), "ALSO ON SATURDAY 21 NOVEMBER — 20 MORE VERIFIED STORIES", font=f_sec_hdr, fill=INK_DARK)
    d.line([(left_x, band_top + 14), (left_x + left_w, band_top + 14)], fill=INK_DARK, width=2)

    half = len(data["briefs"]) // 2
    col_bw = (left_w - 12) // 2  # 341
    row_bh = (band_bot - (band_top + 18)) / half  # 22.2
    d.line([(left_x + col_bw + 6, band_top + 18), (left_x + col_bw + 6, band_bot)], fill=RULE, width=1)

    for idx, b in enumerate(data["briefs"]):
        col_i = 0 if idx < half else 1
        row_i = idx if idx < half else idx - half
        bx0 = left_x + col_i * (col_bw + 12)
        ry0 = int(band_top + 18 + row_i * row_bh)
        ry1 = int(band_top + 18 + (row_i + 1) * row_bh)
        if row_i % 2 == 1:
            d.rectangle([bx0, ry0, bx0 + col_bw, ry1], fill=BG_TINT)

        # Region-colored circular number badge
        d.ellipse([bx0 + 2, ry0 + 3, bx0 + 17, ry0 + 18], fill=REGION_COLORS[b["region"]])
        draw_centered_text(d, bx0 + 2, ry0 + 3, bx0 + 17, ry0 + 18, str(b["id"]), f_br_num, "#FFFFFF")

        # Right-aligned outlined source chip first so we know exact max width for text
        src_left = draw_source_chips(d, bx0 + col_bw - 2, ry0 + 4, ry0 + 17, [b["source"]], f_br_src)

        tx = bx0 + 21
        place_s = f"{b['place']}: "
        pw, _ = text_size(d, place_s, f_br_loc)
        d.text((tx, ry0 + 5), place_s, font=f_br_loc, fill=INK_DARK)
        tx += pw

        bw_txt, _ = text_size(d, b["text"], f_br_txt)
        if tx + bw_txt > src_left - 2:
            errors.append(
                f"Brief {b['id']} too wide ({tx + bw_txt} > {src_left - 2}, over by {(tx + bw_txt) - (src_left - 2)}px): {place_s}{b['text']} [{b['source']}]"
            )
        d.text((tx, ry0 + 5), b["text"], font=f_br_txt, fill=INK_BODY)

    # Right Top: Clean 11-Pin World Map
    d.text((right_x, band_top), "WHERE IT HAPPENED — LEADS 1–13", font=f_sec_hdr, fill=INK_DARK)
    d.line([(right_x, band_top + 14), (right_x + right_w, band_top + 14)], fill=INK_DARK, width=2)
    map_y0, map_y1 = band_top + 18, 852
    map_img = draw_world_map(data["hero"] + data["cards"], right_w, map_y1 - map_y0)
    img.paste(map_img, (right_x, map_y0))
    d.rectangle([right_x, map_y0, right_x + right_w, map_y1], outline=RULE, width=1)

    # Right Bottom: Story Breakdown by Beat (computed dynamically from all 33 stories)
    beat_y0, beat_y1 = 858, band_bot
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
        d.text((bx0, by0), beat, font=f_beat_lbl, fill=INK_BODY)
        bar_x0 = bx0 + 54
        bar_max = cell_w - 72
        bar_w = max(8, int(bar_max * cnt / max_bc))
        d.rounded_rectangle([bar_x0, by0 + 2, bar_x0 + bar_w, by0 + 9], radius=2, fill=BEAT_COLORS.get(beat, "#334155"))
        d.text((bar_x0 + bar_w + 4, by0), str(cnt), font=f_beat_cnt, fill=INK_DARK)

    # ── 7. BOLD DARK/GOLD DATE CHECK FOOTER (y = 942..1004) ──────────────
    dc_y0, dc_y1 = 942, 1004
    d.rectangle([MARGIN, dc_y0, W - MARGIN, dc_y1], fill=BG_DARK)
    d.rectangle([MARGIN, dc_y0, MARGIN + 5, dc_y1], fill=GOLD)

    # Left vertical gold badge
    badge_x0, badge_x1 = MARGIN + 12, MARGIN + 96
    d.rounded_rectangle([badge_x0, dc_y0 + 10, badge_x1, dc_y1 - 10], radius=4, fill=GOLD)
    draw_centered_text(d, badge_x0, dc_y0 + 12, badge_x1, dc_y0 + 30, "DATE", f_dc_badge, INK_DARK)
    draw_centered_text(d, badge_x0, dc_y0 + 29, badge_x1, dc_y1 - 12, "CHECK", f_dc_badge, INK_DARK)

    # Split date_check_text into earlier exclusions vs Sunday 22 Nov ahead
    dc_raw = data["date_check_text"]
    split_key = "Still ahead Sunday 22 Nov"
    if split_key in dc_raw:
        part_prev, part_next = dc_raw.split(split_key, 1)
        part_next = split_key + part_next
    else:
        part_prev, part_next = dc_raw, ""

    tx0 = badge_x1 + 12
    max_dc_w = W - MARGIN - tx0 - 10
    prev_lines = wrap_text(d, part_prev.strip(), f_dc_txt, max_dc_w)
    if len(prev_lines) > 3:
        errors.append(f"Date check prev lines > 3: {prev_lines}")
    cy = dc_y0 + 10
    for line in prev_lines[:3]:
        d.text((tx0, cy), line, font=f_dc_txt, fill="#E2E8F0")
        cy += 14
    if part_next:
        next_lines = wrap_text(d, part_next.strip(), f_dc_bold, max_dc_w)
        if len(next_lines) > 1:
            errors.append(f"Date check next lines > 1: {next_lines}")
        d.text((tx0, cy + 3), next_lines[0], font=f_dc_bold, fill=GOLD_SOFT)
        if cy + 15 > dc_y1:
            errors.append(f"Date check vertical overflow: {cy + 15} > {dc_y1}")

    # ── 8. COLOPHON (y = 1007..1021) ─────────────────────────────────────
    footer = (
        "All 33 stories occurred or broke on Saturday 21 November 2026 (full-day roundup through 00:45 UTC 22 Nov) · "
        "Tags: OFFICIAL = agency/state · REPORTED = single outlet · CLAIM = contested · Original vector art"
    )
    fw, _ = text_size(d, footer, f_footer)
    if fw > CONTENT_W:
        errors.append(f"Footer too wide: {fw} > {CONTENT_W}")
    draw_centered_text(d, MARGIN, 1007, W - MARGIN, 1021, footer, f_footer, INK_MUTED)

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
