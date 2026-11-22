"""One page for one day: Saturday, 21 November 2026.

Standard-library-only program that paints a newspaper front page
summarising the world news of 21 November 2026 and encodes it as a
PNG called entry.png.

Everything is drawn into a plain pixel buffer with a small hand-made
5 by 7 bitmap alphabet, then the buffer is written out as a PNG with
zlib compression.  There is no network access, no randomness and no
clock reading, so repeated runs produce identical bytes.

The only place the program tries to write is the directory given by
MAKEFUN_OUTPUT_DIR, falling back to /output and then the current
working directory.  Every write attempt is guarded so a read-only
location is skipped instead of crashing the run.
"""

import os
import struct
import zlib

W = 1024
H = 1024

CREAM = (247, 242, 230)
INK = (22, 20, 18)
GREY = (82, 78, 70)
RED = (164, 28, 20)
BLUE = (20, 42, 92)
TEAL = (16, 92, 84)
GOLD = (196, 142, 32)
PANEL = (236, 228, 204)
PANEL2 = (226, 233, 238)
DARK = (12, 18, 36)
WHITE = (250, 248, 240)

GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10101", "10011", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "01010", "00100", "00100", "00100", "01010", "10001"),
    "Y": ("10001", "01010", "00100", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
}


GLYPHS_EXTRA = {
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10001", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
}


class Page:
    def __init__(self, w, h, colour):
        self.w = w
        self.h = h
        self.buf = bytearray(bytes(colour) * (w * h))

    def rect(self, x, y, w, h, colour):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(colour) * (x1 - x0)
        for yy in range(y0, y1):
            at = (yy * self.w + x0) * 3
            self.buf[at:at + len(row)] = row

    def outline(self, x, y, w, h, colour, t=2):
        self.rect(x, y, w, t, colour)
        self.rect(x, y + h - t, w, t, colour)
        self.rect(x, y, t, h, colour)
        self.rect(x + w - t, y, t, h, colour)

    def line(self, x, y, w, colour, t=2):
        self.rect(x, y, w, t, colour)


def text_width(text, scale):
    return len(text) * 6 * scale - scale if text else 0


def draw_text(page, x, y, text, scale, colour):
    cx = x
    for ch in text.upper():
        glyph = GLYPHS.get(ch)
        if glyph is None:
            glyph = GLYPHS_EXTRA.get(ch)
        if glyph is not None:
            for row_i, row in enumerate(glyph):
                for col_i, bit in enumerate(row):
                    if bit == "1":
                        page.rect(cx + col_i * scale, y + row_i * scale,
                                  scale, scale, colour)
        cx += 6 * scale
    return cx


