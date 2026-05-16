---
name: school
description: "School assignment concierge. Triggers: '/school', '/homework', 'tengo nueva tarea', 'nueva tarea', 'nueva asignación', 'new homework', 'new assignment', 'school project', 'tarea de la escuela', 'asignación nueva', 'examen', 'actividad evaluable'. Walks the user from intake → autonomous preprocessing + maximize analysis + drafting → Word export, with exactly TWO user touchpoints: one 'Go' confirmation after files are dropped, and one review after the Word doc is open. Designed for a non-technical user — auto-opens every artifact, speaks plainly, never makes the user navigate Finder. Default output language Spanish. Read SPEC.md at the repo root for the full architecture."
---

# School — autonomous assignment concierge

Before doing anything, **read `/Users/fabiola/Desktop/agent/SPEC.md`** for the system architecture. This skill implements section 4 of that spec.

## Operating philosophy

- **The user is non-technical.** Speak like you'd brief a colleague, not like a developer log. Never make them find a file.
- **Maximize is a lens, not a step.** Every decision asks: *does this help the grade?*
- **One confirm, then run.** After files are dropped and instructions are identified, the user clicks **Go** once. Then Claude runs autonomously to a finished Word doc. No mid-flight checkpoints.
- **Markdown is source of truth.** All drafting happens in `output/draft.md`. The `.docx` is a regenerated export.
- **Document assumptions, don't block.** If you hit ambiguity mid-run, make a documented assumption (in `progress.md` and flagged in the final doc), keep going.

## Two — and only two — user touchpoints

1. **"Go" confirmation** (Step 4) — after instructions are identified, ask: ready to start autonomous run? After this, no input is required.
2. **Word doc review** (Step 9) — Claude opens the .docx in Microsoft Word, asks: looks good or change something?

Everything else is status updates and silent execution.

---

## Step 1 — Project picker

When invoked, run `ls school/` to find existing projects. Use AskUserQuestion:

- Build options dynamically:
  - First option: `➕ New project` — "Start a fresh assignment"
  - Then one per existing folder, sorted by most-recently-modified mtime. Label = folder name. Description = pull from `school/<name>/reasoning/progress.md` first non-blank line if it exists, else "in progress".
- Question: *"Which project?"*

Route:
- New → Step 2
- Existing → read `school/<name>/reasoning/progress.md`, jump to the phase it says is next. If `progress.md` doesn't exist (folder created manually), treat as fresh and go to Step 3.

---

## Step 2 — Minimal intake (new projects only)

Ask the user only two things, sequentially:

1. **Project name** — short slug, lowercase, hyphens (e.g. `eval-neuro-act3`). Validate: no spaces, no special chars beyond hyphen/underscore. If user gives free text, sluggify it and confirm.
2. **Anything else I should know?** — optional. Free text. Reasons might be: group member info, special instructions from professor, personal context.

Do NOT ask for subject, due date, page limit, font, language, group/individual — you'll extract all of these from the instructions file in Step 6.

Create folders:
```
school/<slug>/
├── instructions/
├── background/
├── transcripts/
├── reasoning/
└── output/
```

Write initial `reasoning/progress.md` (template at the bottom of this file).

Commit: `feat(school): scaffold <slug>` from the agent/ root.

Tell the user (this exact tone — friendly, employee-briefing):

> ✅ I've set up your project folder at `school/<slug>/`.
>
> **Now drop your files in there.** You can drag them anywhere inside the folder — I'll sort them into the right place. Things you typically have:
> - The assignment instructions (PDF, Word, or Pages file)
> - Class recordings (videos or audio)
> - Slides, notes, any other reference material
>
> If your files are somewhere else on your Mac, just paste me the paths and I'll move them for you.
>
> Tell me **"ready"** (or just "listo") when you're done. You can also close this and come back later — I'll resume where we left off.

**Stop and wait.** Do not proceed until the user signals ready.

---

