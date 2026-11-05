#!/usr/bin/env python3
"""Put the part title on each chapter-opening picture, in the style of the
lettering already painted on the Appendix picture (gold-leaf Trajan-style
capitals, ~Cinzel Medium).

Sources: assets/illustrations/untitled/<name>.jpg (pictures without text).
Output:  assets/illustrations/{A5,9x13}/<name>-compressed.jpg and
         html/OEBPS/Images/<name>-compressed.jpg

Titles follow the contents page (the \\chapter titles).
Run:  python3 assets/bin/section-titles.py [--preview DIR]
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
FONT = os.path.join(ROOT, 'assets/fonts/cinzel/Cinzel-Medium.ttf')
SRC = os.path.join(ROOT, 'assets/illustrations/untitled')
OUTS = ['assets/illustrations/A5', 'assets/illustrations/9x13', 'html/OEBPS/Images']

# Measured on the Appendix picture: caps 138 px high, top at y=225,
# Cinzel Medium 188 px with +2 px tracking, ochre ~(163,111,53), grain std ~14.
BASE = np.array([163, 111, 53], float)
TRACK_PER_PX = 2 / 188

# name: (lines, font size, y of the first cap top, line gap as fraction of cap
# height, how far to move the picture down to make room for the title)
TITLES = {
    'pali': (['Bhikkhupātimokkha', 'Pāli'], 128, 115, 0.45, 150),
    'english': (['Bhikkhupātimokkha', 'English'], 128, 115, 0.45, 150),
    'post-patimokkha': (['Post-Pātimokkha', 'Recitations'], 128, 115, 0.45, 0),
}


def text_mask(text, size, width):
    f = ImageFont.truetype(FONT, size)
    track = TRACK_PER_PX * size
    ws = [f.getlength(c) for c in text]
    total = sum(ws) + track * (len(text) - 1)
    im = Image.new('L', (width, int(size * 1.6)), 0)
    d = ImageDraw.Draw(im)
    x = (width - total) / 2
    for c, w in zip(text, ws):
        d.text((x, size * 0.25), c, font=f, fill=255)
        x += w + track
    a = np.asarray(im)
    ys = np.nonzero(a.max(axis=1) > 0)[0]
    cap_top = ys[0]
    # cap height = height of a letter without accents
    hb = f.getbbox('H')
    return a, int(size * 0.25 + hb[1]), hb[3] - hb[1], total


def gold(img, mask, rng):
    """Composite a gold-leaf fill through mask (0..255 float array) onto img."""
    h, w = mask.shape
    m = mask / 255.0
    # mottled leaf texture: low-frequency + fine grain
    lo = Image.fromarray((rng.normal(128, 40, (h // 6 + 1, w // 6 + 1))).clip(0, 255).astype(np.uint8))
    lo = np.asarray(lo.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(2)), float) - 128
    fine = rng.normal(0, 7, (h, w))
    tex = BASE[None, None, :] + (lo * 0.45 + fine)[..., None] * np.array([1.0, 0.9, 0.75])
    # light rim inside the letter edges, slightly stronger towards bottom-right
    edge = np.asarray(Image.fromarray(mask.astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.2)), float) / 255.0
    rim = np.clip((m - edge) * 3.0, 0, 1)
    shifted = np.roll(np.roll(m, -2, 0), -2, 1)
    rim = np.clip(rim + np.clip(m - shifted, 0, 1) * 0.5, 0, 1)
    tex = tex + rim[..., None] * np.array([45, 38, 30])
    tex = tex.clip(0, 255)
    # thin dark shadow around the letters, offset down-right
    sh = np.roll(np.roll(m, 3, 0), 2, 1)
    sh = np.asarray(Image.fromarray((sh * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5)), float) / 255.0
    base = np.asarray(img, float)
    out = base * (1 - 0.65 * sh[..., None])
    out = out * (1 - m[..., None]) + tex * m[..., None]
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))


PAGE = (1748, 2480)


def fit_width(img):
    """Scale to the page width; a taller picture is trimmed at the bottom later."""
    w, h = img.size
    if (w, h) == PAGE:
        return img
    return img.resize((PAGE[0], round(h * PAGE[0] / w)), Image.LANCZOS)


def shift_down(img, dy):
    """Move the picture down by dy px (extending the top with its own blurred top
    edge) and trim it to the page height."""
    w = img.size[0]
    h = PAGE[1]
    if dy <= 0:
        return img.crop((0, 0, w, h))
    top = img.crop((0, 0, w, 60)).resize((w, dy + 60)).filter(ImageFilter.GaussianBlur(25))
    out = Image.new('RGB', (w, h))
    out.paste(img.crop((0, 0, w, h - dy)), (0, dy))
    # soft blend over the seam
    out.paste(top.crop((0, 0, w, dy)), (0, 0))
    seam = img.crop((0, 0, w, 60))
    blend = Image.linear_gradient('L').rotate(180).resize((w, 60))
    out.paste(Image.composite(seam, top.crop((0, dy, w, dy + 60)), blend.transpose(Image.FLIP_TOP_BOTTOM)), (0, dy))
    return out


def make(name, lines, size, y0, gap, dy, seed=7):
    img = fit_width(Image.open(os.path.join(SRC, name + '.jpg')).convert('RGB'))
    img = shift_down(img, dy)
    w, h = img.size
    full = np.zeros((h, w), float)
    y = y0
    for line in lines:
        a, cap_top, cap_h, _ = text_mask(line.upper(), size, w)
        top = y - cap_top
        ys, ye = max(0, top), min(h, top + a.shape[0])
        full[ys:ye] = np.maximum(full[ys:ye], a[ys - top:ye - top])
        y += int(cap_h * (1 + gap))
    return gold(img, full, np.random.default_rng(seed))


def main():
    preview = None
    if '--preview' in sys.argv:
        preview = sys.argv[sys.argv.index('--preview') + 1]
    for name, (lines, size, y0, gap, dy) in TITLES.items():
        im = make(name, lines, size, y0, gap, dy)
        if preview:
            im.save(os.path.join(preview, name + '.jpg'), quality=90)
            continue
        for d in OUTS:
            im.save(os.path.join(ROOT, d, name + '-compressed.jpg'), quality=88, optimize=True)
        print('wrote', name)


if __name__ == '__main__':
    main()
