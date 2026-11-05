#!/usr/bin/env python3
"""Regenerate EPUB body pages + endnotes.xhtml from the LaTeX sources used for the PDF."""
"""Usage: python3 assets/bin/tex2epub.py --write   (run after tangling the org file)"""
import re, html, sys, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..') + os.sep
TXT = ROOT + 'html/OEBPS/Text/'

PALI = [("tex/pali/pubbakicca.tex", "pubbakicca"), ("tex/pali/nidan'uddesa.tex", "nidanuddeso"),
        ("tex/pali/parajika.tex", "parajika"), ("tex/pali/sanghadisesa.tex", "sanghadisesa"),
        ("tex/pali/aniyata.tex", "aniyata"), ("tex/pali/nissaggiya-pacittiya.tex", "nissaggiyapacittiya"),
        ("tex/pali/pacittiya.tex", "pacittiya"), ("tex/pali/patidesaniya.tex", "patidesaniya"),
        ("tex/pali/sekhiya.tex", "sekhiya"), ("tex/pali/adhikaranasamatha.tex", "adhikaranasamatha"),
        ("tex/pali/patimokkhanitthana.tex", "patimokkhanitthana")]
ENG = [("tex/english/%s.tex" % f, f) for f in
       "preliminary-duties introduction disqualifications community-meetings uncertain-cases forfeiture-expiations "
       "expiations acknowledgments trainings settlements conclusion".split()]
POST = [("tex/post/%s.tex" % f, f) for f in "pubba-bhaga siluddesa tayana-gatha ovada-patimokkha".split()]
ORDER = PALI + ENG + POST + [("tex/in-brief.tex", None)]

NOTE_RE = re.compile(r"\\makeatletter\s*\\hyperlink\{[^}]*\}\\Hy@raisedlink\{\\hypertarget\{[^}]*\}\{\}\{\\pagenote\{%?\s*"
                     r"\\hypertarget\{[^}]*\}\{\\hyperlink\{[^}]*\}\{")


def close_brace(s, i, depth=1):
    while i < len(s):
        c = s[i]
        if c == '\\':
            i += 2
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError('unbalanced')


def arg(s, i):
    """s[i] == '{' -> (content, index after closing brace)"""
    assert s[i] == '{', s[i:i + 30]
    j = close_brace(s, i + 1)
    return s[i + 1:j], j + 1


def strip_conditionals(s):
    # keep the A5 branch, drop the 9x13 branch
    s = re.sub(r'\\ifninebythirteenversion\b(.*?)\\fi\b', '', s, flags=re.S)
    s = re.sub(r'\\ifafiveversion\b(.*?)\\fi\b', r'\1', s, flags=re.S)
    return s


