# Ñāṇatusita's Bhikkhupātimokkha: notes for Claude

## Where the text lives
- **Single source of truth:** `nanatusita-patimokkha.tex.org`. Edit only this file for content.
- `python3 assets/bin/org-tangle.py nanatusita-patimokkha.tex.org` regenerates `tex/**` from it.
  Org blocks with no `:tangle` are not printed.
- PDF: `make pdf-a5`, `make pdf-9x13` (LuaLaTeX, `main.tex`, `anecdote.cls`, `A5.sty`/`9x13.sty`).
- EPUB: `python3 assets/bin/tex2epub.py --write` regenerates the body pages and `endnotes.xhtml`
  in `html/OEBPS/Text/` from `tex/`, numbering footnotes like the PDF. Then run `make epub`.
  `make epub` overwrites `copyright.xhtml` with today's date, so restore it before committing.
- Hand-maintained EPUB files (not generated): `abbreviations`, `copyright(.xhtml.tpl)`, `titlepage`,
  `nav`, `contents`, `content.opf`, the `cover-*.xhtml` pages.
- Check the EPUB: `java -jar /usr/bin/epubcheck <file>.epub`. The one OPF-003 warning about
  `contents.xhtml` is known and harmless.
- CI (`.github/workflows/building.yaml`) builds only on pushes to `main`.

## Workflow after any text change
1. Edit the org file.
2. Tangle.
3. Run `tex2epub.py --write`.
4. Build the PDF and check the affected pages.
5. Commit and push to the working branch (`claude/bold-pascal-lctmlq`; the user merges to `main`).

## Conventions and decisions so far
- Footnote macro pattern:
  `word\makeatletter\hyperlink{endnoteX-appendix}\Hy@raisedlink{...\pagenote{%`
  `...}}}}}\makeatother{} next`.
  Always use `\makeatother{} ` with a real space after it, never `\makeatother \thinspace `.
  The thinspace form glued words together and caused bad line breaks.
  Before a full stop, use `\makeatother.` with no space.
- Endnotes: the siglum is always "BhPm" (never "Bh Pm"); variant readings are in `\textit{}`.
  Pāli uses ṁ; ṃ is kept only in Sanskrit and Sinhala words.
- Spelling: always "pātimokkha" (t, not ṭ) in the main text, titles and English. Exception: endnotes that
  record *pāṭimokkhe* as another edition's reading (Mm Se, G, V), and the V manuscript title in the
  abbreviations, keep ṭ unless the user decides otherwise.
- Covers: `assets/illustrations/A5/{front,back}-cover-compressed.jpg` (the same files as in `html/OEBPS/Images/`).
  `main.tex` places them as the first and last pages of the digital A5 PDF only (`\ifdigitalversion`).
  The front cover is 864×1227 (EPUB `cover-image`).
- EPUB titles: every h1–h3 is a link and uses the PDF's link colour, #60291f (sbs-brown), in `main.css`.
  Pāli/English sections, vaggas and brief-recitation Levels link to their partner heading.
  `tex2epub.py` does this automatically (`PAIRS`, `link_partner_headings`). The Post-Pātimokkha headings link Pāli ↔ English within their page
  (e.g. `pubba-bhaga.xhtml#pubba-bhaga-english`), matching the PDF. Don't link to `contents.xhtml`:
  it isn't in the manifest, so epubcheck reports RSC-008.
- PDF heading links: `\linkheadingto{label}` before a \section/\subsection makes that title link to
  `label` (anecdote.cls `\headinglinktarget`; default is the table of contents). Every Pāli section, vagga,
  Level and rule heading links to its English counterpart and back. Vagga labels: np-/pc-/sekh-vaggaN ↔
  forf-exp-/exp-/trainings-vaggaN. Starred headings (Levels) need `\phantomsection` before them.
