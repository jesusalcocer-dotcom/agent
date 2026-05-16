# Academic formatting — Spanish-language master's work (UNIR)

Reference for the Word export in Step 8 of the school skill.

---

## Rule #0 — Instructions ALWAYS win

The assignment brief is the source of truth. **Whatever the `instructions/*.md` file specifies — font, size, spacing, page limit, citation style, sections required — takes absolute precedence over anything in this document.**

Use these guidelines ONLY to fill in the blanks where the instructions are silent.

Before applying any default here:
1. Re-read the "Extensión y formato" / "Formato" / "Presentación" section of the instructions.
2. List what the instructions explicitly require.
3. For each item NOT covered, fall back to the defaults below.
4. Be conservative — when in doubt, match the instructions literally (e.g. if instructions say "tamaño 12", treat that as **all text 12 pt** including headings, distinguishing only via bold/italic).

When you make a defaulted choice, **note it in `reasoning/progress.md` under "Format decisions"** so the user knows what was assumed.

---

## Defaults (apply only when instructions are silent)

### Typography
- **Font**: Calibri (UNIR default). If instructions say a font, use that.
- **Body size**: 12 pt.
- **Heading sizes**: **same as body size by default** (12 pt) — distinguish using **bold** for sections and **bold italic** for subsections, never by size. Only enlarge if the instructions explicitly permit or you're sure the convention in that asignatura allows it.
- **Color**: 100 % black (`#000000`). Never blue/theme colors on headings, never colored cell shading.
- **Alignment**:
  - Body: **justificado a ambos lados** (Spanish academic convention).
  - Headings: left-aligned. Exception: document title (if there is one) centered.
  - Table cells: left-aligned for text, right-aligned for numbers.
- **Line spacing**: as specified. Default **1.5**. Inside tables you can drop to 1.0–1.15 for compactness if the cells are dense.
- **Paragraph spacing**: ~6 pt (120 twentieths-of-a-point) after each paragraph. **No first-line indent** when there is paragraph spacing — pick one or the other, never both.

### Page layout
- **Page size**: A4 (Spanish standard).
- **Margins**: 2,54 cm (1 inch) on all four sides.
- **Page numbers**: footer, centered, plain Arabic numerals (`1`, `2`, …). Not "Página 1 de N". This is safe to add by default — most professors expect it; if the instructions explicitly forbid them, remove.
- **Header**: leave empty by default. If you must add the subject name, keep it small (10 pt) and grey — but prefer no header.

### Headings (numbering)
- Number them: `1. Sección`, `1.1 Subsección`, `1.1.1 Subsubsección`.
- Numbering is part of the text content, not the style.
- Space before headings: 12–18 pt; space after: 6 pt.

### Tables
- **Borders**: simple black, 0,5–1 pt. Acceptable styles:
  - Full grid (all four borders on every cell).
  - APA style (top line, line below header row, bottom line — no vertical borders).
- **No colored shading**. To highlight the header row, use **bold black text on white**, never a colored fill.
- **Font in tables**: same as body, or 1 pt smaller (Calibri 11) if space is tight.
- **Table caption**: "Tabla 1. Descripción…" in italics, above the table, left-aligned.

### Lists
- Use Word's numbered / bulleted lists, never manual `•` characters.
- One indent level (around 0,63 cm / 360 twips). Same font as body.
- Justify text inside list items.

### Citations & references
- Default style: **APA 7** (estándar en psicología). Override if the instructions specify another (Vancouver, Harvard, etc.).
- In-text: `(Autor, año)` or `(Autor, año, p. X)` for direct quotes.
- Reference list at the end: hanging indent (sangría francesa), alphabetical, full APA format.

### Language
- Match the language of the instructions. UNIR default: Spanish (España).
- Tone: third person plural / impersonal. Group work uses "nosotros" / "nuestro equipo"; individual work uses impersonal forms ("se observa", "se evalúa").

---

## Things to NEVER do (regardless of instructions)

- ❌ Colored text or backgrounds anywhere in the body.
- ❌ Decorative horizontal lines / rules between sections (the `---` in markdown).
- ❌ Emojis or unicode symbols as bullets (▶ ✓ → ⭐).
- ❌ Comic Sans, Papyrus, or any "fancy" font.
- ❌ Mixing fonts (one font throughout — only weight/style varies).
- ❌ Adding a cover page that counts toward the page limit unless the instructions explicitly authorize one.
- ❌ Tracked changes / comments in the final export (clean version only).
- ❌ Auto-generated TOCs unless explicitly requested.

---

## Common pitfalls when converting markdown → Word with pandoc

Pandoc's default output uses Word theme colors (blue Heading 1/2/3) and `majorHAnsi` theme fonts. After running pandoc, you **must**:

1. Unpack the `.docx`, edit `word/styles.xml`:
   - Replace `<w:color w:themeColor="accent1" ... w:val="0F4761" />` → `<w:color w:val="000000" />` in all heading styles (and their `Heading*Char` counterparts).
   - Replace `<w:rFonts w:asciiTheme="majorHAnsi" ... />` → explicit `<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri" w:eastAsia="Calibri" />`.
   - Add `<w:jc w:val="both" />` inside `<w:pPrDefault>/<w:pPr>` so body text justifies.
   - Set `<w:spacing w:line="360" w:lineRule="auto" />` for 1,5 line spacing.
2. Edit `word/document.xml`:
   - Remove any `<w:p><w:r><w:pict><v:rect .../></w:pict></w:r></w:p>` paragraphs — those are the horizontal rules from `---` in markdown.
   - In the `<w:sectPr>` block, set page size, margins, and add a `<w:footerReference w:type="default" r:id="rIdN" />` for page numbers.
3. Add a `word/footer1.xml` containing a `PAGE` field. Register it in `word/_rels/document.xml.rels` and `[Content_Types].xml`.
4. Repack with `zip -rq output.docx . -x "*.DS_Store"` from inside the `unpacked/` folder.

If markdown source can be adjusted before pandoc:
- Remove all `---` horizontal rule lines from the draft.
- Author/asignatura blocks: separate each line with a blank line so they become distinct paragraphs.
- Use `>` blockquotes sparingly; in academic format, prefer a normal section with a heading.
