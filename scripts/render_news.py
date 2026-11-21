#!/usr/bin/env python3
"""Render a 1024x1024 broadsheet world-news summary PNG for 21 November 2026."""

from __future__ import annotations

import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 16
CONTENT_W = W - 2 * MARGIN

BG_PAPER = "#FBF9F4"
BG_CARD = "#FFFFFF"
BG_TINT = "#F4F1EA"
BG_DATE_CHECK = "#FEF2F2"
INK_DARK = "#0F172A"
INK_BODY = "#334155"
INK_MUTED = "#64748B"
RULE = "#CBD5E1"
ACCENT_RED = "#B91C1C"
ACCENT_NAVY = "#1E3A5F"

REGION_COLORS = {
    "Europe": "#1D4ED8",
    "Americas": "#7C3AED",
    "Asia": "#B91C1C",
    "Middle East": "#B45309",
    "Africa": "#0F766E",
    "Oceania": "#0369A1",
    "Global": "#334155",
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


def load_font(kind: str, size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_CANDIDATES[kind]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0], box[3] - box[1]


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


def draw_pill(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    label: str,
    font: ImageFont.ImageFont,
    bg: str,
    fg: str = "#FFFFFF",
    px: int = 6,
    py: int = 2,
    radius: int = 3,
) -> tuple[int, int]:
    tw, th = text_size(draw, label, font)
    pw = tw + 2 * px
    ph = th + 2 * py + 2
    draw.rounded_rectangle([x, y, x + pw, y + ph], radius=radius, fill=bg)
    draw.text((x + px, y + py - 1), label, font=font, fill=fg)
    return pw, ph


def supersampled(w: int, h: int, bg: str, fn) -> Image.Image:
    scale = 2
    im = Image.new("RGB", (w * scale, h * scale), bg)
    d = ImageDraw.Draw(im)
    fn(d, w * scale, h * scale)
    return im.resize((w, h), Image.Resampling.LANCZOS)


def draw_hero_art(kind: str, w: int, h: int) -> Image.Image:
    def _cop31(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        for y in range(ch):
            t = y / max(1, ch - 1)
            r = int(22 + 30 * t)
            g = int(52 + 45 * t)
            b = int(88 + 40 * (1 - t))
            d.line([(0, y), (cw, y)], fill=(r, g, b))
        cx, cy, rad = int(cw * 0.42), int(ch * 0.52), int(ch * 0.36)
        d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill="#1D6FA5", outline="#93C5FD", width=4)
        d.polygon([(cx - 48, cy - 30), (cx - 12, cy - 52), (cx + 10, cy - 18), (cx - 16, cy + 28), (cx - 44, cy + 10)], fill="#34D399")
        d.polygon([(cx + 18, cy - 38), (cx + 55, cy - 22), (cx + 46, cy + 22), (cx + 12, cy + 12)], fill="#34D399")
        d.arc([cx - rad - 14, cy - rad - 14, cx + rad + 14, cy + rad + 14], 295, 65, fill="#F97316", width=8)
        tx = int(cw * 0.66)
        d.rounded_rectangle([tx - 10, 26, tx + 10, ch - 46], radius=10, fill="#F8FAFC", outline="#CBD5E1", width=3)
        d.ellipse([tx - 20, ch - 60, tx + 20, ch - 20], fill="#DC2626", outline="#F8FAFC", width=3)
        d.rectangle([tx - 5, 58, tx + 5, ch - 38], fill="#DC2626")
        kx, ky, kr = int(cw * 0.84), int(ch * 0.34), 34
        d.ellipse([kx - kr, ky - kr, kx + kr, ky + kr], fill="#FEF3C7", outline="#F59E0B", width=5)
        d.line([(kx, ky), (kx, ky - 20)], fill="#B45309", width=5)
        d.line([(kx, ky), (kx + 18, ky + 6)], fill="#DC2626", width=5)

    def _bepicolombo(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        d.rectangle([0, 0, cw, ch], fill="#090D1A")
        stars = [(40, 28), (110, 44), (170, 22), (245, 70), (310, 32), (390, 50), (470, 24), (540, 62), (610, 36), (130, 150), (340, 172), (510, 155), (585, 130)]
        for sx, sy in stars:
            d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill="#E2E8F0")
        d.ellipse([-80, ch // 2 - 90, 80, ch // 2 + 90], fill="#F59E0B")
        d.ellipse([-60, ch // 2 - 70, 56, ch // 2 + 70], fill="#FDE047")
        d.arc([int(cw * 0.36), -40, int(cw * 0.98), ch + 40], 110, 250, fill="#38BDF8", width=4)
        mx, my, mr = int(cw * 0.72), int(ch * 0.52), int(ch * 0.36)
        d.ellipse([mx - mr, my - mr, mx + mr, my + mr], fill="#94A3B8", outline="#CBD5E1", width=3)
        for cx0, cy0, cr0 in [(mx - 24, my - 18, 12), (mx + 22, my - 22, 9), (mx + 10, my + 24, 15), (mx - 30, my + 20, 8)]:
            d.ellipse([cx0 - cr0, cy0 - cr0, cx0 + cr0, cy0 + cr0], fill="#64748B")
        px, py = int(cw * 0.41), int(ch * 0.47)
        d.polygon([(px - 52, py + 8), (px - 18, py - 2), (px - 18, py + 12)], fill="#38BDF8")
        d.rectangle([px - 18, py - 14, px + 18, py + 14], fill="#F8FAFC", outline="#475569", width=3)
        d.rectangle([px + 18, py - 10, px + 38, py + 10], fill="#CBD5E1", outline="#475569", width=2)
        d.rectangle([px - 10, py - 58, px + 10, py - 14], fill="#1D4ED8", outline="#93C5FD", width=2)
        d.rectangle([px - 10, py + 14, px + 10, py + 58], fill="#1D4ED8", outline="#93C5FD", width=2)

    def _riyadh(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        d.rectangle([0, 0, cw, ch], fill="#0F172A")
        buildings = [(20, 148, 60, ch), (68, 126, 114, ch), (122, 138, 170, ch), (180, 96, 226, ch), (236, 134, 290, ch), (300, 110, 344, ch), (356, 140, 412, ch), (422, 118, 476, ch), (486, 144, 548, ch), (558, 124, 628, ch)]
        for x0, y0, x1, y1 in buildings:
            d.rectangle([x0, y0, x1, y1], fill="#1E293B")
            for wy in range(y0 + 10, y1 - 8, 16):
                for wx in range(x0 + 8, x1 - 8, 14):
                    d.rectangle([wx, wy, wx + 6, wy + 8], fill="#FDE68A" if (wx + wy) % 3 == 0 else "#334155")
        intercepts = [(185, 58), (330, 44), (475, 64)]
        for ix, iy in intercepts:
            d.line([(ix - 90, 8), (ix, iy)], fill="#EF4444", width=5)
            d.line([(ix + 40, 140), (ix, iy)], fill="#38BDF8", width=4)
            for ang in range(0, 360, 45):
                rad = math.radians(ang)
                d.line([(ix, iy), (ix + int(24 * math.cos(rad)), iy + int(24 * math.sin(rad)))], fill="#FBBF24", width=4)
            d.ellipse([ix - 10, iy - 10, ix + 10, iy + 10], fill="#FEF08A")

    fn = {"cop31": _cop31, "bepicolombo": _bepicolombo, "riyadh": _riyadh}[kind]
    return supersampled(w, h, "#0F172A", fn)


def draw_card_art(kind: str, w: int, h: int) -> Image.Image:
    def _nato(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        d.rectangle([0, 0, cw, ch], fill="#1E3A8A")
        cx, cy = cw // 2, ch // 2
        r = 34
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline="#E2E8F0", width=3)
        d.polygon([(cx, cy - 38), (cx + 10, cy - 10), (cx + 38, cy), (cx + 10, cy + 10), (cx, cy + 38), (cx - 10, cy + 10), (cx - 38, cy), (cx - 10, cy - 10)], fill="#FFFFFF")
        for sx in (-120, 120):
            d.polygon([(cx + sx, cy - 18), (cx + sx + 28, cy + 14), (cx + sx - 28, cy + 14)], fill="#93C5FD")

    def _plastic(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        d.rectangle([0, 0, cw, ch], fill="#065F46")
        cx, cy = int(cw * 0.44), ch // 2
        for i in range(12):
            ang = math.radians(i * 30)
            sx, sy = cx + int(24 * math.cos(ang)), cy + int(24 * math.sin(ang))
            d.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill="#FACC15")
        bx, by = int(cw * 0.76), ch // 2
        d.rounded_rectangle([bx - 13, by - 18, bx + 13, by + 22], radius=5, fill="#BAE6FD")
        d.rectangle([bx - 7, by - 26, bx + 7, by - 18], fill="#E0F2FE")
        d.ellipse([bx - 28, by - 28, bx + 28, by + 28], outline="#EF4444", width=6)
        d.line([(bx - 20, by - 20), (bx + 20, by + 20)], fill="#EF4444", width=6)

    def _ukraine(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        d.rectangle([0, 0, cw, ch // 2], fill="#1D4ED8")
        d.rectangle([0, ch // 2, cw, ch], fill="#EAB308")
        px = int(cw * 0.34)
        d.polygon([(px, 14), (px - 26, ch - 12), (px + 26, ch - 12)], outline="#0F172A", width=5)
        d.line([(px - 36, 36), (px + 36, 36)], fill="#0F172A", width=5)
        bx = int(cw * 0.68)
        d.polygon([(bx + 10, 14), (bx - 14, 52), (bx + 4, 52), (bx - 12, 88), (bx + 22, 44), (bx + 2, 44)], fill="#F8FAFC", outline="#0F172A", width=3)

    def _defense(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        d.rectangle([0, 0, cw // 2, ch], fill="#F8FAFC")
        d.rectangle([cw // 2, 0, cw, ch], fill="#FFEDD5")
        d.ellipse([int(cw * 0.22) - 24, ch // 2 - 24, int(cw * 0.22) + 24, ch // 2 + 24], fill="#DC2626")
        d.ellipse([int(cw * 0.78) - 24, ch // 2 - 24, int(cw * 0.78) + 24, ch // 2 + 24], fill="#16A34A", outline="#1E3A8A", width=4)
        d.arc([int(cw * 0.22), 18, int(cw * 0.78), ch + 40], 195, 345, fill="#0F172A", width=5)

    def _chips(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        d.rectangle([0, 0, cw, ch], fill="#312E81")
        cx, cy = cw // 2, ch // 2
        for dx in range(-44, 48, 14):
            d.line([(cx + dx, cy - 38), (cx + dx, cy + 38)], fill="#FBBF24", width=4)
        for dy in range(-28, 32, 14):
            d.line([(cx - 56, cy + dy), (cx + 56, cy + dy)], fill="#FBBF24", width=4)
        d.rounded_rectangle([cx - 38, cy - 26, cx + 38, cy + 26], radius=6, fill="#1E293B", outline="#38BDF8", width=4)
        d.rectangle([cx - 18, cy - 12, cx + 18, cy + 12], fill="#10B981")

    def _diplomacy(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        d.rectangle([0, 0, cw, ch], fill="#0F766E")
        for bx, col in [(int(cw * 0.42), "#FDE68A"), (int(cw * 0.80), "#CBD5E1")]:
            d.rectangle([bx - 30, 26, bx + 30, ch - 8], fill=col)
            d.polygon([(bx - 36, 26), (bx, 10), (bx + 36, 26)], fill="#1E293B")
            for wx in (-16, 0, 16):
                d.rectangle([bx + wx - 4, 38, bx + wx + 4, 54], fill="#0F172A")
        mx = int(cw * 0.61)
        d.line([(mx - 18, 20), (mx + 18, ch - 14)], fill="#EF4444", width=7)
        d.line([(mx + 18, 20), (mx - 18, ch - 14)], fill="#EF4444", width=7)

    def _cricket(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        d.rectangle([0, 0, cw, ch], fill="#15803D")
        d.rectangle([int(cw * 0.44), 0, int(cw * 0.68), ch], fill="#D6C79C")
        sx = int(cw * 0.56)
        for ox in (-12, 0, 12):
            d.line([(sx + ox, 18), (sx + ox, 68)], fill="#FEF3C7", width=4)
        d.line([(sx - 14, 18), (sx + 14, 18)], fill="#F59E0B", width=4)
        d.ellipse([int(cw * 0.78) - 13, ch // 2 - 13, int(cw * 0.78) + 13, ch // 2 + 13], fill="#B91C1C", outline="#FFFFFF", width=2)

    def _football(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        d.rectangle([0, 0, cw, ch], fill="#064E3B")
        cx = int(cw * 0.62)
        d.line([(cx, 0), (cx, ch)], fill="#34D399", width=3)
        d.ellipse([cx - 32, ch // 2 - 32, cx + 32, ch // 2 + 32], outline="#34D399", width=3)
        cy, r = ch // 2, 23
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#FFFFFF", outline="#0F172A", width=3)
        d.polygon([(cx, cy - 9), (cx + 9, cy - 3), (cx + 5, cy + 8), (cx - 5, cy + 8), (cx - 9, cy - 3)], fill="#0F172A")

    fn = {
        "nato": _nato,
        "plastic": _plastic,
        "ukraine": _ukraine,
        "defense": _defense,
        "chips": _chips,
        "diplomacy": _diplomacy,
        "cricket": _cricket,
        "football": _football,
    }[kind]
    return supersampled(w, h, "#1E293B", fn)


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

    def proj(lat: float, lon: float, cw: int, ch: int) -> tuple[int, int]:
        x = int((lon + 150.0) / 345.0 * (cw - 20) + 10)
        y = int((76.0 - lat) / 138.0 * (ch - 18) + 8)
        return x, y

    def _draw(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        d.rectangle([0, 0, cw, ch], fill="#1B365D")
        for lat in (-30, 0, 30, 60):
            _, gy = proj(lat, 0, cw, ch)
            d.line([(0, gy), (cw, gy)], fill="#274978", width=2)
        for poly in continents:
            pts = [proj(lat, lon, cw, ch) for lon, lat in poly]
            d.polygon(pts, fill="#E5DEC9", outline="#94A3B8")
        pin_font = load_font("sans_bold", 17)
        # Deterministic custom nudges for dense European/Middle East cluster
        nudges = {4: (10, -14), 5: (-12, -10), 6: (18, 2), 1: (-6, 8), 3: (12, 10), 9: (10, 6), 11: (-10, 4)}
        for s in stories:
            if s.get("lat") is None:
                continue
            px, py = proj(s["lat"], s["lon"], cw, ch)
            dx, dy = nudges.get(s["id"], (0, 0))
            px += dx
            py += dy
            r = 12
            d.ellipse([px - r, py - r, px + r, py + r], fill="#B91C1C", outline="#FFFFFF", width=3)
            txt = str(s["id"])
            tw, th = text_size(d, txt, pin_font)
            d.text((px - tw // 2, py - th // 2 - 2), txt, font=pin_font, fill="#FFFFFF")

    return supersampled(w, h, "#1B365D", _draw)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    data = json.loads((root / "news" / "stories.json").read_text(encoding="utf-8"))

    img = Image.new("RGB", (W, H), BG_PAPER)
    d = ImageDraw.Draw(img)

    f_mast = load_font("serif_bold", 46)
    f_deck = load_font("serif_italic", 11)
    f_kicker_top = load_font("sans_bold", 10)
    f_stat_val = load_font("serif_bold", 21)
    f_stat_lbl = load_font("sans", 10)
    f_reg = load_font("sans_bold", 10)
    f_pill = load_font("sans_bold", 9)
    f_hero_k = load_font("sans_bold", 9)
    f_hero_h = load_font("serif_bold", 15)
    f_hero_b = load_font("sans", 11)
    f_hero_s = load_font("serif_italic", 10)
    f_card_k = load_font("sans_bold", 8)
    f_card_h = load_font("serif_bold", 12)
    f_card_b = load_font("sans", 10)
    f_card_s = load_font("serif_italic", 9)
    f_sec_hdr = load_font("sans_bold", 10)
    f_brief_num = load_font("sans_bold", 9)
    f_brief_loc = load_font("narrow_bold", 11)
    f_brief_txt = load_font("narrow", 11)
    f_brief_src = load_font("serif_italic", 9)
    f_dc_txt = load_font("narrow", 11)
    f_footer = load_font("sans", 10)

    # 1. Masthead (y = 8..104)
    d.line([(MARGIN, 8), (W - MARGIN, 8)], fill=ACCENT_NAVY, width=2)
    d.line([(MARGIN, 12), (W - MARGIN, 12)], fill=RULE, width=1)
    d.text((MARGIN, 16), data["edition_kicker"], font=f_kicker_top, fill=ACCENT_RED)
    all_stories = data["hero"] + data["cards"] + data["briefs"]
    right_tag = f"{len(all_stories)} VERIFIED STORIES · 7 REGIONS · EVERY ONE DATED 21 NOV 2026"
    rw, _ = text_size(d, right_tag, f_kicker_top)
    d.text((W - MARGIN - rw, 16), right_tag, font=f_kicker_top, fill=INK_BODY)

    mw, _ = text_size(d, data["date_label"], f_mast)
    d.text(((W - mw) // 2, 30), data["date_label"], font=f_mast, fill=INK_DARK)

    dw, _ = text_size(d, data["deck"], f_deck)
    d.text(((W - dw) // 2, 83), data["deck"], font=f_deck, fill=INK_BODY)
    d.line([(MARGIN, 101), (W - MARGIN, 101)], fill=INK_DARK, width=1)

    # 2. Key Numbers Strip (y = 104..148)
    stats = data["stats"]
    col_w = CONTENT_W // len(stats)
    for i, st in enumerate(stats):
        sx = MARGIN + i * col_w
        if i > 0:
            d.line([(sx, 107), (sx, 145)], fill=RULE, width=1)
        d.text((sx + 8, 105), st["value"], font=f_stat_val, fill=ACCENT_NAVY)
        lbl_lines = wrap_text(d, st["label"], f_stat_lbl, col_w - 14)
        for li, line in enumerate(lbl_lines[:2]):
            d.text((sx + 8, 129 + li * 11), line, font=f_stat_lbl, fill=INK_BODY)

    # 3. Region Bar (y = 154..172)
    reg_order = ["Europe", "Americas", "Asia", "Middle East", "Africa", "Oceania", "Global"]
    reg_short = {"Middle East": "Mid East"}
    counts = {r: sum(1 for s in all_stories if s["region"] == r) for r in reg_order}
    total = sum(counts.values())
    rx = MARGIN
    for idx, r in enumerate(reg_order):
        cnt = counts[r]
        seg_w = (W - MARGIN - rx) if idx == len(reg_order) - 1 else round(CONTENT_W * cnt / total)
        d.rectangle([rx, 154, rx + seg_w - 1, 171], fill=REGION_COLORS[r])
        lbl = f"{reg_short.get(r, r)} {cnt}"
        lw, lh = text_size(d, lbl, f_reg)
        d.text((rx + (seg_w - lw) // 2, 154 + (17 - lh) // 2 - 1), lbl, font=f_reg, fill="#FFFFFF")
        rx += seg_w

    # 4. Three Hero Lead Cards (y = 178..394)
    hero_y, hero_h = 178, 216
    hero_gap = 10
    hero_w = (CONTENT_W - 2 * hero_gap) // 3
    for i, hitem in enumerate(data["hero"]):
        hx = MARGIN + i * (hero_w + hero_gap)
        d.rectangle([hx, hero_y, hx + hero_w, hero_y + hero_h], fill=BG_CARD, outline=RULE, width=1)
        art_h = 92
        art = draw_hero_art(hitem["art"], hero_w - 2, art_h)
        img.paste(art, (hx + 1, hero_y + 1))
        draw_pill(d, hx + 8, hero_y + art_h - 21, hitem["tag"], f_pill, ACCENT_RED)
        d.text((hx + 9, hero_y + art_h + 5), hitem["kicker"], font=f_hero_k, fill=REGION_COLORS[hitem["region"]])
        cy = hero_y + art_h + 18
        for line in wrap_text(d, hitem["headline"], f_hero_h, hero_w - 18)[:2]:
            d.text((hx + 9, cy), line, font=f_hero_h, fill=INK_DARK)
            cy += 18
        cy += 3
        sum_lines = wrap_text(d, hitem["summary"], f_hero_b, hero_w - 18)
        assert len(sum_lines) <= 3, f"Hero {hitem['id']} summary overflow: {sum_lines}"
        for line in sum_lines:
            d.text((hx + 9, cy), line, font=f_hero_b, fill=INK_BODY)
            cy += 13
        src_y = hero_y + hero_h - 15
        assert cy <= src_y - 2, f"Hero {hitem['id']} overlaps source line"
        d.text((hx + 9, src_y), f"Sources: {hitem['sources']}", font=f_hero_s, fill=INK_MUTED)

    # 5. Eight Secondary Cards (2 rows x 4 cols, y = 400..692)
    c_top = 400
    c_gap_x, c_gap_y = 8, 8
    c_w = (CONTENT_W - 3 * c_gap_x) // 4
    c_h = 142
    for idx, citem in enumerate(data["cards"]):
        row, col = divmod(idx, 4)
        cx = MARGIN + col * (c_w + c_gap_x)
        cy0 = c_top + row * (c_h + c_gap_y)
        d.rectangle([cx, cy0, cx + c_w, cy0 + c_h], fill=BG_CARD, outline=RULE, width=1)
        art_h = 40
        art = draw_card_art(citem["art"], c_w - 2, art_h)
        img.paste(art, (cx + 1, cy0 + 1))
        draw_pill(d, cx + 6, cy0 + art_h - 17, citem["tag"], f_pill, REGION_COLORS[citem["region"]], px=5, py=1)
        d.text((cx + 7, cy0 + art_h + 4), citem["kicker"], font=f_card_k, fill=REGION_COLORS[citem["region"]])
        ty = cy0 + art_h + 15
        h_lines = wrap_text(d, citem["headline"], f_card_h, c_w - 14)
        assert len(h_lines) <= 2, f"Card {citem['id']} headline overflow: {h_lines}"
        for line in h_lines:
            d.text((cx + 7, ty), line, font=f_card_h, fill=INK_DARK)
            ty += 14
        ty += 3
        b_lines = wrap_text(d, citem["summary"], f_card_b, c_w - 14)
        assert len(b_lines) <= 3, f"Card {citem['id']} summary overflow: {b_lines}"
        for line in b_lines:
            d.text((cx + 7, ty), line, font=f_card_b, fill=INK_BODY)
            ty += 12
        src_y = cy0 + c_h - 14
        assert ty <= src_y - 2, f"Card {citem['id']} text ({ty}) collides with source ({src_y})"
        d.text((cx + 7, src_y), f"{citem['sources']}", font=f_card_s, fill=INK_MUTED)

    # 6. Bottom Editorial Band (y = 698..996)
    left_x, left_w = MARGIN, 332
    right_x, right_w = left_x + left_w + 10, CONTENT_W - left_w - 10

    d.rectangle([left_x, 698, left_x + left_w, 716], fill=ACCENT_NAVY)
    d.text((left_x + 8, 701), "WHERE IT HAPPENED (PINS 1, 3–11)", font=f_sec_hdr, fill="#FFFFFF")
    map_img = draw_world_map(data["hero"] + data["cards"], left_w, 138)
    img.paste(map_img, (left_x, 716))
    draw_pill(d, left_x + 6, 834, "Pin 2: Mercury orbit", f_pill, "#0F172A", "#E2E8F0", px=5, py=1)

    d.rectangle([left_x, 860, left_x + left_w, 996], fill=BG_DATE_CHECK, outline=ACCENT_RED, width=2)
    d.rectangle([left_x, 860, left_x + left_w, 879], fill=ACCENT_RED)
    d.text((left_x + 8, 863), "DATE CHECK — EXCLUDED (19–20 NOV)", font=f_sec_hdr, fill="#FFFFFF")
    for idx, ex in enumerate(data["excluded"]):
        ey = 885 + idx * 18
        line = f"×  {ex}"
        ew, _ = text_size(d, line, f_dc_txt)
        assert ew <= left_w - 14, f"Excluded line too wide ({ew}>{left_w-14}): {line}"
        d.text((left_x + 7, ey), line, font=f_dc_txt, fill="#7F1D1D")

    d.rectangle([right_x, 698, right_x + right_w, 718], fill=ACCENT_NAVY)
    d.text((right_x + 10, 702), "ALSO ON SATURDAY 21 NOVEMBER — 15 MORE VERIFIED STORIES", font=f_sec_hdr, fill="#FFFFFF")
    d.rectangle([right_x, 718, right_x + right_w, 996], fill=BG_CARD, outline=RULE, width=1)
    row_h = (996 - 718) / len(data["briefs"])
    for idx, b in enumerate(data["briefs"]):
        ry0 = int(718 + idx * row_h)
        ry1 = int(718 + (idx + 1) * row_h)
        if idx % 2 == 1:
            d.rectangle([right_x + 1, ry0, right_x + right_w - 1, ry1], fill=BG_TINT)
        bx = right_x + 6
        d.rounded_rectangle([bx, ry0 + 3, bx + 18, ry0 + 15], radius=2, fill=REGION_COLORS[b["region"]])
        nw, _ = text_size(d, str(b["id"]), f_brief_num)
        d.text((bx + (18 - nw) // 2, ry0 + 3), str(b["id"]), font=f_brief_num, fill="#FFFFFF")
        tx = bx + 24
        place_str = f"{b['place']} — "
        pw, _ = text_size(d, place_str, f_brief_loc)
        d.text((tx, ry0 + 3), place_str, font=f_brief_loc, fill=INK_DARK)
        tx += pw
        body_str = f"{b['text']} "
        bw, _ = text_size(d, body_str, f_brief_txt)
        d.text((tx, ry0 + 3), body_str, font=f_brief_txt, fill=INK_BODY)
        tx += bw
        src_str = f"({b['source']})"
        sw, _ = text_size(d, src_str, f_brief_src)
        assert tx + sw <= right_x + right_w - 6, f"Brief {b['id']} overflow: {place_str}{body_str}{src_str}"
        d.text((tx, ry0 + 4), src_str, font=f_brief_src, fill=INK_MUTED)

    # 7. Footer (y = 1002..1020)
    d.line([(MARGIN, 1001), (W - MARGIN, 1001)], fill=RULE, width=1)
    footer = "Every story happened or was first reported on Saturday 21 November 2026 in at least one time zone · Sources attributed · Original vector artwork"
    fw, _ = text_size(d, footer, f_footer)
    d.text(((W - fw) // 2, 1005), footer, font=f_footer, fill=INK_MUTED)

    out_path = root / "entry.png"
    img.save(out_path, format="PNG", optimize=True)
    preview = img.resize((300, 300), Image.Resampling.LANCZOS)
    preview.save(root.parent / "preview_300.png", format="PNG")
    print(f"Saved {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
