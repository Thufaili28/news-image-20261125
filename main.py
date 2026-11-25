#!/usr/bin/env python3
"""Sum up 25 November 2026 world news in one image.

Built from scratch for the make.fun news-image-20261125 bounty.
Standard library only (binascii, os, struct, zlib), no network.
Writes a deterministic 1024x1024 PNG to /output/entry.png and to
output/entry.png next to this script. Text uses an embedded 5x7
bitmap font drawn by hand, scaled up per element.
"""
import binascii
import os
import struct
import zlib

W, H = 1024, 1024
WHITE = (255, 255, 255)
CARD = (242, 244, 247)
BLUE = (0, 90, 180)
DARK = (17, 24, 39)
MUTED = (75, 85, 99)
GOLD = (251, 191, 36)
BLACK = (0, 0, 0)

# Embedded 5x7 bitmap font. Each glyph is 7 rows of 5 chars; '1' = on.
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
}

STORIES = [
    ("1  NVIDIA", "HUANG APOLOGISES TO STAFF",
     "HUANG APOLOGISED TO NVIDIA STAFF AFTER HIS CEO COMEBACK. "
     "SHARES CLOSED 31.5% HIGHER."),
    ("2  POLAND", "NATO PLANS AWACS BOOST",
     "NATO PLANS TO DEPLOY EARLY WARNING AIRCRAFT IN POLAND "
     "AFTER MISSILES CROSSED ITS AIRSPACE."),
    ("3  TARIFFS", "TRUMP TO UNVEIL NEW TARIFFS",
     "TRUMP IS SET TO UNVEIL NEW IMPORT DUTIES AFTER A PROBE "
     "INTO EXCESS INDUSTRIAL CAPACITY."),
    ("4  UKRAINE", "ZELENSKIY CONFIRMS SHIP HIT",
     "ZELENSKIY CONFIRMED UKRAINE HIT THE RUSSIAN CARGO SHIP "
     "SPARTA II IN THE GULF OF FINLAND."),
    ("5  NEPAL", "QUAKE HITS KOSHI PROVINCE",
     "A 5.6 MAGNITUDE EARTHQUAKE HIT NEPAL'S KOSHI PROVINCE "
     "NEAR THE CHINESE BORDER."),
    ("6  YEMEN", "SAUDI STRIKES HIT YEMEN",
     "HOUTHIS REPORTED DEATHS AND MISSING PEOPLE AFTER SAUDI "
     "STRIKES IN SOUTH WESTERN YEMEN."),
]

FOOTER = "SOURCES: TOI, JAGRAN JOSH, NEWSREEL, BLOOMBERG, BBC * 25 NOV 2026"


def chunk(kind, payload):
    """One PNG chunk: length, type, data, CRC32 of type+data."""
    crc = binascii.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)


def encode_png(pixels):
    """Encode the RGB pixel buffer (W*H*3 bytes) as a PNG byte string."""
    scanlines = b"".join(
        b"\x00" + bytes(pixels[row * W * 3:(row + 1) * W * 3])
        for row in range(H)
    )
    out = b"\x89PNG\r\n\x1a\n"
    out += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    out += chunk(b"IDAT", zlib.compress(scanlines, 9))
    out += chunk(b"IEND", b"")
    return out


class Canvas:
    """Flat RGB framebuffer with rectangle fill and bitmap text."""

    def __init__(self, bg):
        self.px = bytearray(bg * (W * H))

    def fill_rect(self, x, y, w, h, color):
        left, right = max(0, x), min(W, x + w)
        top, bottom = max(0, y), min(H, y + h)
        if left >= right or top >= bottom:
            return
        rgb = bytes(color)
        for yy in range(top, bottom):
            offset = (yy * W + left) * 3
            for _ in range(left, right):
                self.px[offset:offset + 3] = rgb
                offset += 3

    def draw_text(self, x, y, text, scale, color):
        pen_x = x
        for ch in text.upper():
            glyph = FONT.get(ch, FONT[" "])
            for row_i, row in enumerate(glyph):
                for col_i, bit in enumerate(row):
                    if bit == "1":
                        self.fill_rect(pen_x + col_i * scale,
                                       y + row_i * scale,
                                       scale, scale, color)
            pen_x += 6 * scale
        return pen_x

    @staticmethod
    def measure(text, scale):
        return len(text) * 6 * scale

    def wrap_text(self, text, scale, max_width):
        lines = []
        current = ""
        for word in text.split():
            candidate = (current + " " + word).strip()
            if self.measure(candidate, scale) <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines


def render():
    img = Canvas(WHITE)
    # Header: dark band, blue rule, gold date box.
    img.fill_rect(0, 0, W, 110, DARK)
    img.fill_rect(0, 110, W, 4, BLUE)
    img.draw_text(40, 20, "WORLD NEWS", 7, WHITE)
    img.draw_text(40, 78, "25 NOVEMBER 2026", 3, BLUE)
    img.fill_rect(830, 24, 154, 56, GOLD)
    img.draw_text(848, 38, "25 NOV", 3, BLACK)
    # Story cards.
    y = 124
    for kicker, title, body in STORIES:
        img.fill_rect(32, y, 960, 132, CARD)
        img.fill_rect(32, y, 8, 132, BLUE)
        img.draw_text(62, y + 12, kicker, 2, BLUE)
        img.draw_text(62, y + 36, title, 4, DARK)
        line_y = y + 82
        for line in img.wrap_text(body, 3, 880)[:2]:
            img.draw_text(62, line_y, line, 3, MUTED)
            line_y += 26
        y += 142
    img.draw_text(40, 988, FOOTER, 2, MUTED)
    return img.px


def main():
    data = encode_png(render())
    here = os.path.dirname(os.path.abspath(__file__))
    destinations = ["/output/entry.png",
                    os.path.join(here, "output", "entry.png")]
    saved = []
    for dest in destinations:
        try:
            folder = os.path.dirname(dest)
            if folder:
                os.makedirs(folder, exist_ok=True)
            with open(dest, "wb") as fh:
                fh.write(data)
            saved.append(dest)
            print("wrote %s %d bytes" % (dest, len(data)))
        except OSError as exc:
            print("skip %s: %s" % (dest, exc))
    if not saved:
        raise SystemExit("no output could be written")


if __name__ == "__main__":
    main()
