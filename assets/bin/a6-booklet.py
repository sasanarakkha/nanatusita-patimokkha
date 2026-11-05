#!/usr/bin/env python3
"""Impose an A6 booklet 4-up on A4, printed duplex.

Uses only the Python standard library and LaTeX (pdfpages), because the release CI
image has no pypdf and no pip.

Source: the native booklet build/booklet/booklet-a6-pages.pdf (main_a6booklet.tex: Pāli
Pātimokkha, Post-Pātimokkha recitations in Pāli, endnotes 1–8, front and back
covers). pdfpages scales its pages by 0.72 onto the A6 cells, so the text prints at 9 pt.

Layout is the same as the user's reference booklet: each A4 side has a 2×2 grid
of A6 pages. Print double-sided, flip on the LONG edge, cut every sheet across
the middle, keep the top halves in sheet order (sheet 1 outermost) and put the
bottom halves inside them, also in sheet order; fold the whole stack in the
middle and staple. The pages then run 1, 2, 3 … in reading order.

Usage:
  python3 assets/bin/a6-booklet.py [SOURCE.pdf] [OUT.pdf] [PAGES]
PAGES is "auto" (default: all pages, blank pages inserted before the last page,
the back cover, up to a multiple of 8), or a comma-separated list of source pages /
ranges with "b" for a blank page, e.g. "1,9-52,b,b,153" to impose straight from
the A5 book PDF. Lists are padded with blank pages to a multiple of 8.
The page count for "auto" is read from SOURCE's LaTeX log (same name, .log).
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

DEFAULT_SRC = 'build/booklet/booklet-a6-pages.pdf'
DEFAULT_OUT = 'build/Ñāṇatusita_Bhikkhupātimokkha-Pāli-A6-booklet.pdf'
DEFAULT_PAGES = 'auto'


def page_count(src):
    log = os.path.splitext(src)[0] + '.log'
    if os.path.exists(log):
        m = re.findall(r'Output written on .*?\((\d+) pages?', open(log, encoding='latin-1').read(), re.S)
        if m:
            return int(m[-1])
    if shutil.which('pdfinfo'):
        out = subprocess.run(['pdfinfo', src], capture_output=True, text=True).stdout
        m = re.search(r'^Pages:\s+(\d+)', out, re.M)
        if m:
            return int(m.group(1))
    sys.exit('a6-booklet: cannot determine the page count of %s (no LaTeX log, no pdfinfo)' % src)


def parse_pages(spec, total):
    if spec == 'auto':
        return list(range(1, total)) + [None] * ((-total) % 8) + [total]
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
    page indices (0-based) in the order TL, TR, BL, BR."""
    q = n // 4
    res = []
    for k in range(n // 8):
        res.append((n - 1 - 2 * k, 2 * k, n - q - 1 - 2 * k, q + 2 * k))          # front
        res.append((2 * k + 1, n - 2 - 2 * k, q + 1 + 2 * k, n - q - 2 - 2 * k))  # back
    return res


TEX = r'''\documentclass[a4paper]{article}
\usepackage{pdfpages}
\setlength{\unitlength}{1pt}
\begin{document}
\includepdf[pages={%(pages)s}, nup=2x2, noautoscale=false, delta=0 0, offset=0 0,
  picturecommand*={%%
    \linethickness{0.4pt}\color[gray]{0.6}%%
    \put(0,420.945){\line(1,0){14}}\put(581.276,420.945){\line(1,0){14}}%%   cut line
    \put(297.638,0){\line(0,1){14}}\put(297.638,827.89){\line(0,1){14}}%%   fold line
    \put(297.638,413.945){\line(0,1){14}}%%
  }]{%(src)s}
\end{document}
'''


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
    out = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT
    spec = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_PAGES
    pages = parse_pages(spec, page_count(src))
    n = len(pages)
    order = []
    for side in sides(n):
        order.extend('{}' if pages[i] is None else str(pages[i]) for i in side)
    tmp = tempfile.mkdtemp(prefix='a6-booklet-')
    tex = os.path.join(tmp, 'impose.tex')
    open(tex, 'w', encoding='utf-8').write(TEX % {'pages': ','.join(order), 'src': os.path.abspath(src)})
    r = subprocess.run(['lualatex', '-interaction=nonstopmode', '-halt-on-error', 'impose.tex'],
                       cwd=tmp, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(os.path.join(tmp, 'impose.pdf')):
        sys.stdout.write(r.stdout[-3000:])
        sys.exit('a6-booklet: imposition with pdfpages failed')
    shutil.move(os.path.join(tmp, 'impose.pdf'), out)
    shutil.rmtree(tmp, ignore_errors=True)
    print('%s: %d booklet pages on %d A4 sheets (%d sides)' % (out, n, n // 8, n // 4))


if __name__ == '__main__':
    main()
