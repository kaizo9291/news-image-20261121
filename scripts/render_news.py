#!/usr/bin/env python3
"""Render a 1024x1024 broadsheet world-news summary PNG for Saturday 21 November 2026."""

from __future__ import annotations

import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
MARGIN = 16
CONTENT_W = W - 2 * MARGIN

BG_PAPER = "#FAF8F2"
BG_CARD = "#FFFFFF"
BG_TINT = "#F3EFE6"
BG_DATE_CHECK = "#FEF2F2"
INK_DARK = "#0F172A"
INK_BODY = "#273449"
INK_MUTED = "#5A677A"
RULE = "#CBD5E1"
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
            # Warm sun-haze bar on right
            d.rectangle([int(cw * 0.62), 0, cw, ch], fill="#F5E6CC")
            # Earth globe bottom-center-right
            cx, cy, r = int(cw * 0.50), int(ch * 0.68), 64
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill="#2563EB", outline="#0F172A", width=5)
            d.polygon([(cx - 38, cy - 22), (cx - 10, cy - 42), (cx + 12, cy - 16), (cx - 12, cy + 26), (cx - 36, cy + 10)], fill="#22C55E")
            d.polygon([(cx + 16, cy - 30), (cx + 48, cy - 14), (cx + 38, cy + 22), (cx + 12, cy + 12)], fill="#22C55E")
            # Thermometer
            tx = int(cw * 0.72)
            d.rounded_rectangle([tx - 12, 48, tx + 12, ch - 52], radius=12, fill="#FFFFFF", outline="#0F172A", width=4)
            d.ellipse([tx - 22, ch - 68, tx + 22, ch - 24], fill="#DC2626", outline="#0F172A", width=4)
            d.rectangle([tx - 6, 86, tx + 6, ch - 42], fill="#DC2626")
            # Overtime clock
            kx, ky, kr = int(cw * 0.88), int(ch * 0.64), 40
            d.ellipse([kx - kr, ky - kr, kx + kr, ky + kr], fill="#FFFFFF", outline="#0F172A", width=5)
            d.line([(kx, ky), (kx, ky - 24)], fill="#0F172A", width=5)
            d.line([(kx, ky), (kx + 20, ky + 8)], fill="#DC2626", width=5)
            d.ellipse([kx - 5, ky - 5, kx + 5, ky + 5], fill="#0F172A")
        elif kind == "riyadh":
            d.rectangle([0, 0, cw, ch], fill="#0B162C")
            # Horizon desert sand strip
            d.rectangle([0, ch - 26, cw, ch], fill="#1E293B")
            # Riyadh skyline incl. Kingdom Centre arch silhouette
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
            # Kingdom arch cutout on tall building (446..514)
            d.ellipse([462, 106, 498, 142], fill="#0B162C")
            # Intercept trails and golden bursts
            bursts = [(290, 92), (410, 62), (555, 86)]
            for ix, iy in bursts:
                d.line([(ix + 95, 6), (ix, iy)], fill="#EF4444", width=5)
                d.line([(ix - 50, ch - 30), (ix, iy)], fill="#38BDF8", width=4)
                for ang in range(0, 360, 45):
                    rad = math.radians(ang)
                    d.line([(ix, iy), (ix + int(28 * math.cos(rad)), iy + int(28 * math.sin(rad)))], fill="#F59E0B", width=5)
                d.ellipse([ix - 12, iy - 12, ix + 12, iy + 12], fill="#FEF08A")
        else:
            # Banda Sea M6.8 earthquake: warm parchment sky, sea band, island silhouette, bold seismograph trace
            d.rectangle([0, 0, cw, ch], fill="#F6EFE2")
            d.rectangle([0, int(ch * 0.68), cw, ch], fill="#1D4ED8")
            # Concentric shock rings in sea
            ex, ey = int(cw * 0.72), int(ch * 0.76)
            for rr in (26, 52, 78, 104):
                d.ellipse([ex - rr, ey - rr // 2, ex + rr, ey + rr // 2], outline="#EF4444", width=4)
            d.ellipse([ex - 10, ey - 10, ex + 10, ey + 10], fill="#DC2626", outline="#FFFFFF", width=3)
            # Island/house silhouette on left-mid shore
            d.polygon([(30, int(ch * 0.68)), (110, int(ch * 0.56)), (220, int(ch * 0.60)), (290, int(ch * 0.68))], fill="#92400E")
            # Bold red seismograph waveform shifted right of top-left pills
            pts = [
                (16, 146), (180, 146), (245, 142), (285, 150), (318, 128), (344, 166),
                (372, 94), (398, 180), (426, 56), (456, 184), (486, 74), (514, 166),
                (544, 114), (576, 150), (608, 142), (636, 146),
            ]
            d.line(pts, fill="#B91C1C", width=6)

        # Giant high-contrast top-left banner (legible even at 300px!)
        f_ban = load_font("sans_bold", 42)
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
    banner_bg = "#B91C1C" if kind in ("drone", "kyiv", "bitcoin", "plane") else "#1E3A5F"

    def _draw(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        bar_h = 44
        # Scene strip below top banner (y = bar_h .. ch)
        sy0 = bar_h
        sh = ch - sy0
        mid_y = sy0 + sh // 2

        if kind == "drone":
            d.rectangle([0, sy0, cw, ch], fill="#DBEAFE")
            d.rectangle([0, ch - 18, cw, ch], fill="#1D4ED8")
            # Iran & US detailed flag chips left
            d.rectangle([12, sy0 + 8, 60, sy0 + 18], fill="#16A34A")
            d.rectangle([12, sy0 + 18, 60, sy0 + 28], fill="#FFFFFF")
            d.rectangle([12, sy0 + 28, 60, sy0 + 38], fill="#DC2626")
            d.ellipse([32, sy0 + 19, 40, sy0 + 27], fill="#DC2626")
            for si in range(6):
                col = "#B91C1C" if si % 2 == 0 else "#FFFFFF"
                d.rectangle([70, sy0 + 8 + si * 5, 118, sy0 + 13 + si * 5], fill=col)
            d.rectangle([70, sy0 + 8, 92, sy0 + 23], fill="#1E3A8A")
            # Drone silhouette right
            dx = int(cw * 0.62)
            d.line([(dx - 64, mid_y - 4), (dx + 64, mid_y - 4)], fill="#0F172A", width=6)
            d.polygon([(dx - 24, mid_y - 8), (dx + 32, mid_y - 4), (dx - 24, mid_y + 6)], fill="#334155")
            d.ellipse([dx - 8, mid_y - 16, dx + 14, mid_y + 4], outline="#DC2626", width=4)
        elif kind == "kyiv":
            d.rectangle([0, sy0, cw, sy0 + sh // 2], fill="#1D4ED8")
            d.rectangle([0, sy0 + sh // 2, cw, ch], fill="#FACC15")
            # Microphone / speaker wave icon
            mx = int(cw * 0.34)
            d.rounded_rectangle([mx - 12, sy0 + 8, mx + 12, sy0 + 38], radius=10, fill="#0F172A")
            d.line([(mx, sy0 + 38), (mx, ch - 6)], fill="#0F172A", width=5)
            d.arc([mx + 14, sy0 + 10, mx + 44, sy0 + 40], 300, 60, fill="#0F172A", width=4)
            d.arc([mx + 22, sy0 + 4, mx + 60, sy0 + 46], 300, 60, fill="#0F172A", width=4)
        elif kind == "bitcoin":
            d.rectangle([0, sy0, cw, ch], fill="#111827")
            # Crash sparkline red
            pts = [(16, sy0 + 10), (70, sy0 + 14), (110, sy0 + 12), (160, sy0 + 26), (205, sy0 + 22), (260, sy0 + 44), (315, sy0 + 50), (360, sy0 + 42)]
            d.line(pts, fill="#EF4444", width=5)
            # Orange Bitcoin circle right-center
            bx, by, br = int(cw * 0.44), mid_y, 24
            d.ellipse([bx - br, by - br, bx + br, by + br], fill="#F59E0B", outline="#FEF3C7", width=3)
            bf = load_font("sans_bold", 28)
            d.text((bx - 9, by - 17), "B", font=bf, fill="#FFFFFF")
        elif kind == "robots":
            d.rectangle([0, sy0, cw, ch], fill="#E0F2FE")
            # UN blue emblem left
            ux, uy, ur = 60, mid_y, 24
            d.ellipse([ux - ur, uy - ur, ux + ur, uy + ur], fill="#0284C7", outline="#FFFFFF", width=3)
            d.ellipse([ux - 13, uy - 13, ux + 13, uy + 13], outline="#FFFFFF", width=2)
            # Robot head + red caution ring
            rx, ry = int(cw * 0.54), mid_y
            d.rounded_rectangle([rx - 22, ry - 18, rx + 22, ry + 18], radius=6, fill="#334155", outline="#0F172A", width=3)
            d.ellipse([rx - 13, ry - 7, rx - 3, ry + 3], fill="#EF4444")
            d.ellipse([rx + 3, ry - 7, rx + 13, ry + 3], fill="#EF4444")
            d.line([(rx, ry - 26), (rx, ry - 18)], fill="#0F172A", width=4)
        elif kind == "math":
            d.rectangle([0, sy0, cw, ch], fill="#1E1B4B")
            # Formula & Lean proof checkmark badge
            mf = load_font("serif_bold", 34)
            d.text((24, sy0 + 10), "ζ(s) = 0", font=mf, fill="#FDE047")
            cx, cy = int(cw * 0.56), mid_y
            d.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], fill="#10B981", outline="#FFFFFF", width=3)
            d.line([(cx - 9, cy + 1), (cx - 2, cy + 9), (cx + 11, cy - 8)], fill="#FFFFFF", width=5)
        elif kind == "plane":
            d.rectangle([0, sy0, cw, ch], fill="#BAE6FD")
            d.rectangle([0, ch - 18, cw, ch], fill="#475569")
            # Jet silhouette landing safely
            px, py = int(cw * 0.44), sy0 + 28
            d.polygon([(px - 56, py), (px + 48, py - 6), (px + 66, py + 4), (px - 50, py + 10)], fill="#FFFFFF", outline="#0F172A", width=3)
            d.polygon([(px - 54, py), (px - 68, py - 20), (px - 36, py - 2)], fill="#DC2626")
            d.polygon([(px - 10, py + 2), (px + 20, py + 2), (px + 4, py + 18)], fill="#94A3B8")
        elif kind == "cricket":
            d.rectangle([0, sy0, cw, ch], fill="#15803D")
            d.rectangle([int(cw * 0.42), sy0, int(cw * 0.64), ch], fill="#E5D5A8")
            # India & NZ detailed flags left
            d.rectangle([12, sy0 + 8, 56, sy0 + 18], fill="#F97316")
            d.rectangle([12, sy0 + 18, 56, sy0 + 28], fill="#FFFFFF")
            d.rectangle([12, sy0 + 28, 56, sy0 + 38], fill="#16A34A")
            d.ellipse([30, sy0 + 19, 38, sy0 + 27], outline="#1E3A8A", width=2)
            d.rectangle([64, sy0 + 8, 108, sy0 + 38], fill="#1E3A8A")
            d.line([(64, sy0 + 16), (86, sy0 + 16)], fill="#DC2626", width=3)
            d.line([(75, sy0 + 8), (75, sy0 + 24)], fill="#DC2626", width=3)
            for sx0, sy_off in [(96, 13), (102, 20), (92, 22), (96, 31)]:
                d.ellipse([sx0 - 2, sy0 + sy_off - 2, sx0 + 2, sy0 + sy_off + 2], fill="#EF4444")
            # Stumps + red cricket ball
            sx = int(cw * 0.53)
            for ox in (-10, 0, 10):
                d.line([(sx + ox, sy0 + 10), (sx + ox, ch - 8)], fill="#92400E", width=4)
            d.line([(sx - 12, sy0 + 10), (sx + 12, sy0 + 10)], fill="#F59E0B", width=4)
            d.ellipse([int(cw * 0.72) - 12, mid_y - 12, int(cw * 0.72) + 12, mid_y + 12], fill="#B91C1C", outline="#FFFFFF", width=2)
        else:  # f1
            d.rectangle([0, sy0, cw, ch], fill="#111827")
            # Checkered flag strip left
            for r in range(3):
                for c in range(4):
                    col = "#FFFFFF" if (r + c) % 2 == 0 else "#0F172A"
                    d.rectangle([10 + c * 14, sy0 + 8 + r * 14, 24 + c * 14, sy0 + 22 + r * 14], fill=col)
            # F1 car silhouette center
            fx, fy = int(cw * 0.48), mid_y + 4
            d.rounded_rectangle([fx - 56, fy - 12, fx + 52, fy + 10], radius=8, fill="#1E3A8A", outline="#FACC15", width=3)
            d.rectangle([fx + 38, fy - 16, fx + 62, fy + 12], fill="#EF4444")
            d.ellipse([fx - 44, fy + 2, fx - 22, fy + 22], fill="#0F172A", outline="#E2E8F0", width=3)
            d.ellipse([fx + 18, fy + 2, fx + 40, fy + 22], fill="#0F172A", outline="#E2E8F0", width=3)

        # Full-width top bold banner (legible at 300px!)
        d.rectangle([0, 0, cw, bar_h], fill=banner_bg)
        f_ban = load_font("sans_bold", 28)
        draw_centered_text(d, 0, 0, cw, bar_h, item["banner"], f_ban, "#FFFFFF", align_left_pad=12)

        # Crisp bottom-right credit pill
        f_cred = load_font("sans_bold", 16)
        crw, crh = text_size(d, item["credit"], f_cred)
        cx0 = cw - crw - 18
        cy0 = ch - crh - 12
        d.rectangle([cx0, cy0, cw, ch], fill="#0F172A")
        draw_centered_text(d, cx0, cy0, cw, ch, item["credit"], f_cred, "#F8FAFC")

    return supersampled(w, h, "#1E293B", _draw)


def draw_world_map(all_stories: list[dict], w: int, h: int) -> Image.Image:
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
        y = (76.0 - lat) / 138.0 * (ch - 56) + 12
        return x, y

    def _draw(d: ImageDraw.ImageDraw, cw: int, ch: int) -> None:
        d.rectangle([0, 0, cw, ch], fill="#D8E6F2")
        for lat in (-30, 0, 30, 60):
            _, gy = proj(lat, 0, cw, ch)
            d.line([(0, int(gy)), (cw, int(gy))], fill="#C3D7E8", width=2)
        for poly in continents:
            pts = [proj(lat, lon, cw, ch) for lon, lat in poly]
            d.polygon(pts, fill="#EFECE4", outline="#94A3B8")

        # Deterministic repulsion pass so all 35 pins stay distinct & readable
        nodes = []
        for s in all_stories:
            if s.get("lat") is None:
                continue
            px, py = proj(s["lat"], s["lon"], cw, ch)
            nodes.append({"id": s["id"], "region": s["region"], "x": px, "y": py})

        min_dist = 25.0
        for _ in range(60):
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
                n["x"] = max(16.0, min(cw - 16.0, n["x"]))
                n["y"] = max(16.0, min(ch - 54.0, n["y"]))

        pin_font = load_font("sans_bold", 15)
        for n in nodes:
            px, py = int(n["x"]), int(n["y"])
            r = 11
            d.ellipse([px - r, py - r, px + r, py + r], fill=REGION_COLORS[n["region"]], outline="#FFFFFF", width=2)
            draw_centered_text(d, px - r, py - r, px + r, py + r, str(n["id"]), pin_font, "#FFFFFF")

        # Bottom legend strip inside map box
        d.rectangle([0, ch - 36, cw, ch], fill="#F8FAFC")
        d.line([(0, ch - 36), (cw, ch - 36)], fill="#CBD5E1", width=2)
        lf = load_font("sans_bold", 15)
        lx = 12
        for reg, lbl in [("Europe", "Eur"), ("Americas", "Amer"), ("Asia", "Asia"), ("Middle East", "ME"), ("Africa", "Afr"), ("Oceania", "Oce"), ("Global", "Glb")]:
            d.ellipse([lx, ch - 25, lx + 12, ch - 13], fill=REGION_COLORS[reg])
            d.text((lx + 16, ch - 28), lbl, font=lf, fill="#1E293B")
            lw, _ = text_size(d, lbl, lf)
            lx += lw + 32

    return supersampled(w, h, "#D8E6F2", _draw)


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    data = json.loads((root / "news" / "stories.json").read_text(encoding="utf-8"))

    img = Image.new("RGB", (W, H), BG_PAPER)
    d = ImageDraw.Draw(img)

    f_mast = load_font("serif_bold", 50)
    f_deck = load_font("serif_italic", 11)
    f_kicker_top = load_font("sans_bold", 10)
    f_stat_val = load_font("serif_bold", 20)
    f_stat_lbl = load_font("sans", 9)
    f_reg = load_font("sans_bold", 10)
    f_num_sm = load_font("sans_bold", 9)
    f_hero_k = load_font("sans_bold", 9)
    f_hero_h = load_font("serif_bold", 16)
    f_hero_b = load_font("sans", 10)
    f_card_k = load_font("sans_bold", 8)
    f_card_h = load_font("serif_bold", 12)
    f_card_b = load_font("sans", 9)
    f_sec_hdr = load_font("sans_bold", 10)
    f_br_num = load_font("sans_bold", 9)
    f_br_loc = load_font("narrow_bold", 10)
    f_br_txt = load_font("narrow", 10)
    f_br_src = load_font("serif_italic", 8)
    f_dc_bold = load_font("sans_bold", 9)
    f_dc_txt = load_font("sans", 9)
    f_footer = load_font("sans", 9)

    all_stories = data["hero"] + data["cards"] + data["briefs"]

    # 1. Masthead (y = 6..96)
    d.line([(MARGIN, 6), (W - MARGIN, 6)], fill=ACCENT_NAVY, width=2)
    d.line([(MARGIN, 10), (W - MARGIN, 10)], fill=RULE, width=1)
    d.text((MARGIN, 13), data["edition_kicker"], font=f_kicker_top, fill=ACCENT_RED)
    right_tag = f"{len(all_stories)} VERIFIED STORIES · 7 REGIONS · EVERY ONE DATED 21 NOV 2026"
    rw, _ = text_size(d, right_tag, f_kicker_top)
    d.text((W - MARGIN - rw, 13), right_tag, font=f_kicker_top, fill=INK_BODY)

    mw, _ = text_size(d, data["date_label"], f_mast)
    d.text(((W - mw) // 2, 23), data["date_label"], font=f_mast, fill=INK_DARK)

    dw, _ = text_size(d, data["deck"], f_deck)
    d.text(((W - dw) // 2, 79), data["deck"], font=f_deck, fill=INK_BODY)
    d.line([(MARGIN, 95), (W - MARGIN, 95)], fill=INK_DARK, width=1)

    # 2. Six Key Numbers Strip (y = 98..142)
    stats = data["stats"]
    col_w = CONTENT_W / len(stats)
    for i, st in enumerate(stats):
        sx = int(MARGIN + i * col_w)
        d.rectangle([sx, 101, sx + 2, 139], fill=ACCENT_RED)
        d.text((sx + 7, 98), st["value"], font=f_stat_val, fill=INK_DARK)
        lbl_lines = wrap_text(d, st["label"], f_stat_lbl, int(col_w) - 12)
        for li, line in enumerate(lbl_lines[:2]):
            d.text((sx + 7, 121 + li * 10), line, font=f_stat_lbl, fill=INK_BODY)

    # 3. Region Bar (y = 146..164)
    reg_order = ["Europe", "Americas", "Asia", "Middle East", "Africa", "Oceania", "Global"]
    reg_short = {"Middle East": "Mid East"}
    counts = {r: sum(1 for s in all_stories if s["region"] == r) for r in reg_order}
    total = sum(counts.values())
    rx = MARGIN
    for idx, r in enumerate(reg_order):
        cnt = counts[r]
        seg_w = (W - MARGIN - rx) if idx == len(reg_order) - 1 else round(CONTENT_W * cnt / total)
        d.rectangle([rx, 146, rx + seg_w - 2, 163], fill=REGION_COLORS[r])
        lbl = f"{reg_short.get(r, r)} {cnt}"
        lw, lh = text_size(d, lbl, f_reg)
        d.text((rx + (seg_w - 2 - lw) // 2, 146 + (17 - lh) // 2 - 1), lbl, font=f_reg, fill="#FFFFFF")
        rx += seg_w

    # 4. Three Hero Lead Panels (y = 170..396)
    hero_y, hero_h = 170, 226
    hero_gap = 10
    hero_w = (CONTENT_W - 2 * hero_gap) // 3
    for i, hitem in enumerate(data["hero"]):
        hx = MARGIN + i * (hero_w + hero_gap)
        d.rectangle([hx, hero_y, hx + hero_w, hero_y + hero_h], fill=BG_CARD, outline=RULE, width=1)
        art_h = 112
        art = draw_hero_panel_art(hitem, hero_w - 2, art_h)
        img.paste(art, (hx + 1, hero_y + 1))

        # Number badge + kicker
        ky = hero_y + art_h + 6
        d.ellipse([hx + 8, ky, hx + 22, ky + 14], fill=REGION_COLORS[hitem["region"]])
        draw_centered_text(d, hx + 8, ky, hx + 22, ky + 14, str(hitem["id"]), f_num_sm, "#FFFFFF")
        d.text((hx + 26, ky + 1), hitem["kicker"], font=f_hero_k, fill=REGION_COLORS[hitem["region"]])

        cy = ky + 16
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
        assert cy <= hero_y + hero_h - 3, f"Hero {hitem['id']} vertical overflow ({cy})"

    # 5. Eight Wide Secondary Cards (2 rows x 4 cols, y = 402..674)
    c_top = 402
    c_gap_x, c_gap_y = 8, 8
    c_w = (CONTENT_W - 3 * c_gap_x) // 4
    c_h = 132
    for idx, citem in enumerate(data["cards"]):
        row, col = divmod(idx, 4)
        cx = MARGIN + col * (c_w + c_gap_x)
        cy0 = c_top + row * (c_h + c_gap_y)
        d.rectangle([cx, cy0, cx + c_w, cy0 + c_h], fill=BG_CARD, outline=RULE, width=1)
        art_h = 52
        art = draw_card_panel_art(citem, c_w - 2, art_h)
        img.paste(art, (cx + 1, cy0 + 1))

        ky = cy0 + art_h + 4
        d.ellipse([cx + 7, ky, cx + 20, ky + 13], fill=REGION_COLORS[citem["region"]])
        draw_centered_text(d, cx + 7, ky, cx + 20, ky + 13, str(citem["id"]), f_num_sm, "#FFFFFF")
        d.text((cx + 24, ky + 1), citem["kicker"], font=f_card_k, fill=REGION_COLORS[citem["region"]])

        ty = ky + 14
        h_lines = wrap_text(d, citem["headline"], f_card_h, c_w - 14)
        assert len(h_lines) <= 2, f"Card {citem['id']} headline overflow: {h_lines}"
        for line in h_lines:
            d.text((cx + 7, ty), line, font=f_card_h, fill=INK_DARK)
            ty += 14
        ty += 2
        b_lines = wrap_text(d, citem["summary"], f_card_b, c_w - 14)
        assert len(b_lines) <= 3, f"Card {citem['id']} summary overflow: {b_lines}"
        for line in b_lines:
            d.text((cx + 7, ty), line, font=f_card_b, fill=INK_BODY)
            ty += 11
        assert ty <= cy0 + c_h - 2, f"Card {citem['id']} vertical overflow ({ty} > {cy0+c_h-2})"

    # 6. Bottom Editorial Band (y = 680..938)
    left_x, left_w = MARGIN, 334
    right_x, right_w = left_x + left_w + 10, CONTENT_W - left_w - 10
    band_top, band_bot = 680, 938

    # Left: World Map
    d.rectangle([left_x, band_top, left_x + left_w, band_top + 18], fill=ACCENT_NAVY)
    d.text((left_x + 8, band_top + 3), "WHERE IT HAPPENED — ALL 35 STORIES", font=f_sec_hdr, fill="#FFFFFF")
    map_h = band_bot - (band_top + 18)
    map_img = draw_world_map(all_stories, left_w, map_h)
    img.paste(map_img, (left_x, band_top + 18))
    d.rectangle([left_x, band_top, left_x + left_w, band_bot], outline=RULE, width=1)

    # Right: 24 Briefs in 2 clean columns (12 rows x 2 cols)
    d.rectangle([right_x, band_top, right_x + right_w, band_top + 18], fill=ACCENT_NAVY)
    d.text((right_x + 10, band_top + 3), "ALSO ON SATURDAY 21 NOVEMBER — 24 MORE VERIFIED STORIES", font=f_sec_hdr, fill="#FFFFFF")
    d.rectangle([right_x, band_top + 18, right_x + right_w, band_bot], fill=BG_CARD, outline=RULE, width=1)

    half = len(data["briefs"]) // 2
    col_bw = right_w // 2
    row_bh = (band_bot - (band_top + 18)) / half
    d.line([(right_x + col_bw, band_top + 18), (right_x + col_bw, band_bot)], fill=RULE, width=1)

    for idx, b in enumerate(data["briefs"]):
        col_i = 0 if idx < half else 1
        row_i = idx if idx < half else idx - half
        bx0 = right_x + col_i * col_bw
        ry0 = int(band_top + 18 + row_i * row_bh)
        ry1 = int(band_top + 18 + (row_i + 1) * row_bh)
        if row_i % 2 == 1:
            d.rectangle([bx0 + 1, ry0, bx0 + col_bw - 1, ry1], fill=BG_TINT)

        nx = bx0 + 5
        d.rounded_rectangle([nx, ry0 + 3, nx + 17, ry0 + 16], radius=2, fill=REGION_COLORS[b["region"]])
        draw_centered_text(d, nx, ry0 + 3, nx + 17, ry0 + 16, str(b["id"]), f_br_num, "#FFFFFF")

        tx = nx + 21
        place_s = f"{b['place']}: "
        pw, _ = text_size(d, place_s, f_br_loc)
        d.text((tx, ry0 + 4), place_s, font=f_br_loc, fill=INK_DARK)
        tx += pw

        body_s = f"{b['text']} "
        bw, _ = text_size(d, body_s, f_br_txt)
        d.text((tx, ry0 + 4), body_s, font=f_br_txt, fill=INK_BODY)
        tx += bw

        src_s = f"({b['source']})"
        sw, _ = text_size(d, src_s, f_br_src)
        assert tx + sw <= bx0 + col_bw - 4, f"Brief {b['id']} too wide ({tx + sw} > {bx0 + col_bw - 4}): {place_s}{body_s}{src_s}"
        d.text((tx, ry0 + 5), src_s, font=f_br_src, fill=INK_MUTED)

    # 7. Full-Width Date Check & Verification Box (y = 944..996)
    dc_y0, dc_y1 = 944, 996
    d.rectangle([MARGIN, dc_y0, W - MARGIN, dc_y1], fill=BG_DATE_CHECK, outline=ACCENT_RED, width=2)
    lbl1 = "DATE CHECK — "
    l1w, _ = text_size(d, lbl1, f_dc_bold)
    d.text((MARGIN + 8, dc_y0 + 5), lbl1, font=f_dc_bold, fill=ACCENT_RED)
    ex_lines = wrap_text(d, data["date_check_excluded"], f_dc_txt, CONTENT_W - 18 - l1w)
    assert len(ex_lines) <= 2, f"Excluded text wrapped >2 lines: {ex_lines}"
    d.text((MARGIN + 8 + l1w, dc_y0 + 5), ex_lines[0], font=f_dc_txt, fill="#7F1D1D")
    y_next = dc_y0 + 18
    if len(ex_lines) > 1:
        d.text((MARGIN + 8, y_next), ex_lines[1], font=f_dc_txt, fill="#7F1D1D")
        y_next += 14
    lbl2 = "UNCONFIRMED AT 11:45 UTC — "
    l2w, _ = text_size(d, lbl2, f_dc_bold)
    d.text((MARGIN + 8, y_next + 2), lbl2, font=f_dc_bold, fill=ACCENT_NAVY)
    unc_w, _ = text_size(d, data["date_check_unconfirmed"], f_dc_txt)
    assert MARGIN + 8 + l2w + unc_w <= W - MARGIN - 6, "Unconfirmed line overflow"
    d.text((MARGIN + 8 + l2w, y_next + 2), data["date_check_unconfirmed"], font=f_dc_txt, fill=INK_BODY)

    # 8. Footer (y = 1002..1020)
    d.line([(MARGIN, 1001), (W - MARGIN, 1001)], fill=RULE, width=1)
    footer = "Every story happened or was first reported on Saturday 21 November 2026 in at least one time zone · Claims attributed · Named outlets beside every story · Original vector drawings"
    fw, _ = text_size(d, footer, f_footer)
    d.text(((W - fw) // 2, 1005), footer, font=f_footer, fill=INK_MUTED)

    out_path = root / "entry.png"
    img.save(out_path, format="PNG", optimize=True)
    preview = img.resize((300, 300), Image.Resampling.LANCZOS)
    preview.save(root.parent / "preview_300.png", format="PNG")
    print(f"Saved {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