def inline(t, in_note=False):
    """LaTeX inline -> XHTML string. Notes are pre-extracted as \x00N\x00 markers."""
    t = re.sub(r'(?<!\\)%[^\n]*\n?', '', t)
    out = []
    i = 0
    while i < len(t):
        c = t[i]
        if c == '\\':
            m = re.match(r'\\([A-Za-z@]+\*?|[\s\S])', t[i:])
            if not m:
                out.append(' '); i += 1; continue
            cmd = m.group(1)
            i += len(m.group(0))
            if cmd in ('textit', 'emph', 'textbf', 'textsc', 'mbox', 'suttaRef', 'textls', 'textls*'):
                while i < len(t) and t[i] == ' ':
                    i += 1
                a, i = arg(t, i)
                inner = inline(a, in_note)
                out.append({'textit': '<em>%s</em>', 'emph': '<em>%s</em>', 'textbf': '<strong>%s</strong>',
                            'textsc': '<span style="font-variant: small-caps;">%s</span>'}.get(cmd, '%s') % inner)
            elif cmd in ('hspace', 'hspace*', 'vspace', 'vspace*', 'linkdest', 'label', 'chapterOpeningPage'):
                _, i = arg(t, i)
                if cmd == 'hspace*':
                    out.append('\u00a0')
            elif cmd in ('setsubsecheadstyle', 'setsecheadstyle'):
                _, i = arg(t, i)
            elif cmd in ('subsectionFmt', 'subsubsectionFmtalt', 'sectionFmt', 'else', 'fi'):
                pass
            elif cmd == 'hyperref':
                j = t.index(']', i)
                a, i = arg(t, j + 1)
                out.append(inline(a, in_note))
            elif cmd == 'pdfbookmark':
                if t[i] == '[':
                    i = t.index(']', i) + 1
                _, i = arg(t, i)
                _, i = arg(t, i)
            elif cmd == '\\':
                if i < len(t) and t[i] == '[':
                    i = t.index(']', i) + 1
                out.append('<br/>')
            elif cmd in ('anglebracketleft',):
                out.append('〈')
            elif cmd in ('anglebracketright',):
                out.append('〉')
            elif cmd == '&':
                out.append('&amp;')
            elif cmd in ('%', '#', '$', '_', '/'):
                out.append(cmd if cmd != '/' else '')
            elif cmd in (' ', '\n', '\t'):
                out.append(' ')
            elif cmd in ('thinspace', 'thickspace', 'medskip', 'smallskip', 'bigskip', 'clearpage', 'noindent',
                         'centering', 'hfill', 'par', 'makeatletter', 'makeatother', 'relax', 'null'):
                if cmd in ('smallskip', 'medskip') and in_note:
                    out.append('<br/>')
                # control words swallow following spaces
            else:
                raise ValueError('unhandled \\%s near %r' % (cmd, t[max(0, i - 60):i + 40]))
            if re.match(r'[A-Za-z@]', cmd) and cmd not in ('textit', 'emph', 'textbf', 'textsc', 'mbox', 'suttaRef',
                                                           'hyperref', 'textls', 'textls*'):
                while i < len(t) and t[i] in ' \t':
                    i += 1
        elif c in '{}':
            i += 1
        elif c == '~':
            out.append('\u00a0'); i += 1
        elif t.startswith('---', i):
            out.append('—'); i += 3
        elif t.startswith('--', i):
            out.append('–'); i += 2
        elif t.startswith('``', i):
            out.append('“'); i += 2
        elif t.startswith("''", i):
            out.append('”'); i += 2
        elif c == '`':
            out.append("'"); i += 1
        elif c == '<':
            out.append('&lt;'); i += 1
        elif c == '>':
            out.append('&gt;'); i += 1
        elif c == '&':
            out.append('&amp;'); i += 1
        else:
            out.append(c); i += 1
    s = ''.join(out)
    s = re.sub(r'[ \t\n]+', ' ', s)
    s = re.sub(r' ?<br/> ?', '<br/> ', s)
    return s.strip() if not in_note else re.sub(r'^(<br/> ?)+|(<br/> ?)+$', '', s.strip()).strip()


class Book:
    def __init__(self):
        self.notes = []  # (num, html, file)
        self.label_file = {}
        self.warn = []

    def extract_notes(self, s, epub):
        res = ''
        i = 0
        while True:
            m = NOTE_RE.search(s, i)
            if not m:
                res += s[i:]
                break
            res += s[i:m.start()]
            j = close_brace(s, m.end())
            note = s[m.end():j]
            k = j + 1
            while k < len(s) and s[k] == '}':
                k += 1
            if s.startswith('\\makeatother', k):
                k += len('\\makeatother')
            n = len(self.notes) + 1
            self.notes.append([n, inline(note, True), epub])
            res += '\x00%d\x00' % n
            i = k
        return res


def heading_html(level, title, hyper, label, book, attrs):
    t = title
    if hyper:
        f = book.label_file.get(hyper)
        if not f:
            book.warn.append('no file for label ' + hyper)
            t = title
        else:
            t = '<a href="%s.xhtml#%s">%s</a>' % (f, hyper, title)
    if label:
        t += '<a id="%s"></a>' % label
    return '<h%d%s>%s</h%d>' % (level, attrs, t, level)


def old_headings(epub):
    s = open(TXT + epub + '.xhtml', encoding='utf-8').read()
    return [(int(m.group(1)), m.group(2), m.group(0)) for m in re.finditer(r'<h([1-3])([^>]*)>.*?</h\1>', s, re.S)]


