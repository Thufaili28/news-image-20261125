#!/usr/bin/env python3
"""Sum up 25 November 2026 world news in one image (v4).

World map plus 18 stories, every story with its own drawn icon.
Standard library only (no Pillow, no network). Writes a deterministic
1024x1024 PNG to /output/entry.png, falling back to output/entry.png.
All text and pictures are drawn with an embedded 5x7 bitmap font and
simple flat shapes (rects, circles, lines).
"""
import binascii
import os
import struct
import zlib

W, H = 1024, 1024
BG = (255, 255, 255)
CARD = (242, 244, 247)
CHIPBG = (238, 242, 247)
ACCENT = (0, 90, 180)
TEXT = (17, 24, 39)
MUTED = (75, 85, 99)
GOLD = (251, 191, 36)
DARK = (17, 24, 39)
NAVY = (13, 27, 48)
MAPDOT = (56, 120, 190)
MAPTITLE = (148, 197, 255)
ORANGE = (249, 115, 22)

# 5x7 bitmap font, '1' = pixel on
FONT = {
    'A': ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    'B': ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    'C': ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    'D': ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    'E': ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    'F': ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    'G': ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    'H': ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    'I': ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    'J': ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    'K': ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    'L': ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    'M': ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    'N': ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    'O': ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    'P': ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    'Q': ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    'R': ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    'S': ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    'T': ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    'U': ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    'V': ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    'W': ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    'X': ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    'Y': ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    'Z': ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    '0': ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    '1': ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    '2': ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    '3': ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    '4': ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    '5': ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    '6': ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    '7': ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    '8': ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    '9': ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    ' ': ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    '.': ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ',': ["00000", "00000", "00000", "00000", "01100", "00100", "01000"],
    '-': ["00000", "00000", "00000", "01110", "00000", "00000", "00000"],
    ':': ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    '%': ["11001", "11010", "00010", "00100", "01000", "01011", "10011"],
    '/': ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    '(': ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ')': ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    '*': ["00000", "10101", "01110", "11111", "01110", "10101", "00000"],
    '+': ["00000", "00100", "00100", "01110", "00100", "00100", "00000"],
}

# Coarse dotted world map, 96 columns x 26 rows, '#' = land.
# Rows run north to south, columns west to east (equirectangular).
MAP = [
    "........" "..##.##." ".##....." "........" "........" "........" "........" ".##.##.." "##..##.#" "#.##...." ".##....." "........",
    "......##" "########" "########" "##...###" "###....." "........" "########" "########" "########" "########" "########" "##......",
    ".....###" "########" "########" "#####..." "........" ".......#" "########" "########" "########" "########" "########" "###.....",
    ".......#" "########" "########" "####...." ".....###" "########" "########" "########" "########" "########" "########" "##......",
    "........" "########" "########" "##......" ".....###" "######.." "########" "########" "########" "########" "#######." "........",
    "........" ".#######" "########" "###....." "......##" "#####..." ".#######" "########" "########" "########" "######.." "........",
    "........" "..######" "########" "#......." "....####" "########" "##.#####" "########" "########" "########" "####...." "........",
    "........" "....####" "####...." "........" "...#####" "########" "########" "....####" "########" "###.####" "###....." "........",
    "........" "........" ".......#" "#######." "....####" "########" "########" "#......#" "########" ".#######" "##......" "........",
    "........" "........" "........" "########" "#......." ".....###" "########" "#####..." "........" "....#.##" ".##.##.#" "........",
    "........" "........" "........" ".#######" "##......" "......##" "########" "####...." "........" "......##" "##.##.##" "###.....",
    "........" "........" "........" ".#######" "##......" ".......#" "########" "###....." "........" "........" "........" "........",
    "........" "........" "........" "..######" "#......." ".......#" "########" "##......" "........" "........" "........" "........",
    "........" "........" "........" "..######" "........" "........" "########" "#......." "........" "........" "........" "........",
    "........" "........" "........" ".######." "........" "........" "########" "........" "........" ".......#" "########" "#.......",
    "........" "........" "........" ".#####.." "........" "........" ".######." "........" "........" "......##" "########" "##......",
    "........" "........" "........" "#####..." "........" "........" ".#####.." "........" "........" ".......#" "########" "#.......",
    "........" "........" "........" "####...." "........" "........" "........" "........" "........" "........" "#######." "...##...",
    "........" "........" ".......#" "###....." "........" "........" "........" "........" "........" "........" "........" "........",
    "........" "........" ".......#" "##......" "........" "........" "........" "........" "........" "........" "........" "........",
    "........" "........" "........" "........" "........" "........" "........" "........" "........" "........" "........" "........",
    "........" "........" "........" "........" "........" "........" "........" "........" "........" "........" "........" "........",
    "........" "........" "........" "........" "........" "........" "........" "........" "........" "........" "........" "........",
    "........" "........" "........" "........" "........" "........" "........" "........" "........" "........" "........" "........",
    "........" "........" "........" "........" "........" "........" "........" "........" "........" "........" "........" "........",
    "........" ".#######" "########" "##..####" "########" ".#######" "########" "###..###" "########" "########" "#######." "........",
]