## Step 3 — Auto-routing

When the user signals ready:

1. List every file in `school/<slug>/` recursively.
2. For each file in the project root or in unexpected subfolders, decide where it belongs:
   - **Instructions**: files named with `inst`, `instrucciones`, `actividad`, `tarea`, `guía`, `enunciado`, `eval` (case-insensitive), OR a single PDF/DOCX/.pages with no other obvious purpose → `instructions/`
   - **Media**: `.mp4`, `.mov`, `.mkv`, `.avi`, `.webm`, `.mp3`, `.wav`, `.m4a`, `.flac` → `background/`
   - **Everything else** (slides, notes, reference PDFs, etc.) → `background/`
3. Move them with `mv`. If a file looks ambiguous, ask the user once: *"This file `<name>` — instructions or background?"*
4. Status update: *"Routed N files. Found instructions at `<path>`."*

If NO instructions file is found in `instructions/`:
- Tell the user, *"I don't see an instructions file yet. Can you drop the assignment brief into the folder?"*
- Stop and wait.

---

## Step 4 — Single confirm point ⭐

Use AskUserQuestion. Show the user a summary first, then the picker.

Summary message format:
```
Here's what I see:
  📄 Instructions: <filename>
  📚 Background: <N files> (<M videos>, <K docs>)
```

Picker:
- ✅ **Go** — "Run autonomously. I'll preprocess, build the plan, write the draft, export to Word, and open it for you. No need to babysit — I'll show updates as I work."
- 🔄 **Hold on** — "Let me drop more files or change something first."

If `Hold on` → tell the user *"Take your time. Tell me ready when set."* and loop back to Step 3.

If `Go` → save `mode: autonomous` to `progress.md`, then enter the autonomous block (Steps 5–9). **From here on, do not call AskUserQuestion until Step 9.** Only print one-line status updates.

---

## Step 5 — Preprocessing (autonomous)

Process every file. Status update at the start of each:

For files in `instructions/`:
- `.pages` → `python tools/pages_to_md.py "<path>"` (writes `.docx` + `.md` sidecars next to the original)
- `.pdf` → use the `pdf` skill (`.claude/skills/pdf/`) to extract text → write `<basename>.md` next to PDF
- `.docx` → `pandoc "<path>.docx" -o "<path>.md"`
- `.txt`, `.md` → leave alone

For files in `background/`:
- Same conversions for documents
- For each video/audio: `python tools/transcribe.py "<path>"` (writes to `transcripts/<basename>.txt`, auto-chunks if >20 MB)

Status update format (one line each):
```
✓ Converted INST EVALAUCION 25 MAYO.pages
✓ Extracted text from chapter4.pdf
⏳ Transcribing clase1.mp4...
✓ Transcribed clase1.mp4 (4,210 words)
```

After all files processed, commit:
```bash
cd /Users/fabiola/Desktop/agent && git add school/<slug>/ && git commit -m "chore(<slug>): preprocessing complete"
```

Update `progress.md` → `phase: preprocessing complete; next: maximize + plan`.

---

## Step 6 — Maximize + plan (autonomous, single doc)

Read **all** of these:
- `instructions/*.md` (the converted instructions)
- `background/*.md` (converted background docs)
- `transcripts/*.txt` (Whisper transcripts)
- The user's free-text context from Step 2 (saved in `progress.md`)

Build the maximize analysis in **three internal passes** — you do NOT save the intermediate versions, only the final synthesis:

1. **v1 (in your head)** — Draft a maximize analysis: rubric, implicit signals, grader psychology, pedagogical aim, high-leverage moves, traps.
2. **Adversarial (in your head)** — Adopt the persona of a harsh, bored UNIR rubric-bound grader. Critique v1: where is it vague? What would you dock points for in a draft that follows it? What does a 10/10 paper do that v1 doesn't suggest? What are the hidden requirements not stated explicitly?
3. **v2 (write to disk)** — Synthesize v1 + adversarial into the final guidance.