def convert(book, path, epub, keep_h1=True, text=None):
    s = text if text is not None else open(ROOT + path, encoding='utf-8').read()
    s = re.sub(r'(?m)^[ \t]*%.*\n', '', s)
    s = strip_conditionals(s)
    s = book.extract_notes(s, epub)
    olds = old_headings(epub) if epub and os.path.exists(TXT + epub + '.xhtml') else []
    old_by_level = {1: [o for o in olds if o[0] == 1], 2: [o for o in olds if o[0] == 2], 3: [o for o in olds if o[0] == 3]}
    used = {1: 0, 2: 0, 3: 0}
    blocks = []
    # tokenise into structural pieces
    pos = 0
    env_stack = []
    para = []
    title_for_head = None

    def flush():
        txt = ''.join(para).strip()
        para.clear()
        if not txt:
            return
        for chunk in re.split(r'\n[ \t]*\n', txt):
            h = render_inline_with_notes(chunk, book, epub)
            if not h or h == '<br/>':
                continue
            env = env_stack[-1] if env_stack else None
            if env == 'center':
                blocks.append('<p style="text-align: center;">%s</p>' % h)
            elif env == 'intro':
                blocks.append('<p class="intro">%s</p>' % h)
            elif env == 'outro':
                blocks.append('<p class="outro">%s</p>' % h)
            elif env in ('hanging-indent',):
                blocks.append('<p class="pali-hang">%s</p>' % h)
            elif env in ('hanging-indent-together',):
                blocks.append('<p class="pali-hang-together">%s</p>' % h)
            elif env in ('enumerate', 'packedenumerate', 'itemize'):
                items = [x for x in re.split(r'\s*•ITEM•\s*', h) if x.strip()]
                for it in items:
                    blocks.append('  <li>%s</li>' % it)
            else:
                blocks.append('<p>%s</p>' % h)

    tok = re.compile(r'\\(begin|end)\{([a-z\-]+)\}|\\(chapter|section|subsection|subsubsection)(\*?)\{|\\item\b\s*|\\suttaRef\{')
    while True:
        m = tok.search(s, pos)
        if not m:
            para.append(s[pos:])
            break
        para.append(s[pos:m.start()])
        if m.group(1):
            flush()
            env = m.group(2)
            if m.group(1) == 'begin':
                env_stack.append(env)
                if env in ('enumerate', 'packedenumerate', 'itemize'):
                    blocks.append('<ol>')
            else:
                env_stack.pop()
                if env in ('enumerate', 'packedenumerate', 'itemize'):
                    blocks.append('</ol>')
            pos = m.end()
        elif m.group(3):
            flush()
            a, pos = arg(s, m.end() - 1)
            lm = re.match(r'\s*\\label\{([^}]*)\}', s[pos:])
            label = None
            if lm:
                label = lm.group(1)
                pos += lm.end()
            hm = re.match(r'\\hyperref\[([^]]*)\]\{(.*)\}$', a.strip(), re.S)
            hyper = None
            title = a
            if hm:
                hyper, title = hm.group(1), hm.group(2)
            title = inline(title)
            cmd = m.group(3)
            if cmd == 'chapter':
                continue
            level = {'section': 1, 'subsection': 2, 'subsubsection': 3}[cmd]
            old = old_by_level[level][used[level]] if used[level] < len(old_by_level[level]) else None
            used[level] += 1
            if level == 1 and old is not None and keep_h1:
                # keep the old h1 wrapper (links/anchors), replace text
                oh = old[2]
                inner = re.sub(r'^<h1[^>]*>|</h1>$', '', oh)
                am = re.match(r'(<a href="[^"]*">)(.*?)(</a>.*)$', inner, re.S)
                if am:
                    blocks.append('<h1%s>%s%s%s</h1>' % (old[1], am.group(1), title, am.group(3)))
                else:
                    rest = re.findall(r'<a id="[^"]*"></a>', inner)
                    blocks.append('<h1%s>%s%s</h1>' % (old[1], title, ''.join(rest)))
                blocks.append('<hr/>')
            else:
                attrs = old[1] if old is not None else ''
                if old is None:
                    book.warn.append('%s: new h%d %s (no old heading to take id/class from)' % (epub, level, title))
                blocks.append(heading_html(level, title, hyper, label, book, attrs))
                if level == 1:
                    blocks.append('<hr/>')
        elif m.group(0).startswith('\\item'):
            para.append('•ITEM•')
            pos = m.end()
        else:  # suttaRef
            flush()
            a, pos = arg(s, m.end() - 1)
            blocks.append('<p style="text-align: right;">%s</p>' % inline(a))
    flush()
    for lv in (1, 2, 3):
        if used[lv] != len(old_by_level[lv]):
            book.warn.append('%s: h%d count tex=%d epub=%d' % (epub, lv, used[lv], len(old_by_level[lv])))
    return blocks