# Numbered dots on the map: (digit, longitude, latitude)
LOCATIONS = [
    ("1", -122, 37),   # Santa Clara, USA
    ("2", 28, 60),     # Gulf of Finland
    ("3", 19, 52),     # Poland
    ("4", 84, 28),     # Nepal
    ("5", 43, 15),     # Yemen
    ("6", -75, 10),    # Cartagena, Colombia
    ("7", -17, 14),    # Senegal
    ("8", 116, 40),    # Beijing, China
]

# Top stories: (icon, kicker, title, body)
TOP = [
    ("chip", "1 NVIDIA", "HUANG BACK AS CEO",
     "HUANG RETURNED AS NVIDIA CEO. SHARES JUMPED 30% THEN FELL "
     "AS LAWMAKERS QUESTIONED TRUMP'S ROLE."),
    ("ship", "2 UKRAINE", "ZELENSKIY CONFIRMS SHIP HIT",
     "ZELENSKIY CONFIRMED UKRAINE HIT THE RUSSIAN CARGO SHIP "
     "SPARTA II IN THE GULF OF FINLAND."),
    ("plane", "3 POLAND", "NATO PLANS AWACS BOOST",
     "NATO PLANS TO DEPLOY EARLY WARNING AIRCRAFT IN POLAND "
     "AFTER MISSILES CROSSED ITS AIRSPACE."),
    ("quake", "4 NEPAL", "QUAKE HITS KOSHI PROVINCE",
     "A 5.6 MAGNITUDE EARTHQUAKE HIT NEPAL'S KOSHI PROVINCE "
     "NEAR THE CHINESE BORDER."),
]

# Briefs: (icon, one-line text). Column 1 first, then column 2.
BRIEFS = [
    ("port", "YEMEN: SAUDI STRIKES HIT HODEIDAH PORT, HOOTHI DEATHS REPORTED"),
    ("crate", "TARIFFS: TRUMP TO UNVEIL NEW DUTIES ON 16 TRADE PARTNERS AFTER PROBE"),
    ("basket", "COLOMBIA: CARTAGENA SUPERMARKET HOSTAGES FREED, NO CASUALTIES"),
    ("trophy", "SENEGAL: COURT RESTORES SENEGAL AS AFRICA CUP CHAMPIONS"),
    ("rocket", "SPACE: PAKISTAN'S FIRST ASTRONAUT REACHES CHINA'S SPACE STATION"),
    ("shirt", "BANGLADESH: GARMENT MINIMUM WAGE UP 36% AFTER WEEKS OF PROTESTS"),
    ("mine", "INDONESIA: RESCUERS SEARCH FOR DOZENS TRAPPED IN FLOODED MINE"),
    ("island", "PACIFIC: SOLOMON ISLANDS NAME AUSTRALIA TOP SECURITY PARTNER"),
    ("phone", "HUAWEI: CHINESE TECH GIANT FOUND GUILTY IN US TRADE SECRETS CASE"),
    ("scales", "MYANMAR: WORLD COURT RULES ON ROHINGYA GENOCIDE CASE"),
    ("windmill", "NETHERLANDS: COURT KEEPS BINDING CLIMATE TARGETS IN FORCE"),
    ("ballot", "SPAIN: GOVERNMENT HEADS FOR A SNAP ELECTION"),
    ("capitol", "USA: DEMOCRATS WIN HOUSE MAJORITY OF AT LEAST 259 SEATS"),
    ("skyline", "HONG KONG: CITY MARKS ONE YEAR SINCE THE TAI PO FIRE"),
]