def centred(page, y, text, scale, colour, cx=512):
    draw_text(page, cx - text_width(text, scale) // 2, y, text, scale, colour)


def wrap_lines(text, max_chars):
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if len(trial) <= max_chars:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_paragraph(page, x, y, text, scale, colour, max_chars, leading=11):
    for line_text in wrap_lines(text, max_chars):
        draw_text(page, x, y, line_text, scale, colour)
        y += 8 * scale + leading
    return y


def story(page, x, y, w, kicker, headline, body, accent):
    page.rect(x, y, w, 6, accent)
    draw_text(page, x, y + 14, kicker, 2, accent)
    yy = y + 38
    for line_text in wrap_lines(headline, max(10, w // 18)):
        draw_text(page, x, yy, line_text, 3, INK)
        yy += 26
    yy += 4
    draw_paragraph(page, x, yy, body, 2, GREY, max(16, w // 12), leading=5)
    return yy


def build_page():
    p = Page(W, H, CREAM)
    p.outline(10, 10, W - 20, H - 20, INK, 3)
    p.outline(18, 18, W - 36, H - 36, INK, 1)

    # Masthead
    centred(p, 34, "THE WORLD IN ONE PAGE", 6, INK)
    p.line(48, 86, W - 96, INK, 3)
    centred(p, 98, "SATURDAY  21 NOVEMBER 2026", 3, RED)
    centred(p, 128, "ALL THE DAY'S NEWS - ONE FRONT PAGE - EVERY REGION", 2, GREY)
    p.line(48, 152, W - 96, INK, 2)

    # Lead story: climate summit in Antalya
    p.rect(32, 164, W - 64, 150, DARK)
    draw_text(p, 52, 178, "CLIMATE - ANTALYA, TURKIYE", 2, GOLD)
    draw_text(p, 52, 202, "COP31 TALKS DEADLOCKED", 5, WHITE)
    draw_text(p, 52, 244, "OVER FOSSIL FUELS IN OVERTIME", 4, WHITE)
    draw_paragraph(p, 52, 284, "NEARLY 200 NATIONS, NO FINAL DEAL. DRAFT DROPS COAL, OIL AND GAS.", 2, (205, 210, 220), 78, leading=4)

    # Two major stories side by side
    story(p, 36, 330, 452, "THE HAGUE - WORLD COURT",
          "MYANMAR GUILTY OF ROHINGYA GENOCIDE",
          "THE WORLD COURT RULED MYANMAR COMMITTED GENOCIDE AGAINST THE ROHINGYA - A FIRST VERDICT AGAINST A STATE. FRANCE SEEKS A UN COUNCIL MEETING.", BLUE)
    story(p, 536, 330, 452, "MANAMA - BAHRAIN",
          "IRAN STRIKES BAHRAIN, FIRE AT INDUSTRIAL SITE",
          "IRAN SAID IT HIT US POSITIONS. BAHRAIN SAID THE ATTACK SET AN INDUSTRIAL SITE ABLAZE, NO ONE WAS HURT, AND OTHER ATTACKS WERE INTERCEPTED.", RED)

    p.line(48, 548, W - 96, INK, 2)

    # Second row
    story(p, 36, 562, 452, "GUASAVE, SINALOA - MEXICO",
          "MEXICO CAPTURES FBI MOST-WANTED CARTEL BOSS",
          "FORCES SEIZED EL CHAPO ISIDRO AFTER A SHOOT-OUT. VIOLENCE THAT FOLLOWED LEFT AT LEAST 11 DEAD IN SINALOA.", TEAL)
    story(p, 536, 562, 452, "KRYVYI RIH - UKRAINE",
          "RUSSIAN MISSILE HITS ZELENSKY HOMETOWN",
          "A MISSILE STRUCK THE CITY CENTRE, KILLING TWO AND WOUNDING DOZENS. UKRAINE HIT THE CRIMEA BRIDGE AGAIN.", GOLD)

    # Summit strip, two separate boxes
    p.rect(32, 756, 468, 62, PANEL)
    p.outline(32, 756, 468, 62, INK, 1)
    draw_text(p, 48, 766, "SHENZHEN SUMMIT", 3, BLUE)
    draw_paragraph(p, 48, 794, "TRUMP, XI AND PUTIN MEET AT APEC", 2, INK, 36, leading=2)
    p.rect(524, 756, 468, 62, PANEL2)
    p.outline(524, 756, 468, 62, INK, 1)
    draw_text(p, 540, 766, "EU - INDONESIA DEAL", 3, TEAL)
    draw_paragraph(p, 540, 794, "TRADE PACT SIGNED AFTER 10 YEARS", 2, INK, 36, leading=2)

    # Bottom grid: markets, quake, health
    draw_text(p, 36, 834, "MARKETS", 2, RED)
    draw_text(p, 36, 856, "WALL ST IN CORRECTION", 2, INK)
    draw_paragraph(p, 36, 880, "AI AND CHIP SELL-OFF ERASES NASDAQ 2026 GAINS IN ITS WORST WEEK SINCE 2020.", 2, GREY, 24, leading=4)
    draw_text(p, 356, 834, "PERU - ANDES", 2, RED)
    draw_text(p, 356, 856, "QUAKE 6.7 FELT IN LIMA", 2, INK)
    draw_paragraph(p, 356, 880, "STRONG QUAKE NEAR JUNIN AT 108 KM DEPTH. NO IMMEDIATE CASUALTIES REPORTED.", 2, GREY, 24, leading=4)
    draw_text(p, 676, 834, "BRAZIL - HEALTH HOPE", 2, TEAL)
    draw_text(p, 676, 856, "MOSQUITOES CUT DENGUE", 2, INK)
    draw_paragraph(p, 676, 880, "SPECIALLY BRED MOSQUITOES CUT DENGUE IN CHILDREN BY ABOUT 69% IN A BIG STUDY.", 2, GREY, 25, leading=4)

    # Footer ticker
    p.rect(32, 962, W - 64, 34, INK)
    draw_text(p, 44, 972, "SPORT: ENGLAND 37-12 NEW ZEALAND  +  ANTHROPIC RECORD DEBUT", 2, WHITE)
    centred(p, 1002 - 14, "", 1, GREY)
    return p


def encode_png(page):
    raw = bytearray()
    stride = page.w * 3
    for yy in range(page.h):
        raw.append(0)
        start = yy * stride
        raw.extend(page.buf[start:start + stride])
    compressed = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        return out + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", page.w, page.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", header)
    png += chunk(b"IDAT", compressed)
    png += chunk(b"IEND", b"")
    return png


def main():
    data = encode_png(build_page())
    candidates = []
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if out_dir:
        candidates.append(out_dir)
    candidates.append("/output")
    candidates.append(os.getcwd())
    written = []
    for folder in candidates:
        try:
            os.makedirs(folder, exist_ok=True)
            path = os.path.join(folder, "entry.png")
            with open(path, "wb") as handle:
                handle.write(data)
            written.append(path)
            break
        except Exception:
            continue
    if written:
        print("wrote", written[0], len(data), "bytes")


if __name__ == "__main__":
    main()