def render_inline_with_notes(chunk, book, epub):
    parts = re.split(r'\x00(\d+)\x00', chunk)
    out = ''
    for k, p in enumerate(parts):
        if k % 2 == 0:
            if not p:
                continue
            h = inline(p)
            # keep a single space where the source had one at a note boundary
            if out and re.match(r'^(\{\}|\\thinspace)?\s', p) and h and not out.endswith(' ') and not h.startswith('<br/>'):
                h = ' ' + h
            out += h
        else:
            n = int(p)
            out += '<a id="en%d" href="endnotes.xhtml#en%dappendix"><sup>%d</sup></a>' % (n, n, n)
    out = re.sub(r'\s+', ' ', out).strip()
    out = re.sub(r'(<br/>\s*)+$', '', out).strip()
    out = re.sub(r'^(<br/>\s*)+', '', out).strip()
    out = re.sub(r'(<br/> ?)+(?=</)', '', out)
    return out


def page(title, blocks):
    body = '\n\n'.join('  ' + b if not b.startswith('  ') else b for b in blocks)
    body = body.replace('  <ol>\n\n', '  <ol>\n').replace('\n\n  </ol>', '\n  </ol>')
    return ('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n\n'
            '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">\n<head>\n'
            '  <title>%s</title>\n  <link href="../Styles/main.css" type="text/css" rel="stylesheet"/>\n</head>\n\n'
            '<body>\n%s\n</body>\n</html>\n') % (title, body)


def sections(path):
    s = open(ROOT + path, encoding='utf-8').read()
    idx = [m.start() for m in re.finditer(r'\\section\{', s)]
    return [s[a:b] for a, b in zip(idx, idx[1:] + [len(s)])]


def jobs():
    J = []
    for p, e in PALI + ENG:
        J.append((p, e, None))
    for p, e in POST:
        J.append((p, e, None))      # Pāli section followed by its English translation
    secs = sections('tex/in-brief.tex')
    J.append(('tex/in-brief.tex', 'sankhittapatimokkhuddeso-nitthana', secs[0]))
    J.append(('tex/in-brief.tex', 'patimokkha-in-brief-conclusion', secs[1]))
    return J


def main(write=False):
    book = Book()
    for p, e, txt in jobs():
        s = txt if txt is not None else open(ROOT + p, encoding='utf-8').read()
        for l in re.findall(r'\\label\{([^}]*)\}', s):
            book.label_file.setdefault(l, e)
    out = {}
    for p, e, txt in jobs():
        blocks = convert(book, p, e, text=txt)
        title = e
        h1 = next((b for b in blocks if b.startswith('<h1')), None)
        if h1:
            title = re.sub(r'<[^>]+>', '', h1)
        out[e] = page(title, blocks)
    # endnotes
    en = ['<h1><a style="font-style:normal;" href="nav.xhtml">Endnotes</a></h1>']
    for n, h, f in book.notes:
        en.append('<p><a id="en%dappendix" href="%s.xhtml#en%d"><sup>%d</sup></a> %s</p>' % (n, f, n, n, h))
    out['endnotes'] = page('Endnotes', en)
    for w in book.warn:
        print('WARN', w)
    print('notes:', len(book.notes))
    if write:
        for e, h in out.items():
            open(TXT + e + '.xhtml', 'w', encoding='utf-8').write(h)
    return out


if __name__ == '__main__':
    main('--write' in sys.argv)
