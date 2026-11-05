#!/usr/bin/env python3
"""Impose pages of the A5 PDF as an A6 booklet printed 4-up on A4, duplex.

Layout is the same as the user's reference booklet: each A4 side has a 2×2 grid
of A6 pages. Print double-sided, flip on the LONG edge, cut every sheet across
the middle, keep the top halves in sheet order (sheet 1 outermost) and put the
bottom halves inside them, also in sheet order; fold the whole stack in the
middle and staple. The pages then run 1, 2, 3 … in reading order.

Usage:
  python3 assets/bin/a6-booklet.py [SOURCE.pdf] [OUT.pdf] [PAGES]
PAGES is a comma-separated list of source page numbers / ranges, with "b" for a
blank page. The default "9-52,b,b,b,153" is the Pāli section (PDF pp. 9–52 = book
pp. 1–44; the titled Pāli chapter picture becomes the booklet's front cover), three
blank pages and the back cover: 48 pages, with even page numbers on the left.
"1,9-52,b,b,153" uses the book's front cover instead (even numbers then fall on the right).
The count is padded with blank pages to a multiple of 8 (one A4 sheet = 8 pages).
"""
import sys

from pypdf import PdfReader, PdfWriter, Transformation, PageObject
from pypdf.generic import ContentStream, NameObject, DecodedStreamObject

A4 = (595.276, 841.890)
A6 = (A4[0] / 2, A4[1] / 2)

DEFAULT_SRC = 'build/Ñāṇatusita_Bhikkhupātimokkha.pdf'
DEFAULT_OUT = 'build/Ñāṇatusita_Bhikkhupātimokkha-Pāli-A6-booklet.pdf'
DEFAULT_PAGES = '9-52,b,b,b,153'


def parse_pages(spec):
    out = []
    for part in spec.split(','):
        part = part.strip()
        if part == 'b':
            out.append(None)
        elif '-' in part:
            a, b = part.split('-')
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    while len(out) % 8:
        out.append(None)
    return out


def sides(n):
    """For an n-page booklet (n % 8 == 0) return, per A4 side, the booklet
    page indices (0-based) in the order TL, TR, BL, BR (None = nothing)."""
    m = n // 8                      # sheets
    q = n // 4                      # pages in the outer (top-strip) group's first half
    res = []
    for k in range(m):
        # top strips: outer group (pages 0..q-1 and n-q..n-1)
        # bottom strips: inner group (pages q..n-q-1)
        front = (n - 1 - 2 * k, 2 * k, n - q - 1 - 2 * k, q + 2 * k)
        back = (2 * k + 1, n - 2 - 2 * k, q + 1 + 2 * k, n - q - 2 - 2 * k)
        res.extend([front, back])
    return res


def marks():
    """Short ticks at the horizontal cut line and the vertical fold line."""
    w, h = A4
    t = 14
    ops = ['q', '0.6 G', '0.4 w']
    for x0, y0, x1, y1 in [(0, h / 2, t, h / 2), (w - t, h / 2, w, h / 2),        # cut
                           (w / 2, 0, w / 2, t), (w / 2, h - t, w / 2, h),        # fold
                           (w / 2, h / 2 - t / 2, w / 2, h / 2 + t / 2)]:
        ops.append('%.2f %.2f m %.2f %.2f l S' % (x0, y0, x1, y1))
    ops.append('Q')
    return ' '.join(ops).encode()


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
    out = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT
    spec = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_PAGES
    r = PdfReader(src)
    pages = parse_pages(spec)
    n = len(pages)
    w = PdfWriter()
    slots = [(0, A6[1]), (A6[0], A6[1]), (0, 0), (A6[0], 0)]   # TL, TR, BL, BR origins
    for side in sides(n):
        sheet = PageObject.create_blank_page(width=A4[0], height=A4[1])
        for (x, y), idx in zip(slots, side):
            p = pages[idx]
            if p is None:
                continue
            sp = r.pages[p - 1]
            sw, sh = float(sp.mediabox.width), float(sp.mediabox.height)
            s = min(A6[0] / sw, A6[1] / sh)
            ox = x + (A6[0] - sw * s) / 2
            oy = y + (A6[1] - sh * s) / 2
            sheet.merge_transformed_page(sp, Transformation().scale(s, s).translate(ox, oy))
        stream = DecodedStreamObject()
        stream.set_data(marks())
        ref = w._add_object(stream)
        w.add_page(sheet)
        pg = w.pages[-1]
        contents = pg.get('/Contents')
        from pypdf.generic import ArrayObject
        arr = ArrayObject()
        if contents is not None:
            c = contents.get_object()
            if isinstance(c, ArrayObject):
                arr.extend(c)
            else:
                arr.append(contents)
        arr.append(ref)
        pg[NameObject('/Contents')] = arr
    w.compress_identical_objects()
    with open(out, 'wb') as f:
        w.write(f)
    print('%s: %d booklet pages on %d A4 sheets (%d sides)' % (out, n, n // 8, n // 4))


if __name__ == '__main__':
    main()
