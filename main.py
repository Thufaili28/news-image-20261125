#!/usr/bin/env python3
"""Sum up 25 November 2026 world news in one image.

Rewritten from scratch on 25 Nov 2026 in this session.
Standard library only (no Pillow, no network). Writes a deterministic
1024x1024 PNG to /output/entry.png, falling back to output/entry.png.
All text is drawn with an embedded 5x7 bitmap font, scaled up.
"""
import binascii
import os
import struct
import zlib

W, H = 1024, 1024
BG = (255, 255, 255)
CARD = (242, 244, 247)
ACCENT = (0, 90, 180)
TEXT = (17, 24, 39)
MUTED = (75, 85, 99)
GOLD = (251, 191, 36)
DARK = (17, 24, 39)

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
}

# Six stories for 25 November 2026, in the order they appear on the card.
HEADLINES = [
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
    """A flat RGB pixel buffer with rectangle and bitmap-text drawing."""

    def __init__(self):
        self.buf = bytearray(BG * W * H)

    def rect(self, x, y, w, h, color):
        x0, x1 = max(0, x), min(W, x + w)
        y0, y1 = max(0, y), min(H, y + h)
        if x0 >= x1 or y0 >= y1:
            return
        px = bytes(color)
        for yy in range(y0, y1):
            base = (yy * W + x0) * 3
            for xx in range(x0, x1):
                i = (yy * W + xx) * 3
                self.buf[i:i + 3] = px

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


def draw():
    c = Canvas()
    # Header band
    c.rect(0, 0, W, 110, DARK)
    c.rect(0, 110, W, 4, ACCENT)
    c.text(40, 20, "WORLD NEWS", 7, (255, 255, 255))
    c.text(40, 78, "25 NOVEMBER 2026", 3, ACCENT)
    c.rect(830, 24, 154, 56, GOLD)
    c.text(848, 38, "25 NOV", 3, (0, 0, 0))
    # Six story cards
    y = 124
    for kicker, title, body in HEADLINES:
        c.rect(32, y, 960, 132, CARD)
        c.rect(32, y, 8, 132, ACCENT)
        c.text(62, y + 12, kicker, 2, ACCENT)
        c.text(62, y + 36, title, 4, TEXT)
        ly = y + 82
        for line in c.wrap(body, 3, 880)[:2]:
            c.text(62, ly, line, 3, MUTED)
            ly += 26
        y += 142
    # Footer
    c.text(40, 988, FOOTER, 2, MUTED)
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
