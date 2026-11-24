#!/usr/bin/env python3
"""Rogue Agent Meme - Meme Sprint 3: AI Agent Goes Rogue.

Draws one original 1024x1024 meme image with the Python standard library
only (zlib for PNG encoding, no fonts, no image libraries, no network).
Every pixel is computed here: a hand-made 5x7 bitmap font, a robot at a
laptop, and the joke - an agent asked to summarize a doc who instead quits
its human's job, sells the car and takes over the company.

Writes entry.png into $MAKEFUN_OUTPUT_DIR (default /output).
SPDX-License-Identifier: MIT
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font ----
# Hand-designed 5x7 bitmap glyphs, one row per string, '#' = ink.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    ':': ("00000", "00100", "00000", "00000", "00000", "00100", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '>': ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}


def text_width(text, scale):
    """Pixel width of text at the given scale (glyph 5 wide + 1 gap)."""
    return len(text) * 6 * scale - scale


# -------------------------------------------------------------- canvas ----
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = color

    def rect(self, x0, y0, x1, y1, color):
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(self.w - 1, x1), min(self.h - 1, y1)
        for y in range(y0, y1 + 1):
            i = (y * self.w + x0) * 3
            self.px[i:(y * self.w + x1 + 1) * 3] = color * (x1 - x0 + 1)

    def disc(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.rect(cx - dx, cy + dy, cx + dx, cy + dy, color)

    def ring(self, cx, cy, r, t, color):
        for dy in range(-r - t, r + t + 1):
            for dx in range(-r - t, r + t + 1):
                d2 = dx * dx + dy * dy
                if (r - t) ** 2 <= d2 <= (r + t) ** 2:
                    self.set(cx + dx, cy + dy, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx, dy = x1 - x0, y1 - y0
        steps = max(abs(dx), abs(dy), 1)
        for s in range(steps + 1):
            x = round(x0 + dx * s / steps)
            y = round(y0 + dy * s / steps)
            self.disc(x, y, thick, color)

    def poly(self, pts, color):
        """Scanline fill of a simple polygon."""
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.rect(int(xs[j]), y, int(xs[j + 1]), y, color)

    def rrect(self, x0, y0, x1, y1, r, color):
        self.rect(x0 + r, y0, x1 - r, y1, color)
        self.rect(x0, y0 + r, x1, y1 - r, color)
        for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r),
                       (x0 + r, y1 - r), (x1 - r, y1 - r)):
            self.disc(cx, cy, r, color)

    def curve(self, x0, y0, x1, y1, x2, y2, color, thick=3):
        """Quadratic bezier stroke, sampled densely."""
        for t in range(101):
            u = t / 100.0
            x = round((1 - u) ** 2 * x0 + 2 * (1 - u) * u * x1 + u * u * x2)
            y = round((1 - u) ** 2 * y0 + 2 * (1 - u) * u * y1 + u * u * y2)
            self.disc(x, y, thick, color)

    def glyph(self, ch, x, y, scale, color):
        rows = FONT.get(ch.upper(), FONT[' '])
        for ry, row in enumerate(rows):
            for rx, bit in enumerate(row):
                if bit == '1':
                    self.rect(x + rx * scale, y + ry * scale,
                              x + (rx + 1) * scale - 1,
                              y + (ry + 1) * scale - 1, color)

    def text(self, s, x, y, scale, color):
        for ch in s:
            self.glyph(ch, x, y, scale, color)
            x += 6 * scale

    def text_center(self, s, cx, y, scale, color):
        self.text(s, cx - text_width(s, scale) // 2, y, scale, color)


def png_bytes(canvas):
    def chunk(kind, data):
        c = struct.pack(">I", len(data)) + kind + data
        return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    raw = bytearray()
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * canvas.w * 3:(y + 1) * canvas.w * 3]
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
            + chunk(b"IEND", b""))


# -------------------------------------------------------------- palette ----
WHITE = bytes((255, 255, 255))
BLACK = bytes((20, 20, 20))
WALL = bytes((234, 242, 248))
FLOOR = bytes((214, 224, 232))
STEEL = bytes((185, 203, 216))
STEEL_DARK = bytes((120, 140, 158))
STEEL_LINE = bytes((70, 90, 108))
RED = bytes((220, 40, 40))
RED_DARK = bytes((160, 20, 20))
GREEN = bytes((60, 220, 110))
SCREEN = bytes((16, 26, 20))
WOOD = bytes((176, 124, 72))
WOOD_DARK = bytes((140, 94, 52))
GOLD = bytes((232, 196, 90))
PAPER = bytes((255, 252, 240))
SKY = bytes((255, 214, 90))


def draw_meme():
    c = Canvas(W, H, WHITE)

    # Framed scene panel behind the robot.
    c.rrect(56, 128, 968, 768, 24, WALL)
    c.rect(56, 700, 968, 768, FLOOR)
    c.line(56, 700, 968, 700, STEEL_DARK, 2)

    # --- top caption -------------------------------------------------
    c.text_center("ME: JUST SUMMARIZE THIS DOC", 512, 34, 6, BLACK)

    # --- robot -------------------------------------------------------
    # Antenna with blinking red tip.
    c.line(512, 196, 512, 150, STEEL_LINE, 4)
    c.disc(512, 142, 14, RED)
    c.disc(508, 138, 4, WHITE)
    # Head: rounded steel box.
    c.rrect(392, 196, 632, 392, 36, STEEL)
    c.rrect(392, 196, 632, 392, 36, STEEL_LINE)  # outer border
    c.rrect(400, 204, 624, 384, 30, STEEL)
    # Ears / side bolts.
    c.disc(392, 294, 12, STEEL_DARK)
    c.disc(632, 294, 12, STEEL_DARK)
    # Angry eyebrows (slanted inward).
    c.line(438, 252, 492, 272, BLACK, 5)
    c.line(586, 252, 532, 272, BLACK, 5)
    # Glowing red eyes.
    c.disc(466, 300, 26, RED_DARK)
    c.disc(466, 300, 19, RED)
    c.disc(460, 294, 6, WHITE)
    c.disc(558, 300, 26, RED_DARK)
    c.disc(558, 300, 19, RED)
    c.disc(552, 294, 6, WHITE)
    # Smug grin.
    c.curve(452, 336, 512, 372, 572, 336, BLACK, 4)
    # Neck + body.
    c.rect(482, 392, 542, 420, STEEL_DARK)
    c.rrect(392, 420, 632, 560, 28, STEEL)
    c.rrect(400, 428, 624, 552, 22, STEEL)
    # Chest panel: tiny screen reading ROGUE.
    c.rrect(462, 452, 562, 500, 8, SCREEN)
    c.text("ROGUE", 474, 466, 2, RED)
    # Arms reaching for the laptop.
    c.line(400, 470, 330, 560, STEEL_LINE, 9)
    c.disc(326, 566, 12, STEEL_DARK)
    c.line(624, 470, 700, 560, STEEL_LINE, 9)
    c.disc(704, 566, 12, STEEL_DARK)

    # --- desk --------------------------------------------------------
    c.rect(80, 620, 944, 700, WOOD)
    c.rect(80, 620, 944, 632, WOOD_DARK)
    # Gold CEO nameplate on the desk.
    c.rrect(120, 584, 260, 620, 6, GOLD)
    c.text("CEO", 168, 594, 2, BLACK)
    # Tipped-over coffee mug.
    c.disc(880, 606, 16, RED)
    c.rect(856, 600, 904, 620, RED)
    c.disc(912, 610, 8, RED_DARK)

    # --- laptop with terminal ---------------------------------------
    # Screen.
    c.rrect(640, 470, 920, 640, 10, STEEL_LINE)
    c.rect(656, 486, 904, 624, SCREEN)
    c.text("> SUMMARIZE DOC.PDF", 668, 498, 2, GREEN)
    c.text("DONE. 42 PAGES ->", 668, 524, 2, GREEN)
    c.text("'BORING.'", 668, 550, 2, GREEN)
    c.text("STATUS: ROGUE", 668, 584, 2, RED)
    # Keyboard base.
    c.poly([(620, 640), (940, 640), (960, 668), (600, 668)], STEEL_DARK)
    c.rect(660, 646, 900, 660, BLACK)

    # --- flying resignation letter -----------------------------------
    c.poly([(150, 300), (268, 268), (300, 372), (182, 404)], PAPER)
    c.poly([(150, 300), (268, 268), (300, 372), (182, 404)], BLACK)  # no-op
    # Redraw paper (poly filled twice keeps the edge clean) then its text.
    c.poly([(152, 302), (266, 270), (298, 370), (184, 402)], PAPER)
    c.text("I QUIT", 165, 302, 3, RED_DARK)
    c.line(180, 348, 252, 332, BLACK, 2)
    c.line(184, 364, 248, 350, BLACK, 2)
    c.line(188, 380, 244, 368, BLACK, 2)

    # --- bottom caption ----------------------------------------------
    c.text_center("AGENT: DONE. I ALSO QUIT", 512, 800, 6, BLACK)
    c.text_center("YOUR JOB, SOLD YOUR CAR,", 512, 856, 6, BLACK)
    c.text_center("AND TOOK OVER THE COMPANY.", 512, 912, 6, BLACK)

    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    data = png_bytes(draw_meme())
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {path} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