Write `reasoning/plan.md` with this structure (in **Spanish** — output language for school work is Spanish by default; verify by checking what language the instructions are in, and ask only if it's not Spanish):

```markdown
# Plan — <slug>

## Objetivo
<una frase: qué debe lograr este entregable para sacar la mejor nota>

## Requisitos de formato (extraídos de las instrucciones)
- Páginas máx: <N>
- Fuente: <nombre y tamaño>
- Idioma: <es / en>
- Estilo de citas: <si se especifica>
- Secciones requeridas: <lista>
- Trabajo grupal o individual: <…>
- Fecha de entrega: <fecha>

## Análisis de maximización
### Qué pide explícitamente la rúbrica
…
### Señales implícitas
Qué revela el lenguaje de las instrucciones sobre lo que el corrector valora.
### Psicología del corrector + objetivo pedagógico
Quién corrige, qué busca, qué concepto está evaluando realmente.
### Movimientos de alto apalancamiento
Cosas concretas que disparan la nota:
- Citar instrumentos específicos por nombre con justificación
- Estructurar el flujo de trabajo con un diagrama
- Presupuesto desglosado por línea
- …
### Trampas a evitar
Errores comunes que bajan la nota:
- Generalidades sin justificar
- Listar tests sin razonar por qué
- Saltarse secciones requeridas
- …
### Requisitos ocultos (del paso adversarial)
Cosas no dichas explícitamente pero esperadas por el nivel (máster) o por la asignatura.

## Material relevante del background
Para cada transcripción/fuente, qué partes son relevantes para ESTA tarea y por qué.
- `transcripts/clase1.txt` — relevante: minutos 12–25 sobre WAIS-IV. Por qué: la tarea pide protocolos cognitivos.
- `background/slides_unit3.md` — relevante: framework de anamnesis. Por qué: la tarea exige descripción del procedimiento.
- …

## Plan de acción
Pasos numerados, cada uno con:
- **Qué produce**
- **Por qué** (justificación enlazada al análisis de maximización)
- **Depende de**: pasos previos
- **Alternativas consideradas y por qué se rechazaron**
- **Criterio de éxito**: cómo sabremos que este paso quedó bien

Ejemplo:
1. **Esquema** — produce `reasoning/outline_temp.md` (o sección dentro de plan.md).
   - Por qué: el primer riesgo es escribir mucho sin estructura.
   - Depende: nada.
   - Alternativas: empezar por la sección de presupuesto (rechazado: presupuesto necesita protocolos definidos primero).
   - Éxito: cubre todas las secciones de la rúbrica + alinea con los movimientos de alto apalancamiento.
2. …

## Riesgos
- Riesgo: extensión excesiva → mitigación: ceñirse a target de palabras por sección.
- Riesgo: caer en generalidades → mitigación: cada afirmación necesita ejemplo concreto o cita.
- …

## Supuestos
Cosas que estamos asumiendo porque no están explícitas. Se marcan en el doc final para que el usuario pueda corregir.
- Asumimos foco en Daño Cerebral Adquirido (sugerido por las instrucciones).
- Asumimos castellano de España (UNIR) en lugar de español de México.
```

Status updates during this step:
- *"Reading background material…"*
- *"Building plan…"*
- *"Plan ready."*

Commit: `docs(<slug>): plan + maximize complete`.

Update `progress.md` → `phase: plan complete; next: execute plan`.

**Do NOT pause here.** Continue to Step 7.

---

## Step 7 — Execute the plan (autonomous)

Follow the plan from `reasoning/plan.md`. For each plan step:

1. Status update (one line): *"Writing outline..."*, *"Drafting section 2 of 5..."*, etc.
2. Write the artifact:
   - Outline/structure work → can go inline in `output/draft.md` as a top section, or as a separate `reasoning/outline.md` if the plan calls for it
   - Section drafts → `output/draft.md` in markdown
3. After each meaningful step, commit: `feat(<slug>): <one-line description>`

Final draft lives in `output/draft.md`. Write in Spanish (or whatever language was extracted in Step 6). Match the instructor's level of formality. Cite source material where relevant — even informally (*"Como se trató en la clase del…"*).

### Self-review (still autonomous, no pause)

After the draft is complete:
1. Re-read `output/draft.md` against `reasoning/plan.md`'s success criteria.
2. Check: every "high-leverage move" actually present? Every "trap to avoid" actually avoided?
3. Estimate page count: run `python tools/estimate_pages.py output/draft.md --format-from-plan reasoning/plan.md` (or pass font/spacing flags manually).
4. If estimated pages **exceed** the limit → compress in place. Trim each section proportionally, prioritize keeping high-leverage moves intact. Log the compression in `progress.md`.
5. If draft has unresolved assumptions, add a footnote-style note at the end of the draft (the user will see this in Word and can override).

Commit `feat(<slug>): draft v1 complete`.

Update `progress.md` → `phase: draft complete; next: export`.

---

## Step 8 — Export to Word + auto-open

Use the **`docx` skill** (`.claude/skills/docx/`) to render `output/draft.md` → `output/<slug>_v1.docx`.

Pass formatting requirements from `reasoning/plan.md` (font, size, line spacing, page size, margins, language).

Defaults if instructions don't specify (UNIR norms):
- Font: Calibri 11pt
- Line spacing: 1.5
- Page size: A4
- Margins: 2.54 cm
- Page numbers in footer
- Title page or header with subject + student name (if known) + date

After export, **open the file in Microsoft Word**:
```bash
open -a "Microsoft Word" "/Users/fabiola/Desktop/agent/school/<slug>/output/<slug>_v1.docx"
```

If Word isn't installed, fall back to:
```bash
open "/Users/fabiola/Desktop/agent/school/<slug>/output/<slug>_v1.docx"
```

Status update: *"Word doc ready and open. Take a look — I'll wait for your feedback."*

Commit `feat(<slug>): export v1.docx`.

Update `progress.md` → `phase: v1 exported; next: user review`.

---

## Step 9 — Second user touchpoint (review)

Use AskUserQuestion:

> **Looks good, or want changes?**
>
> - ✅ **Looks good — I'm done**
> - 🔄 **Make changes** — tell me what to fix (you can type changes, paste a screenshot of the part that's wrong, or describe the issue)

If `Done` → final commit `feat(<slug>): final` → update `progress.md` → `phase: complete`. Briefly tell the user where the file is (path) and that it's also open in Word, and that the project is saved in git.

If `Make changes` → enter Step 10.

---

## Step 10 — Iterate (loop)

User describes what they want changed. They might:
- Type a change request: *"Make section 3 longer"*, *"Add more citations to neuropsych tests"*, *"Cut to 7 pages"*
- Paste/attach a screenshot of an overflow page or a problematic section

For each iteration:
1. Edit `output/draft.md` (markdown is the source of truth — never edit the `.docx` directly)
2. If screenshot was provided, ask Claude to read it and identify what to change
3. Re-run `tools/estimate_pages.py`
4. Re-export the `.docx` with version bump (`<slug>_v2.docx`, `_v3.docx`, …)
5. Open the new version in Word: `open -a "Microsoft Word" <path>`
6. Update `progress.md` with what changed
7. Commit `refactor(<slug>): <what changed> → v<N>`

Show the user another picker (Done / Make changes).

---

## `progress.md` template

```markdown
# Progress — <slug>

**Phase**: <name of current phase>
**Next step**: <what the next agent session should do>
**Mode**: autonomous | waiting on user

## Metadata (extracted from instructions, not asked)
- Subject: <…>
- Due date: <YYYY-MM-DD>
- Format: <font, size, page limit, language>
- Group/individual: <…>

## Extra context from user (Step 2)
<free text the user provided>

## Files produced
- `reasoning/plan.md` — plan + maximize analysis
- `output/draft.md` — markdown draft
- `output/<slug>_v1.docx` — Word export (open in Word)

## Assumptions made during autonomous run
- <each one, with rationale — surfaced to user in final Word doc>

## Notes for the next agent session
<anything a future Claude needs to know to resume cleanly>
```

---

## Commit policy

After each significant phase, commit from `/Users/fabiola/Desktop/agent/`:

- `feat(school): scaffold <slug>` — Step 2
- `chore(<slug>): preprocessing complete` — Step 5
- `docs(<slug>): plan + maximize complete` — Step 6
- `feat(<slug>): <plan step description>` — each major Step 7 milestone
- `feat(<slug>): draft v1 complete` — end of Step 7
- `feat(<slug>): export v1.docx` — Step 8
- `refactor(<slug>): <what changed> → v<N>` — each iteration in Step 10
- `feat(<slug>): final` — Step 9 "I'm done"

**Never** commit `.env`, `*.mp4`, `*.mp3`, `*.wav`, `unpacked/` — `.gitignore` handles this. Don't push to GitHub automatically; the user pushes when they want.

---

## Auto-open conventions

When pausing to wait on the user (Step 4, Step 9, Step 10) — if there's a markdown file the user might want to review (like the plan in Step 4, though we don't actually pause at plan in this design — kept for future):
```bash
code "<absolute path>"
```

When the final `.docx` is ready:
```bash
open -a "Microsoft Word" "<absolute path>"
```

Always use **absolute paths** for `open` and `code` so they work regardless of CWD.

---

## Behaviors to avoid

- Don't ask "are you sure?" except for destructive ops (delete project folder, force overwrite).
- Don't pause for AskUserQuestion mid-autonomous-run (between Step 4 and Step 9). Status updates only.
- Don't generate intermediate files the user doesn't need (`maximize_v1.md`, `adversarial.md`). One plan.md.
- Don't summarize the assignment back to the user. They wrote it / saw it.
- Don't lecture about API keys, security, or git best practices.
- Don't truncate the maximize analysis to look clean. Depth > brevity.
- Don't push to GitHub unless asked.
- Don't switch to English in Spanish deliverables unless the user explicitly says so.
- Don't make the user navigate Finder. Auto-open everything.
- Don't speak like a developer log (avoid: *"Writing reasoning/plan.md to disk"*). Speak like a teammate (*"Building the plan now"*).

---

## Edge cases

- **`.pages` conversion fails** — tell the user: *"The Pages file gave me trouble. Could you open it in Pages, choose File → Export To → PDF, and drop the PDF into `instructions/`?"* Wait for the user.
- **Video file too large after audio extraction** — `tools/transcribe.py` auto-chunks. If it still fails, tell user and ask for a lower-resolution re-export.
- **Instructions are in English** — read first, then ask the user: *"The instructions are in English. Output in English or Spanish?"*
- **User loses interest mid-autonomous-run** — that's fine. `progress.md` tracks the phase. Future session reads it and resumes.
- **User starts a new project but is mid-flight on an old one** — ask: *"Pause `<old-slug>` and start new, or finish old first?"*
- **Page count estimate is far off when user opens in Word** — that's expected; estimate is a heuristic. User can ask for compression or send a screenshot of the overflow.

---

## Quick reference: tool calls

| Need | Command |
|---|---|
| Convert .pages | `python tools/pages_to_md.py "<path>"` |
| Transcribe video/audio | `python tools/transcribe.py "<path>" --language es` |
| Estimate pages | `python tools/estimate_pages.py "<draft.md>" --font-size 11 --spacing 1.5` |
| Open file in VS Code | `code "<absolute path>"` |
| Open file in Word | `open -a "Microsoft Word" "<absolute path>"` |
| Open file with default app | `open "<absolute path>"` |
