#!/usr/bin/env python3
"""Render an airy, 300px-legible 1024x1024 world-news front page for Saturday 21 November 2026."""

from __future__ import annotations

import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 16
CONTENT_W = W - 2 * MARGIN

BG_PAPER = "#FAF7F0"
BG_CARD = "#FFFFFF"
BG_TINT = "#F2EDE3"
BG_DATE_CHECK = "#FEF2F2"
INK_DARK = "#0F172A"
INK_BODY = "#273449"
INK_MUTED = "#5A677A"
RULE = "#D4CEC2"
ACCENT_RED = "#B91C1C"
ACCENT_NAVY = "#1E3A5F"

REGION_COLORS = {
    "Europe": "#1D4ED8",
    "Americas": "#6D28D9",
    "Asia": "#B91C1C",
    "Middle East": "#B45309",
    "Africa": "#0F766E",
    "Oceania": "#0369A1",
    "Global": "#334155",
}

STATUS_COLORS = {
    "CONFIRMED": "#15803D",
    "OFFICIAL": "#1E3A5F",
    "REPORTED": "#B45309",
    "CLAIM": "#7E22CE",
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


def supersampled(w: int, h: int, bg: str, fn) -> Image.Image:
    scale = 2
    im = Image.new("RGB", (w * scale, h * scale), bg)
    d = ImageDraw.Draw(im)
    fn(d, w * scale, h * scale)
    return im.resize((w, h), Image.Resampling.LANCZOS)


def draw_hero_panel_art(item: dict, w: int, h: int) -> Image.Image:
    kind = item["art"]

    def _draw(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        if kind == "cop31":
            d.rectangle([0, 0, cw, ch], fill="#DCEEE8")
            d.rectangle([int(cw * 0.62), 0, cw, ch], fill="#F5E6CC")
            cx, cy, r = int(cw * 0.50), int(ch * 0.68), 64
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#2563EB", outline="#0F172A", width=5)
            d.polygon([(cx - 38, cy - 22), (cx - 10, cy - 42), (cx + 12, cy - 16), (cx - 12, cy + 26), (cx - 36, cy + 10)], fill="#22C55E")
            d.polygon([(cx + 16, cy - 30), (cx + 48, cy - 14), (cx + 38, cy + 22), (cx + 12, cy + 12)], fill="#22C55E")
            tx = int(cw * 0.72)
            d.rounded_rectangle([tx - 12, 48, tx + 12, ch - 52], radius=12, fill="#FFFFFF", outline="#0F172A", width=4)
            d.ellipse([tx - 22, ch - 68, tx + 22, ch - 24], fill="#DC2626", outline="#0F172A", width=4)
            d.rectangle([tx - 6, 86, tx + 6, ch - 42], fill="#DC2626")
            kx, ky, kr = int(cw * 0.88), int(ch * 0.64), 40
            d.ellipse([kx - kr, ky - kr, kx + kr, ky + kr], fill="#FFFFFF", outline="#0F172A", width=5)
            d.line([(kx, ky), (kx, ky - 24)], fill="#0F172A", width=5)
            d.line([(kx, ky), (kx + 20, ky + 8)], fill="#DC2626", width=5)
            d.ellipse([kx - 5, ky - 5, kx + 5, ky + 5], fill="#0F172A")
        elif kind == "riyadh":
            d.rectangle([0, 0, cw, ch], fill="#0B162C")
            d.rectangle([0, ch - 26, cw, ch], fill="#1E293B")
            blds = [
                (16, 152, 62), (70, 134, 118), (128, 146, 174), (186, 118, 240),
                (252, 142, 306), (318, 126, 368), (382, 144, 434), (446, 98, 514),
                (526, 136, 578), (586, 148, 634),
            ]
            for x0, y0, x1 in blds:
                d.rectangle([x0, y0, x1, ch - 26], fill="#1E3A5F")
                for wy in range(y0 + 10, ch - 34, 16):
                    for wx in range(x0 + 8, x1 - 8, 14):
                        d.rectangle([wx, wy, wx + 6, wy + 8], fill="#FDE68A" if (wx + wy) % 3 == 0 else "#334155")
            d.ellipse([462, 106, 498, 142], fill="#0B162C")
            for ix, iy in [(290, 94), (410, 64), (555, 88)]:
                d.line([(ix + 95, 6), (ix, iy)], fill="#EF4444", width=5)
                d.line([(ix - 50, ch - 30), (ix, iy)], fill="#38BDF8", width=4)
                for ang in range(0, 360, 45):
                    rad = math.radians(ang)
                    d.line([(ix, iy), (ix + int(28 * math.cos(rad)), iy + int(28 * math.sin(rad)))], fill="#F59E0B", width=5)
                d.ellipse([ix - 12, iy - 12, ix + 12, iy + 12], fill="#FEF08A")
        else:
            d.rectangle([0, 0, cw, ch], fill="#F6EFE2")
            d.rectangle([0, int(ch * 0.68), cw, ch], fill="#1D4ED8")
            ex, ey = int(cw * 0.72), int(ch * 0.76)
            for rr in (26, 52, 78, 104):
                d.ellipse([ex - rr, ey - rr // 2, ex + rr, ey + rr // 2], outline="#EF4444", width=4)
            d.ellipse([ex - 10, ey - 10, ex + 10, ey + 10], fill="#DC2626", outline="#FFFFFF", width=3)
            d.polygon([(30, int(ch * 0.68)), (110, int(ch * 0.56)), (220, int(ch * 0.60)), (290, int(ch * 0.68))], fill="#92400E")
            pts = [
                (16, 148), (180, 148), (245, 144), (285, 152), (318, 130), (344, 168),
                (372, 94), (398, 182), (426, 58), (456, 184), (486, 76), (514, 168),
                (544, 114), (576, 150), (608, 144), (636, 148),
            ]
            d.line(pts, fill="#B91C1C", width=6)

        f_ban = load_font("sans_bold", 40)
        f_sub = load_font("sans_bold", 22)
        f_cred = load_font("sans_bold", 18)

        bw, bh = text_size(d, item["banner"], f_ban)
        b_y1 = 14 + bh + 20
        d.rectangle([14, 14, 14 + bw + 28, b_y1], fill="#B91C1C")
        draw_centered_text(d, 14, 14, 14 + bw + 28, b_y1, item["banner"], f_ban, "#FFFFFF")

        sw, sh = text_size(d, item["sub"], f_sub)
        sy = b_y1 + 8
        sy1 = sy + sh + 16
        d.rectangle([14, sy, 14 + sw + 24, sy1], fill="#FFFFFF", outline="#0F172A", width=2)
        draw_centered_text(d, 14, sy, 14 + sw + 24, sy1, item["sub"], f_sub, "#0F172A")

        crw, crh = text_size(d, item["credit"], f_cred)
        cy0 = ch - crh - 16
        d.rectangle([0, cy0, crw + 24, ch], fill="#0F172A")
        draw_centered_text(d, 0, cy0, crw + 24, ch, item["credit"], f_cred, "#F8FAFC")

    return supersampled(w, h, "#0F172A", _draw)


def draw_card_panel_art(item: dict, w: int, h: int) -> Image.Image:
    kind = item["art"]
    stamp_bg = "#B91C1C" if kind in ("peru", "kyiv", "drone", "bitcoin", "plane") else "#1E3A5F"

    def _draw(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        mid_y = ch // 2
        if kind == "peru":
            d.rectangle([0, 0, cw, ch], fill="#F5EDE0")
            # Andes peaks + village roofs + red seismic waveform
            d.polygon([(0, ch), (110, 36), (220, ch)], fill="#B08968")
            d.polygon([(140, ch), (275, 22), (410, ch)], fill="#9C6644")
            d.polygon([(310, ch), (430, 44), (cw, ch)], fill="#B08968")
            pts = [(16, 76), (170, 76), (220, 72), (260, 88), (290, 44), (320, 102), (350, 34), (380, 96), (410, 62), (468, 76)]
            d.line(pts, fill="#B91C1C", width=6)
        elif kind == "kyiv":
            d.rectangle([0, 0, cw, ch // 2], fill="#1D4ED8")
            d.rectangle([0, ch // 2, cw, ch], fill="#FACC15")
            # Broadcast mic + Kyiv skyline silhouette right
            mx = int(cw * 0.66)
            d.rounded_rectangle([mx - 14, 24, mx + 14, 68], radius=12, fill="#0F172A")
            d.line([(mx, 68), (mx, 98)], fill="#0F172A", width=6)
            d.arc([mx + 18, 24, mx + 54, 68], 300, 60, fill="#0F172A", width=5)
            d.arc([mx + 30, 16, mx + 76, 76], 300, 60, fill="#0F172A", width=5)
        elif kind == "drone":
            d.rectangle([0, 0, cw, ch], fill="#DBEAFE")
            d.rectangle([0, ch - 24, cw, ch], fill="#1D4ED8")
            # Iran & US flags right-top + Reaper drone silhouette below
            d.rectangle([cw - 142, 12, cw - 86, 22], fill="#16A34A")
            d.rectangle([cw - 142, 22, cw - 86, 32], fill="#FFFFFF")
            d.rectangle([cw - 142, 32, cw - 86, 42], fill="#DC2626")
            d.ellipse([cw - 118, 23, cw - 110, 31], fill="#DC2626")
            for si in range(6):
                d.rectangle([cw - 74, 12 + si * 5, cw - 18, 17 + si * 5], fill="#B91C1C" if si % 2 == 0 else "#FFFFFF")
            d.rectangle([cw - 74, 12, cw - 48, 27], fill="#1E3A8A")
            dx, dy = int(cw * 0.56), 72
            d.line([(dx - 82, dy), (dx + 82, dy)], fill="#0F172A", width=7)
            d.polygon([(dx - 28, dy - 8), (dx + 38, dy), (dx - 28, dy + 8)], fill="#334155")
            d.ellipse([dx - 16, dy - 18, dx + 18, dy + 16], outline="#DC2626", width=5)
        elif kind == "robots":
            d.rectangle([0, 0, cw, ch], fill="#E0F2FE")
            ux, uy, ur = int(cw * 0.44), 68, 30
            d.ellipse([ux - ur, uy - ur, ux + ur, uy + ur], fill="#0284C7", outline="#FFFFFF", width=4)
            d.ellipse([ux - 16, uy - 16, ux + 16, uy + 16], outline="#FFFFFF", width=3)
            rx, ry = int(cw * 0.74), 64
            d.rounded_rectangle([rx - 28, ry - 24, rx + 28, ry + 24], radius=8, fill="#334155", outline="#0F172A", width=4)
            d.ellipse([rx - 17, ry - 8, rx - 5, ry + 4], fill="#EF4444")
            d.ellipse([rx + 5, ry - 8, rx + 17, ry + 4], fill="#EF4444")
            d.line([(rx, ry - 36), (rx, ry - 24)], fill="#0F172A", width=5)
        elif kind == "plane":
            d.rectangle([0, 0, cw, ch], fill="#BAE6FD")
            d.rectangle([0, ch - 26, cw, ch], fill="#475569")
            d.line([(20, ch - 13), (cw - 20, ch - 13)], fill="#E2E8F0", width=3)
            px, py = int(cw * 0.58), 64
            d.polygon([(px - 74, py), (px + 66, py - 8), (px + 88, py + 6), (px - 66, py + 12)], fill="#FFFFFF", outline="#0F172A", width=4)
            d.polygon([(px - 72, py), (px - 90, py - 26), (px - 48, py - 2)], fill="#DC2626")
            d.polygon([(px - 12, py + 4), (px + 26, py + 4), (px + 6, py + 24)], fill="#94A3B8")
        elif kind == "bitcoin":
            d.rectangle([0, 0, cw, ch], fill="#111827")
            pts = [(16, 56), (90, 62), (145, 54), (210, 74), (275, 68), (340, 96), (400, 102), (464, 92)]
            d.line(pts, fill="#EF4444", width=6)
            bx, by, br = int(cw * 0.76), 54, 34
            d.ellipse([bx - br, by - br, bx + br, by + br], fill="#F59E0B", outline="#FEF3C7", width=4)
            bf = load_font("sans_bold", 40)
            draw_centered_text(d, bx - br, by - br, bx + br, by + br, "B", bf, "#FFFFFF")
        elif kind == "cricket":
            d.rectangle([0, 0, cw, ch], fill="#15803D")
            d.rectangle([int(cw * 0.44), 0, int(cw * 0.68), ch], fill="#E5D5A8")
            # India & NZ flags on right/bottom-left
            d.rectangle([16, 64, 68, 76], fill="#F97316")
            d.rectangle([16, 76, 68, 88], fill="#FFFFFF")
            d.rectangle([16, 88, 68, 100], fill="#16A34A")
            d.ellipse([38, 78, 46, 86], outline="#1E3A8A", width=2)
            d.rectangle([78, 64, 130, 100], fill="#1E3A8A")
            d.line([(78, 73), (104, 73)], fill="#DC2626", width=3)
            d.line([(91, 64), (91, 82)], fill="#DC2626", width=3)
            for sx0, sy_off in [(116, 70), (123, 79), (111, 81), (116, 92)]:
                d.ellipse([sx0 - 2, sy_off - 2, sx0 + 2, sy_off + 2], fill="#EF4444")
            sx = int(cw * 0.56)
            for ox in (-12, 0, 12):
                d.line([(sx + ox, 26), (sx + ox, 98)], fill="#92400E", width=5)
            d.line([(sx - 15, 26), (sx + 15, 26)], fill="#F59E0B", width=5)
            d.ellipse([int(cw * 0.78) - 16, mid_y - 16, int(cw * 0.78) + 16, mid_y + 16], fill="#B91C1C", outline="#FFFFFF", width=3)
        else:  # f1
            d.rectangle([0, 0, cw, ch], fill="#111827")
            for r in range(3):
                for c in range(4):
                    col = "#FFFFFF" if (r + c) % 2 == 0 else "#0F172A"
                    d.rectangle([cw - 76 + c * 16, 10 + r * 16, cw - 60 + c * 16, 26 + r * 16], fill=col)
            fx, fy = int(cw * 0.48), 72
            d.rounded_rectangle([fx - 68, fy - 14, fx + 64, fy + 12], radius=10, fill="#1E3A8A", outline="#FACC15", width=4)
            d.rectangle([fx + 46, fy - 18, fx + 74, fy + 14], fill="#EF4444")
            d.ellipse([fx - 54, fy + 2, fx - 28, fy + 28], fill="#0F172A", outline="#E2E8F0", width=4)
            d.ellipse([fx + 24, fy + 2, fx + 50, fy + 28], fill="#0F172A", outline="#E2E8F0", width=4)

        # Compact high-contrast top-left title stamp (huge at 300px without smothering art!)
        f_ban = load_font("sans_bold", 28)
        bw, bh = text_size(d, item["banner"], f_ban)
        bx1 = 10 + bw + 22
        by1 = 10 + bh + 14
        d.rectangle([10, 10, bx1, by1], fill=stamp_bg)
        draw_centered_text(d, 10, 10, bx1, by1, item["banner"], f_ban, "#FFFFFF")

        # Bottom-right crisp credit pill
        f_cred = load_font("sans_bold", 16)
        crw, crh = text_size(d, item["credit"], f_cred)
        cx0 = cw - crw - 18
        cy0 = ch - crh - 12
        d.rectangle([cx0, cy0, cw, ch], fill="#0F172A")
        draw_centered_text(d, cx0, cy0, cw, ch, item["credit"], f_cred, "#F8FAFC")

    return supersampled(w, h, "#1E293B", _draw)


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
        x = (lon + 150.0) / 342.0 * (cw - 26) + 13
        y = (76.0 - lat) / 138.0 * (ch - 26) + 13
        return x, y

    def _draw(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        d.rectangle([0, 0, cw, ch], fill="#DCE8F2")
        for lat in (-30, 0, 30, 60):
            _, gy = proj(lat, 0, cw, ch)
            d.line([(0, int(gy)), (cw, int(gy))], fill="#C6D9EA", width=2)
        for poly in continents:
            pts = [proj(lat, lon, cw, ch) for lon, lat in poly]
            d.polygon(pts, fill="#EFECE2", outline="#94A3B8")

        nodes = []
        for s in lead_stories:
            if s.get("lat") is None:
                continue
            px, py = proj(s["lat"], s["lon"], cw, ch)
            nodes.append({"id": s["id"], "region": s["region"], "x": px, "y": py})

        min_dist = 32.0
        for _ in range(50):
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    dx = nodes[j]["x"] - nodes[i]["x"]
                    dy = nodes[j]["y"] - nodes[i]["y"]
                    dist = math.hypot(dx, dy)
                    if dist < 0.01:
                        dx, dy, dist = 1.0, 0.5, 1.118
                    if dist < min_dist:
                        push = (min_dist - dist) * 0.52
                        ux, uy = dx / dist, dy / dist
                        nodes[i]["x"] -= ux * push
                        nodes[i]["y"] -= uy * push
                        nodes[j]["x"] += ux * push
                        nodes[j]["y"] += uy * push
            for n in nodes:
                n["x"] = max(20.0, min(cw - 20.0, n["x"]))
                n["y"] = max(20.0, min(ch - 20.0, n["y"]))

        pin_font = load_font("sans_bold", 20)
        for n in nodes:
            px, py = int(n["x"]), int(n["y"])
            r = 15
            d.ellipse([px - r, py - r, px + r, py + r], fill=REGION_COLORS[n["region"]], outline="#FFFFFF", width=3)
            draw_centered_text(d, px - r, py - r, px + r, py + r, str(n["id"]), pin_font, "#FFFFFF")

    return supersampled(w, h, "#DCE8F2", _draw)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    data = json.loads((root / "news" / "stories.json").read_text(encoding="utf-8"))

    img = Image.new("RGB", (W, H), BG_PAPER)
    d = ImageDraw.Draw(img)

    f_mast = load_font("serif_bold", 52)
    f_deck = load_font("serif_italic", 11)
    f_kicker_top = load_font("sans_bold", 10)
    f_stat_val = load_font("serif_bold", 21)
    f_stat_lbl = load_font("sans", 9)
    f_reg = load_font("sans_bold", 10)
    f_num_sm = load_font("sans_bold", 9)
    f_badge = load_font("sans_bold", 8)
    f_hero_k = load_font("sans_bold", 9)
    f_hero_h = load_font("serif_bold", 17)
    f_hero_b = load_font("sans", 10)
    f_card_k = load_font("sans_bold", 8)
    f_card_h = load_font("serif_bold", 13)
    f_card_b = load_font("sans", 10)
    f_sec_hdr = load_font("sans_bold", 10)
    f_br_num = load_font("sans_bold", 9)
    f_br_loc = load_font("sans_bold", 10)
    f_br_txt = load_font("sans", 10)
    f_br_src = load_font("serif_italic", 9)
    f_dc_bold = load_font("sans_bold", 9)
    f_dc_txt = load_font("sans", 9)
    f_footer = load_font("sans", 9)

    all_stories = data["hero"] + data["cards"] + data["briefs"]

    # 1. Masthead (y = 8..96)
    d.line([(MARGIN, 7), (W - MARGIN, 7)], fill=INK_DARK, width=2)
    d.text((MARGIN, 12), data["edition_kicker"], font=f_kicker_top, fill=ACCENT_RED)
    right_tag = f"{len(all_stories)} VERIFIED STORIES · 7 REGIONS · EVERY ONE DATED 21 NOV 2026"
    rw, _ = text_size(d, right_tag, f_kicker_top)
    d.text((W - MARGIN - rw, 12), right_tag, font=f_kicker_top, fill=INK_BODY)

    mw, _ = text_size(d, data["date_label"], f_mast)
    d.text(((W - mw) // 2, 22), data["date_label"], font=f_mast, fill=INK_DARK)

    dw, _ = text_size(d, data["deck"], f_deck)
    d.text(((W - dw) // 2, 79), data["deck"], font=f_deck, fill=INK_BODY)
    d.line([(MARGIN, 95), (W - MARGIN, 95)], fill=INK_DARK, width=2)

    # 2. Six Key Numbers Strip (y = 99..144)
    stats = data["stats"]
    col_w = CONTENT_W / len(stats)
    for i, st in enumerate(stats):
        sx = int(MARGIN + i * col_w)
        d.rectangle([sx, 102, sx + 2, 140], fill=ACCENT_RED)
        d.text((sx + 7, 98), st["value"], font=f_stat_val, fill=INK_DARK)
        lbl_lines = wrap_text(d, st["label"], f_stat_lbl, int(col_w) - 12)
        for li, line in enumerate(lbl_lines[:2]):
            d.text((sx + 7, 123 + li * 10), line, font=f_stat_lbl, fill=INK_BODY)

    # 3. Region Bar (y = 148..167)
    reg_order = ["Europe", "Americas", "Asia", "Middle East", "Africa", "Oceania", "Global"]
    reg_short = {"Middle East": "Mid East"}
    counts = {r: sum(1 for s in all_stories if s["region"] == r) for r in reg_order}
    total = sum(counts.values())
    rx = MARGIN
    for idx, r in enumerate(reg_order):
        cnt = counts[r]
        seg_w = (W - MARGIN - rx) if idx == len(reg_order) - 1 else round(CONTENT_W * cnt / total)
        d.rectangle([rx, 148, rx + seg_w - 2, 166], fill=REGION_COLORS[r])
        lbl = f"{reg_short.get(r, r)} {cnt}"
        draw_centered_text(d, rx, 148, rx + seg_w - 2, 166, lbl, f_reg, "#FFFFFF")
        rx += seg_w

    # 4. Three Hero Lead Panels (y = 173..403)
    hero_y, hero_h = 173, 230
    hero_gap = 10
    hero_w = (CONTENT_W - 2 * hero_gap) // 3
    for i, hitem in enumerate(data["hero"]):
        hx = MARGIN + i * (hero_w + hero_gap)
        d.rectangle([hx, hero_y, hx + hero_w, hero_y + hero_h], fill=BG_CARD, outline=RULE, width=1)
        art_h = 114
        art = draw_hero_panel_art(hitem, hero_w - 2, art_h)
        img.paste(art, (hx + 1, hero_y + 1))

        ky = hero_y + art_h + 6
        d.ellipse([hx + 8, ky, hx + 22, ky + 14], fill=REGION_COLORS[hitem["region"]])
        draw_centered_text(d, hx + 8, ky, hx + 22, ky + 14, str(hitem["id"]), f_num_sm, "#FFFFFF")
        d.text((hx + 26, ky + 1), hitem["kicker"], font=f_hero_k, fill=REGION_COLORS[hitem["region"]])

        st_lbl = hitem["status"]
        stw, _ = text_size(d, st_lbl, f_badge)
        bx0 = hx + hero_w - stw - 18
        d.rounded_rectangle([bx0, ky, hx + hero_w - 8, ky + 14], radius=3, fill=STATUS_COLORS[st_lbl])
        draw_centered_text(d, bx0, ky, hx + hero_w - 8, ky + 14, st_lbl, f_badge, "#FFFFFF")

        cy = ky + 17
        h_lines = wrap_text(d, hitem["headline"], f_hero_h, hero_w - 18)
        assert len(h_lines) <= 2, f"Hero {hitem['id']} headline overflow: {h_lines}"
        for line in h_lines:
            d.text((hx + 9, cy), line, font=f_hero_h, fill=INK_DARK)
            cy += 19
        cy += 3
        full_body = f"{hitem['summary']} ({hitem['sources']})"
        b_lines = wrap_text(d, full_body, f_hero_b, hero_w - 18)
        assert len(b_lines) <= 4, f"Hero {hitem['id']} summary overflow: {b_lines}"
        for line in b_lines:
            d.text((hx + 9, cy), line, font=f_hero_b, fill=INK_BODY)
            cy += 13
        assert cy <= hero_y + hero_h - 2, f"Hero {hitem['id']} vertical overflow ({cy})"

    # 5. Eight Spacious Secondary Cards (2 rows x 4 cols, y = 410..688)
    c_top = 410
    c_gap_x, c_gap_y = 8, 8
    c_w = (CONTENT_W - 3 * c_gap_x) // 4
    c_h = 135
    for idx, citem in enumerate(data["cards"]):
        row, col = divmod(idx, 4)
        cx = MARGIN + col * (c_w + c_gap_x)
        cy0 = c_top + row * (c_h + c_gap_y)
        d.rectangle([cx, cy0, cx + c_w, cy0 + c_h], fill=BG_CARD, outline=RULE, width=1)
        art_h = 56
        art = draw_card_panel_art(citem, c_w - 2, art_h)
        img.paste(art, (cx + 1, cy0 + 1))

        ky = cy0 + art_h + 4
        d.ellipse([cx + 7, ky, cx + 20, ky + 13], fill=REGION_COLORS[citem["region"]])
        draw_centered_text(d, cx + 7, ky, cx + 20, ky + 13, str(citem["id"]), f_num_sm, "#FFFFFF")
        d.text((cx + 24, ky + 1), citem["kicker"], font=f_card_k, fill=REGION_COLORS[citem["region"]])

        st_lbl = citem["status"]
        stw, _ = text_size(d, st_lbl, f_badge)
        bx0 = cx + c_w - stw - 14
        d.rounded_rectangle([bx0, ky, cx + c_w - 6, ky + 13], radius=3, fill=STATUS_COLORS[st_lbl])
        draw_centered_text(d, bx0, ky, cx + c_w - 6, ky + 13, st_lbl, f_badge, "#FFFFFF")

        ty = ky + 15
        h_lines = wrap_text(d, citem["headline"], f_card_h, c_w - 14)
        assert len(h_lines) <= 2, f"Card {citem['id']} headline overflow: {h_lines}"
        for line in h_lines:
            d.text((cx + 7, ty), line, font=f_card_h, fill=INK_DARK)
            ty += 15
        ty += 2
        card_body = f"{citem['summary']} ({citem['sources']})"
        b_lines = wrap_text(d, card_body, f_card_b, c_w - 14)
        assert len(b_lines) <= 2, f"Card {citem['id']} summary overflow: {b_lines}"
        for line in b_lines:
            d.text((cx + 7, ty), line, font=f_card_b, fill=INK_BODY)
            ty += 12
        assert ty <= cy0 + c_h - 2, f"Card {citem['id']} vertical overflow ({ty} > {cy0+c_h-2})"

    # 6. Airy Bottom Band (y = 696..934)
    left_x, left_w = MARGIN, 330
    right_x, right_w = left_x + left_w + 14, CONTENT_W - left_w - 14
    band_top, band_bot = 696, 934

    # Left: Clean 11-Pin World Map
    d.text((left_x, band_top), "WHERE IT HAPPENED — LEAD STORIES 1–11", font=f_sec_hdr, fill=INK_DARK)
    d.line([(left_x, band_top + 15), (left_x + left_w, band_top + 15)], fill=INK_DARK, width=1)
    map_img = draw_world_map(data["hero"] + data["cards"], left_w, band_bot - (band_top + 19))
    img.paste(map_img, (left_x, band_top + 19))
    d.rectangle([left_x, band_top + 19, left_x + left_w, band_bot], outline=RULE, width=1)

    # Right: 18 Briefs in 2 airy columns (9 rows x 2 cols, 24px per row!)
    d.text((right_x, band_top), "ALSO ON SATURDAY 21 NOVEMBER — 18 MORE VERIFIED STORIES", font=f_sec_hdr, fill=INK_DARK)
    d.line([(right_x, band_top + 15), (right_x + right_w, band_top + 15)], fill=INK_DARK, width=1)

    half = len(data["briefs"]) // 2
    col_bw = (right_w - 12) // 2
    row_bh = (band_bot - (band_top + 19)) / half
    d.line([(right_x + col_bw + 6, band_top + 19), (right_x + col_bw + 6, band_bot)], fill=RULE, width=1)

    for idx, b in enumerate(data["briefs"]):
        col_i = 0 if idx < half else 1
        row_i = idx if idx < half else idx - half
        bx0 = right_x + col_i * (col_bw + 12)
        ry0 = int(band_top + 19 + row_i * row_bh)
        ry1 = int(band_top + 19 + (row_i + 1) * row_bh)
        if row_i % 2 == 1:
            d.rectangle([bx0, ry0, bx0 + col_bw, ry1], fill=BG_TINT)

        num_s = f"{b['id']}"
        d.ellipse([bx0 + 2, ry0 + 4, bx0 + 18, ry0 + 20], fill=REGION_COLORS[b["region"]])
        draw_centered_text(d, bx0 + 2, ry0 + 4, bx0 + 18, ry0 + 20, num_s, f_br_num, "#FFFFFF")

        tx = bx0 + 22
        place_s = f"{b['place']}: "
        pw, _ = text_size(d, place_s, f_br_loc)
        d.text((tx, ry0 + 5), place_s, font=f_br_loc, fill=INK_DARK)
        tx += pw

        body_s = f"{b['text']} "
        bw, _ = text_size(d, body_s, f_br_txt)
        d.text((tx, ry0 + 5), body_s, font=f_br_txt, fill=INK_BODY)
        tx += bw

        src_s = f"({b['source']})"
        sw, _ = text_size(d, src_s, f_br_src)
        assert tx + sw <= bx0 + col_bw - 2, f"Brief {b['id']} too wide ({tx + sw} > {bx0 + col_bw - 2}): {place_s}{body_s}{src_s}"
        d.text((tx, ry0 + 6), src_s, font=f_br_src, fill=INK_MUTED)

    # 7. Full-Width Date Check & Verification Strip (y = 940..994)
    dc_y0, dc_y1 = 940, 994
    d.rectangle([MARGIN, dc_y0, W - MARGIN, dc_y1], fill=BG_DATE_CHECK, outline=ACCENT_RED, width=2)
    lbl1 = "DATE CHECK — Left out as earlier news (18–20 Nov): "
    l1w, _ = text_size(d, lbl1, f_dc_bold)
    d.text((MARGIN + 8, dc_y0 + 5), lbl1, font=f_dc_bold, fill=ACCENT_RED)
    ex_lines = wrap_text(d, data["date_check_excluded"], f_dc_txt, CONTENT_W - 18 - l1w)
    assert len(ex_lines) <= 2, f"Excluded text wrapped >2 lines: {ex_lines}"
    d.text((MARGIN + 8 + l1w, dc_y0 + 5), ex_lines[0], font=f_dc_txt, fill="#7F1D1D")
    y_next = dc_y0 + 18
    if len(ex_lines) > 1:
        d.text((MARGIN + 8, y_next), ex_lines[1], font=f_dc_txt, fill="#7F1D1D")
        y_next += 15
    lbl2 = "NOT CONFIRMED AT 11:45 UTC (NOT SHOWN AS DONE): "
    l2w, _ = text_size(d, lbl2, f_dc_bold)
    d.text((MARGIN + 8, y_next + 2), lbl2, font=f_dc_bold, fill=ACCENT_NAVY)
    unc_w, _ = text_size(d, data["date_check_unconfirmed"], f_dc_txt)
    assert MARGIN + 8 + l2w + unc_w <= W - MARGIN - 6, "Unconfirmed line overflow"
    d.text((MARGIN + 8 + l2w, y_next + 2), data["date_check_unconfirmed"], font=f_dc_txt, fill=INK_BODY)

    # 8. Footer (y = 999..1020)
    footer = "Every story happened or was first reported on Saturday 21 Nov 2026 · HOW WE CHECKED: CONFIRMED = 2+ outlets · OFFICIAL = agency/on the record · CLAIM = unverified/one side · Original vector art"
    fw, _ = text_size(d, footer, f_footer)
    d.text(((W - fw) // 2, 1003), footer, font=f_footer, fill=INK_MUTED)

    out_path = root / "entry.png"
    img.save(out_path, format="PNG", optimize=True)
    preview = img.resize((300, 300), Image.Resampling.LANCZOS)
    preview.save(root.parent / "preview_300.png", format="PNG")
    print(f"Saved {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