FOOTER = "SOURCES: ONE TURN, DAILY EDITION, HORIZON, BBC, BLOOMBERG, AP * 25 NOV 2026"


def png_chunk(typ, data):
    body = struct.pack(">I", len(data)) + typ + data
    return body + struct.pack(">I", binascii.crc32(typ + data) & 0xFFFFFFFF)


def save_png(path, pixels):
    raw = b"".join(
        b"\x00" + bytes(pixels[y * W * 3:(y + 1) * W * 3]) for y in range(H)
    )
    png = b"\x89PNG\r\n\x1a\n"
    png += png_chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += png_chunk(b"IDAT", zlib.compress(raw, 9))
    png += png_chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)


class Canvas:
    """A flat RGB pixel buffer with shapes and bitmap-text drawing."""

    def __init__(self):
        self.buf = bytearray(BG * W * H)

    def px(self, x, y, color):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        x0, x1 = max(0, x), min(W, x + w)
        y0, y1 = max(0, y), min(H, y + h)
        if x0 >= x1 or y0 >= y1:
            return
        px = bytes(color)
        for yy in range(y0, y1):
            base = (yy * W + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i:i + 3] = px

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.px(xx, yy, color)

    def line(self, x0, y0, x1, y1, color, thick=2):
        # Bresenham, stamping a small circle at each step for thickness.
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        r = max(1, thick // 2)
        while True:
            self.circle(x0, y0, r, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def tri(self, x0, y0, x1, y1, x2, y2, color):
        # Filled triangle via scanline over the bounding box.
        minx, maxx = min(x0, x1, x2), max(x0, x1, x2)
        miny, maxy = min(y0, y1, y2), max(y0, y1, y2)
        d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if d == 0:
            return
        for yy in range(miny, maxy + 1):
            for xx in range(minx, maxx + 1):
                a = ((y1 - y2) * (xx - x2) + (x2 - x1) * (yy - y2)) / d
                b = ((y2 - y0) * (xx - x2) + (x0 - x2) * (yy - y2)) / d
                c = 1 - a - b
                if a >= 0 and b >= 0 and c >= 0:
                    self.px(xx, yy, color)

    def text(self, x, y, s, scale, color):
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch, FONT[" "])
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    if bit == "1":
                        self.rect(cx + gx * scale, y + gy * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx

    @staticmethod
    def text_w(s, scale):
        return len(s) * 6 * scale

    def wrap(self, s, scale, max_w):
        lines, cur = [], ""
        for word in s.split():
            trial = (cur + " " + word).strip()
            if self.text_w(trial, scale) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


def draw_icon(c, name, x, y, s):
    """Draw a mini scene for one story inside an s-by-s chip at (x, y).

    Icon art is laid out in a 100x100 unit box and scaled to s.
    """
    # Chip background and border
    c.rect(x, y, s, s, CHIPBG)
    b = max(1, s // 50)
    border = (203, 213, 225)
    c.rect(x, y, s, b, border)
    c.rect(x, y + s - b, s, b, border)
    c.rect(x, y, b, s, border)
    c.rect(x + s - b, y, b, s, border)

    u = s / 100.0

    def X(v):
        return x + int(v * u)

    def Y(v):
        return y + int(v * u)

    def S(v):
        return max(1, int(v * u))

    def R(rx, ry, rw, rh, color):
        c.rect(X(rx), Y(ry), S(rw), S(rh), color)

    def C(cx, cy, r, color):
        c.circle(X(cx), Y(cy), max(1, S(r)), color)

    def L(x0, y0, x1, y1, color, thick=3):
        c.line(X(x0), Y(y0), X(x1), Y(y1), color, max(1, S(thick)))

    def T(x0, y0, x1, y1, x2, y2, color):
        c.tri(X(x0), Y(y0), X(x1), Y(y1), X(x2), Y(y2), color)

    grey = (156, 163, 175)
    dgrey = (107, 114, 128)
    dark2 = (31, 41, 55)
    brown = (180, 120, 60)
    dbrown = (146, 104, 58)
    red = (220, 38, 38)
    green = (22, 163, 74)
    white = (255, 255, 255)

    if name == "chip":
        R(36, 16, 6, 12, GOLD)
        R(58, 16, 6, 12, GOLD)
        R(36, 72, 6, 12, GOLD)
        R(58, 72, 6, 12, GOLD)
        R(16, 36, 12, 6, GOLD)
        R(16, 58, 12, 6, GOLD)
        R(72, 36, 12, 6, GOLD)
        R(72, 58, 12, 6, GOLD)
        R(28, 28, 44, 44, dark2)
        R(40, 40, 20, 20, (96, 165, 250))
    elif name == "ship":
        R(38, 42, 22, 14, white)
        R(43, 34, 12, 8, dgrey)
        R(18, 56, 64, 8, dgrey)
        R(24, 64, 52, 7, grey)
        R(32, 71, 36, 6, dark2)
        for wx in (20, 36, 52, 68, 84):
            C(wx, 86, 5, ACCENT)
        R(10, 90, 80, 4, ACCENT)
    elif name == "plane":
        T(14, 44, 6, 30, 22, 44, dgrey)
        R(14, 44, 58, 12, grey)
        T(72, 44, 90, 50, 72, 56, grey)
        T(38, 56, 60, 56, 48, 74, dgrey)
        C(46, 39, 8, (229, 231, 235))
        R(44, 44, 4, 4, dgrey)
        for wx in (24, 34, 56, 64):
            C(wx, 50, 2, (219, 234, 254))
    elif name == "quake":
        T(4, 80, 34, 32, 60, 80, grey)
        T(40, 80, 64, 40, 90, 80, dgrey)
        pts = [(47, 18), (40, 34), (51, 48), (42, 64), (49, 84)]
        for i in range(len(pts) - 1):
            L(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], ORANGE, 4)
        R(70, 68, 16, 12, brown)
        T(66, 68, 78, 58, 90, 68, red)
    elif name == "port":
        R(22, 16, 6, 62, dark2)
        R(22, 16, 60, 6, dark2)
        L(70, 22, 70, 38, dark2, 3)
        R(62, 38, 17, 12, ORANGE)
        R(38, 64, 46, 14, red)
        R(38, 50, 32, 14, ACCENT)
    elif name == "crate":
        R(22, 28, 56, 48, brown)
        R(46, 28, 8, 48, dbrown)
        R(22, 48, 56, 8, dbrown)
        C(35, 40, 4, white)
        C(65, 64, 4, white)
        L(62, 38, 38, 66, white, 3)
    elif name == "basket":
        L(34, 46, 50, 27, dark2, 3)
        L(50, 27, 66, 46, dark2, 3)
        R(24, 46, 52, 8, (217, 119, 6))
        R(28, 54, 44, 8, (217, 119, 6))
        R(32, 62, 36, 10, (180, 100, 4))
        C(36, 82, 4, dark2)
        C(64, 82, 4, dark2)
    elif name == "trophy":
        R(22, 24, 10, 6, GOLD)
        R(22, 24, 6, 14, GOLD)
        R(68, 24, 10, 6, GOLD)
        R(72, 24, 6, 14, GOLD)
        R(32, 18, 36, 30, GOLD)
        R(46, 48, 8, 12, (202, 138, 4))
        R(34, 60, 32, 8, (202, 138, 4))
        R(38, 24, 6, 16, (253, 224, 71))
    elif name == "rocket":
        T(50, 4, 39, 25, 61, 25, red)
        R(39, 25, 22, 34, (203, 213, 225))
        C(50, 37, 5, ACCENT)
        T(39, 48, 26, 68, 39, 60, red)
        T(61, 48, 74, 68, 61, 60, red)
        T(50, 78, 42, 59, 58, 59, ORANGE)
        T(50, 70, 46, 59, 54, 59, (253, 224, 71))
    elif name == "shirt":
        R(20, 34, 15, 19, (37, 99, 235))
        R(65, 34, 15, 19, (37, 99, 235))
        R(34, 34, 32, 44, (37, 99, 235))
        R(42, 34, 16, 7, (29, 78, 216))
    elif name == "mine":
        T(8, 82, 50, 26, 92, 82, dbrown)
        C(50, 58, 11, (31, 25, 18))
        R(39, 58, 22, 24, (31, 25, 18))
        L(28, 18, 50, 40, dgrey, 4)
        L(72, 18, 50, 40, dgrey, 4)
    elif name == "island":
        C(82, 20, 9, GOLD)
        R(24, 70, 52, 9, (240, 200, 110))
        C(24, 74, 5, (240, 200, 110))
        C(76, 74, 5, (240, 200, 110))
        L(50, 70, 55, 48, dbrown, 4)
        L(55, 48, 59, 38, dbrown, 4)
        for fx, fy in ((38, 30), (48, 25), (64, 26), (76, 34), (42, 40)):
            L(59, 38, fx, fy, green, 4)
    elif name == "phone":
        R(33, 12, 34, 68, dark2)
        R(37, 19, 26, 48, (147, 197, 253))
        C(50, 73, 3, white)
    elif name == "scales":
        R(47, 20, 6, 52, dark2)
        R(20, 17, 60, 6, dark2)
        L(28, 23, 19, 44, dark2, 2)
        L(28, 23, 37, 44, dark2, 2)
        R(15, 44, 26, 6, (202, 138, 4))
        L(72, 23, 63, 44, dark2, 2)
        L(72, 23, 81, 44, dark2, 2)
        R(59, 44, 26, 6, (202, 138, 4))
        R(35, 72, 30, 6, dark2)
    elif name == "windmill":
        R(40, 46, 20, 36, (168, 138, 100))
        R(43, 34, 14, 12, (168, 138, 100))
        R(45, 24, 10, 10, (168, 138, 100))
        for bx, by in ((33, 7), (67, 7), (33, 41), (67, 41)):
            L(50, 24, bx, by, dark2, 4)
        C(50, 24, 4, dark2)
        R(46, 66, 8, 16, (31, 25, 18))
    elif name == "ballot":
        R(36, 12, 28, 32, (203, 213, 225))
        L(43, 31, 49, 37, green, 4)
        L(49, 37, 61, 19, green, 4)
        R(24, 48, 52, 32, (100, 116, 139))
        R(30, 43, 40, 6, dark2)
    elif name == "capitol":
        R(48, 8, 4, 9, (96, 165, 250))
        R(42, 17, 16, 6, (96, 165, 250))
        R(38, 23, 24, 6, (96, 165, 250))
        R(33, 29, 34, 6, (96, 165, 250))
        R(24, 38, 52, 10, (59, 130, 246))
        R(24, 50, 52, 24, (37, 99, 235))
        for cx_ in (29, 39, 49, 59, 69):
            R(cx_, 53, 4, 18, white)
        R(19, 74, 62, 6, grey)
    elif name == "skyline":
        R(14, 44, 17, 38, dark2)
        R(35, 30, 19, 52, dark2)
        R(58, 40, 17, 42, dark2)
        R(78, 52, 13, 30, dark2)
        for wx, wy in ((19, 52), (25, 64), (40, 40), (47, 54),
                       (40, 68), (63, 50), (69, 64), (82, 60)):
            R(wx, wy, 4, 5, (253, 224, 71))
        C(44, 21, 6, ORANGE)
        C(44, 21, 3, (253, 224, 71))
    else:
        C(50, 50, 16, ORANGE)


def draw():
    c = Canvas()
    # Header band
    c.rect(0, 0, W, 92, DARK)
    c.rect(0, 92, W, 4, ACCENT)
    c.text(36, 22, "WORLD NEWS IN ONE IMAGE", 5, (255, 255, 255))
    c.text(36, 64, "WEDNESDAY 25 NOVEMBER 2026", 3, ACCENT)
    c.rect(860, 18, 128, 56, GOLD)
    c.text(874, 32, "25 NOV", 3, (0, 0, 0))

    # Map panel
    c.rect(0, 100, W, 260, NAVY)
    c.text(36, 110, "WHERE IT HAPPENED", 2, MAPTITLE)
    cols = len(MAP[0])
    rows = len(MAP)
    ox, oy, step = 32, 134, 10
    for gy, row in enumerate(MAP):
        for gx, cell in enumerate(row):
            if cell == "#":
                c.circle(ox + gx * step, oy + gy * step, 3, MAPDOT)
    for digit, lon, lat in LOCATIONS:
        gx = round((lon + 180) / 360 * (cols - 1))
        gy = round((90 - lat) / 180 * (rows - 1))
        cx, cy = ox + gx * step, oy + gy * step
        c.circle(cx, cy, 7, ORANGE)
        c.text(cx - 2, cy - 3, digit, 1, (255, 255, 255))

    # Top story cards, 2x2, each with a big icon
    positions = [(32, 368), (516, 368), (32, 508), (516, 508)]
    for (icon, kicker, title, body), (x, y) in zip(TOP, positions):
        c.rect(x, y, 476, 132, CARD)
        c.rect(x, y, 8, 132, ACCENT)
        draw_icon(c, icon, x + 16, y + 14, 104)
        tx = x + 136
        c.text(tx, y + 12, kicker, 2, ACCENT)
        tscale = 3 if c.text_w(title, 3) <= 320 else 2
        c.text(tx, y + 34, title, tscale, TEXT)
        ly = y + 58
        for line in c.wrap(body, 2, 324)[:5]:
            c.text(tx, ly, line, 2, MUTED)
            ly += 18

    # Briefs heading
    c.text(36, 664, "AROUND THE WORLD IN BRIEF", 3, TEXT)
    c.rect(36, 690, 220, 4, ACCENT)

    # Briefs: 7 per column, each with a small icon
    for idx, (icon, text) in enumerate(BRIEFS):
        col = 0 if idx < 7 else 1
        row = idx if idx < 7 else idx - 7
        x = 36 if col == 0 else 524
        y = 700 + row * 38
        draw_icon(c, icon, x, y, 34)
        ly = y
        for line in c.wrap(text, 2, 420)[:2]:
            c.text(x + 44, ly, line, 2, TEXT)
            ly += 19

    # Footer
    c.text(36, 988, FOOTER, 2, MUTED)
    return c.buf


def main():
    pixels = draw()
    written = []
    here = os.path.dirname(os.path.abspath(__file__))
    targets = ["/output/entry.png",
               os.path.join(here, "output", "entry.png")]
    for path in targets:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            size = save_png(path, pixels)
            written.append(path)
            print(f"wrote {path} {size} bytes")
        except Exception as exc:  # keep going if /output is not writable
            print(f"skip {path}: {exc}")
    if not written:
        raise SystemExit("could not write any output")


if __name__ == "__main__":
    main()
