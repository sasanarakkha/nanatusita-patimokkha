#!/usr/bin/env python3
"""Write the sources for the A6 Pāli booklet (main_a6booklet.tex) into tex/booklet/.

From the tangled tex/ files (run org-tangle first):
  pali.tex       the Pāli Pātimokkha (Pubbakicca … Pātimokkhaniṭṭhāna) without the
                 chapter-opening picture and without page breaks between sections
  post-pali.tex  the Pāli half of each Post-Pātimokkha recitation (the English
                 sections are left out), also without page breaks
"""
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
PALI = ["pubbakicca", "nidan'uddesa", "parajika", "sanghadisesa", "aniyata", "nissaggiya-pacittiya",
        "pacittiya", "patidesaniya", "sekhiya", "adhikaranasamatha", "patimokkhanitthana"]
POST = ["pubba-bhaga", "siluddesa", "tayana-gatha", "ovada-patimokkha"]


def run_on(s):
    """Drop forced page breaks and the chapter opener; sections run on."""
    s = re.sub(r'\\chapterOpeningPage\{[^}]*\}', '', s)
    s = re.sub(r'\\chapter\{[^}]*\}', '', s)
    s = re.sub(r'\\if(afive|ninebythirteen)version\\clearpage\\fi', '', s)
    s = re.sub(r'\\(clearpage|cleardoublepage|newpage)\b', r'\\par\\medskip', s)
    return s


def read(path):
    return open(os.path.join(ROOT, path), encoding='utf-8').read()


def main():
    out = os.path.join(ROOT, 'tex', 'booklet')
    os.makedirs(out, exist_ok=True)
    pali = '\n'.join(run_on(read('tex/pali/%s.tex' % f)) for f in PALI)
    post = []
    for f in POST:
        s = read('tex/post/%s.tex' % f)
        secs = [m.start() for m in re.finditer(r'\\section\{', s)]
        # keep everything before the second \section (the English translation),
        # dropping the \linkheadingto that belongs to that English heading
        part = s[:secs[1]] if len(secs) > 1 else s
        part = re.sub(r'\\linkheadingto\{[^}]*\}\s*$', '', part.rstrip()) + '\n'
        post.append(run_on(part))
    open(os.path.join(out, 'pali.tex'), 'w', encoding='utf-8').write(pali)
    open(os.path.join(out, 'post-pali.tex'), 'w', encoding='utf-8').write('\n'.join(post))
    print('wrote tex/booklet/pali.tex, tex/booklet/post-pali.tex')


if __name__ == '__main__':
    main()