- Chapter-opening pictures carry their part title (as in the contents page), in the style of the
  lettering painted on the Appendix picture. Regenerate them with `python3 assets/bin/section-titles.py`,
  which reads the untitled originals in `assets/illustrations/untitled/` and uses Cinzel Medium
  (`assets/fonts/cinzel`, OFL). The Pāli picture (the user's 768×1376 image) is scaled to page width
  (2.3×), moved down 150 px for the title and trimmed at the bottom. The English picture (the user's
  848×1264 image of the western monk with the book on a stand) is scaled to page width (2.06×) and
  trimmed at the bottom, with no shift. The painted pseudo-text on both book pages is blurred into faint,
  unreadable lines (`ILLEGIBLE` regions in `section-titles.py`, in the original images' pixel coordinates).
  The Appendix picture already had its title painted in, so it is not regenerated.
- A6 Pāli booklet: `make booklet-a6`. `assets/bin/booklet-sources.py` writes `tex/booklet/` (generated,
  git-ignored) from the tangled files: the Pāli Pātimokkha and the Pāli half of each Post-Pātimokkha
  recitation, with sections running on (no \clearpage) and no chapter opener. `main_a6booklet.tex` typesets
  them with the A5 design on a 145.83×205.56 mm page (A6 ÷ 0.72), so that after scaling by 0.72 the body
  prints at exactly 9 pt. Only endnotes 1–8 (Pubbakicca) are kept; all other markers are dropped. The notes
  are also 9 pt (12.5/14.5 in source units), and the front and back covers are included: 48 pages = 6 A4
  sheets. `assets/bin/a6-booklet.py` imposes it 4-up on A4 in the layout of the user's reference booklet
  ("auto" page list: blank pages go before the back cover). Print duplex, flip on the long edge, cut across
  the middle, nest the bottom halves inside the top halves, fold, staple. If the text grows past 48 pages,
  the build gives 56 (7 sheets).
  Every release includes the booklet: `make all` (the CI default) also runs `booklet-a6`, warning instead of
  failing if it can't be built. Intermediate pages go to `build/booklet/`; the release file is
  `build/Ñāṇatusita_Bhikkhupātimokkha-Pāli-A6-booklet.pdf`.
- The user's copy of Ñāṇatusita's *The Bhikkhu Pātimokkha: A Word by Word Translation* (BPS 2014) is
  copyrighted. Never commit it; use it only as a reference for checking.
- English spelling decisions: clothweavers, sheepwool, extraordinary, ninefold, "rains bathing-cloth".
  Pāli: sammāsambuddhena (unhyphenated). Pāc 91 keeps "Vassikasāṭikāsikkhāpada" (user's decision).
- `main.tex` includes `tex/pali/nidan'uddesa.tex`; the old `nidan'uddeso.tex` was stale and is deleted.
- Chapter-opening images: `assets/illustrations/{A5,9x13}/{pali,english,post-patimokkha,appendix}-compressed.jpg`.
  Copies are in `html/OEBPS/Images/`. They are 1748×2480, upscaled from 1024 px, so print quality is limited.
- Post-Pātimokkha recitations: each has a Pāli section followed by its English section
  (Preliminary Part, The Summary on Virtue, On Protection, The Pātimokkha Exhortation).
  The English text is the user's own translation; keep its wording as given. The "restrain of the Pātimokkhā"
  phrasing is intended, not a typo.
- Saṅkhittapātimokkh'uddesa-niṭṭhāna (Appendix): Levels 1–4 are subsections under that title.
  The English page "The Pātimokkha Recitation in Brief Conclusion" mirrors them. Level 4 is the standard brief conclusion.
  - Recited sections use "uddiṭṭhā …"; the rest use "Sutā kho pan'āyasmantehi …".
  - The English uses "Heard by the venerables have been …".
  - "pañcasattati" has its long footnote only in Level 1 (the user removed the identical copies in
    Levels 2–4, formerly notes 546–548). The English says "the seventy-five cases related to the training".
  - Use only the book's own Pāḷi and English phrasing. Add no commentarial terms such as *sāvetabbaṃ*.
- Year in copyright and edition: 2026. The ISBN is still a placeholder (000-0-00000-000-0).
- Known unfixed item: `tex/abbreviations` has Ñd before Mv, and Sanne after SVibh, out of alphabetical order.

## User preferences
Direct, concise, technical. State uncertainty and give a confidence score. Do not auto-agree.
Flag possible errors and ask; don't silently "fix" the user's own translations.
