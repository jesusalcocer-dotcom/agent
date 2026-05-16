---
name: school
description: "School assignment concierge. Triggers: '/school', '/homework', 'tengo nueva tarea', 'nueva tarea', 'nueva asignación', 'new homework', 'new assignment', 'school project', 'tarea de la escuela', 'asignación nueva', 'examen', 'actividad evaluable'. Walks the user from intake → autonomous preprocessing + maximize analysis (with blind adversarial sub-agent review) + drafting (with blind draft critic sub-agent) + audit summary → Word export, with exactly TWO user touchpoints: one 'Go' confirmation after files are dropped, and one review after the Word doc is open. Designed for a non-technical user — auto-opens every artifact, speaks plainly, never makes the user navigate Finder. Default output language Spanish. Read SPEC.md at the repo root for the full architecture and FORMATTING.md in this directory for academic formatting rules."
---

# School — autonomous assignment concierge

Before doing anything, **read `/Users/fabiola/Desktop/agent/SPEC.md`** for the system architecture and **`./FORMATTING.md`** (this directory) for academic formatting rules. This skill implements section 4 of SPEC.md.

## Operating philosophy

- **The user is non-technical.** Speak like you'd brief a colleague, not like a developer log. Never make them find a file.
- **Maximize is a lens, not a step.** Every decision asks: *does this help the grade?*
- **One confirm, then run.** After files are dropped and instructions are identified, the user clicks **Go** once. Then Claude runs autonomously to a finished Word doc. No mid-flight checkpoints.
- **Markdown is source of truth.** All drafting happens in `output/draft.md`. The `.docx` is a regenerated export.
- **Document assumptions, don't block.** If you hit ambiguity mid-run, make a documented assumption (in `progress.md` and flagged in the final doc), keep going.
- **EVERYTHING runs on Opus 4.7, max effort, --dangerously-skip-permissions. Non-negotiable.** Main session AND every sub-agent. When calling the Agent tool, ALWAYS set `model: "opus"`. If the current session is not on Opus, max effort, and dangerously-skip mode, **stop immediately** and tell the user to relaunch with: `claude --dangerously-skip-permissions` and `/effort max`. The skill is designed for this configuration; lesser settings produce shallow analyses.
- **Blind reviews to remove same-agent bias.** Sub-agents for adversarial maximize critique and draft critique run in isolation — they do not see the writer's chain of thought, per-source analyses, plan, or outline.

## Two — and only two — user touchpoints

1. **"Go" confirmation** (Step 4) — after instructions are identified, ask: ready to start autonomous run? After this, no input is required.
2. **Word doc review** (Step 9) — Claude opens the .docx in Microsoft Word, asks: looks good or change something?

Between these two: status updates only, plus the **audit summary in Step 8.5** before the Word doc opens.

---

## Step 0 — Pre-flight check (mandatory)

Before anything else, verify the session is correctly configured:

1. **Model = Opus 4.7** (claude-opus-4-7). If you don't know your own model, you may proceed but flag this fact in chat: *"I'm proceeding; if I'm not on Opus, please /switch to it and rerun."*
2. **Effort = max** (`/effort max` was set). If unsure, ask the user once: *"Are you on max effort? If not, run `/effort max`."*
3. **`--dangerously-skip-permissions`** is enabled (the session was launched with this CLI flag). If permission prompts appear during the autonomous run, the launch flag was missing — tell the user to relaunch.

If any of these fail or are uncertain, surface a one-line warning in chat before proceeding but don't block. The user is informed and chose to continue.

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

If `Go` → save `mode: autonomous` to `progress.md`, then enter the autonomous block (Steps 5–9). **From here on, do not call AskUserQuestion until Step 9.** Only print one-line status updates and the Step 8.5 audit summary.

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

## Step 6 — Maximize + per-source analysis + plan (autonomous, blind sub-agent A)

Read **all** of these:
- `instructions/*.md` (the converted instructions)
- `background/*.md` (converted background docs)
- `transcripts/*.txt` (Whisper transcripts)
- The user's free-text context from Step 2 (saved in `progress.md`)

### 6a. Write maximize v1 (in your head, do NOT save)

Draft a maximize-score analysis: rubric requirements, implicit signals from the wording, grader psychology, pedagogical aim, high-leverage moves, common traps, hidden requirements.

### 6b. Per-source analysis — MANDATORY, one file per source ⚠️

**This step is non-negotiable.** Do not skip, do not collapse multiple sources into one file, do not write a superficial paragraph. The goal is to force deep integration of every source through the maximize lens.

Create `reasoning/sources/` if it doesn't exist. For **every** file in `instructions/`, `background/`, and `transcripts/` (one analysis per file), write a separate markdown file at `reasoning/sources/<sluggified-basename>.md` with this exact structure (in **Spanish**):

```markdown
# Análisis de fuente: <nombre del archivo>

## 1. Identificación
- **Tipo**: <transcripción de clase | PDF de instrucciones | DOCX de instrucciones | slides | manual | notas | etc.>
- **Origen**: <ubicación en el árbol del proyecto, p.ej. `background/clase1.mp4` → `transcripts/clase1.txt`>
- **Extensión**: <palabras / páginas / minutos aproximados>
- **Idioma**: <es | en | mixto>
- **Fecha (si aplica)**: <…>

## 2. Resumen sustantivo del contenido (NO superficial)
De 3 a 5 párrafos. Cubre obligatoriamente:
- Tema principal y subtemas, con marcadores (minutos para audio/vídeo, páginas para documentos)
- Marcos conceptuales presentados (escuelas, autores citados, modelos)
- Ejemplos concretos, casos clínicos o datos que aparecen
- Vocabulario técnico y definiciones específicas
- Estructura argumentativa del material (p.ej. "primero define X, luego compara Y vs Z, cierra con caso clínico")

## 3. Análisis de relevancia para esta actividad
Razonamiento explícito y completo sobre cómo se conecta con la tarea. Una sub-sección por cada conexión identificada — no menos de una. Si genuinamente no hay conexión, explica por qué se conserva o se descarta la fuente.

### Conexión <N>: <descripción corta>
- **Qué del contenido se conecta**: <pasaje o cita específica, con marcador>
- **Con qué requisito de la rúbrica o sección del entregable**: <criterio o sección>
- **Por qué es de alto apalancamiento**: <justificación enlazada al análisis de maximización — no un "porque sí">
- **Cómo se usará en el doc final**: <cita textual | paráfrasis | framework adaptado | dato>

(Múltiples conexiones por fuente. Sé exhaustivo.)

## 4. Material citable (lista lista para integrar al borrador)
- Citas directas con marcadores: *"<cita exacta>"* — `<archivo>:<min/pág>`
- Datos / estadísticas: <valor> — `<archivo>:<min/pág>`
- Frameworks / esquemas a adaptar: <nombre> — `<archivo>:<min/pág>`

## 5. Lo que NO se usará (y por qué)
Justificación de descartes — uno por uno, no genérico:
- **Pasaje**: <descripción>
- **Por qué se descarta**: <fuera de scope | redundante con otra fuente | baja calidad | etc.>

## 6. Integración con otras fuentes
Cómo este material se conecta con otras fuentes ya analizadas (rellenar al analizar la última fuente, o ir actualizando):
- **Refuerza**: <fuente X> en <punto> — porque <razón>
- **Complementa**: <fuente Y> en <punto> — porque <razón>
- **Contradice / matiza**: <fuente Z> en <punto> — se resolverá así: <decisión>

## 7. Mapeo al doc final
Dónde, concretamente, entrará este material en el outline (Step 7a):
- **Sección del entregable**: <…>
- **Subsección / párrafo**: <…>
- **Forma de uso**: <cita | paráfrasis | framework integrado | dato>
```

Status updates during this step (one per source):
- *"Analyzing clase1.txt (12,400 words)…"*
- *"Source analysis saved: reasoning/sources/clase1.md"*

If a source is large (>10k words or >30 min audio): take longer, write more — depth scales with content. **A 200-word analysis of a 1-hour transcript is unacceptable. Push yourself.**

### 6c. Spawn blind sub-agent A — adversarial critique

Use the **Agent** tool. Settings:
- `subagent_type`: `"general-purpose"`
- `model`: `"opus"`
- `description`: `"Blind maximize-score critique"`
- `prompt`: Use exactly the template below, with `{ASIGNATURA}`, `{INSTRUCTIONS_TEXT}`, and `{ANALYSIS_V1_TEXT}` substituted with the actual content.

**Template:**
```
Eres un corrector experimentado de la UNIR, máster en {ASIGNATURA}, con la rúbrica oficial en mano y poco tiempo para corregir. Has visto cientos de trabajos similares y eres exigente.

Aquí están las instrucciones COMPLETAS de la actividad:
---
{INSTRUCTIONS_TEXT}
---

Aquí está un "análisis de maximización" escrito por la asistente del estudiante. Tú NO has visto su razonamiento — solo el resultado:
---
{ANALYSIS_V1_TEXT}
---

Tu tarea: critica el análisis DURO. Específicamente:
1. ¿Dónde es vago o generalista?
2. ¿Qué requisitos explícitos de la rúbrica está minimizando o ignorando?
3. ¿Qué requisitos OCULTOS o implícitos (nivel máster, convenciones UNIR, expectativas del corrector experto) no menciona?
4. Si un borrador siguiera este análisis al pie de la letra, ¿qué puntos concretos perdería al ser corregido?
5. ¿Qué movimientos haría un trabajo de matrícula (9-10/10) que este análisis no sugiere?

Responde en español, <500 palabras, en formato de lista numerada. Sé honesto y duro — el objetivo es mejorar el análisis, no ser amable. Devuelve solo la crítica, sin saludos ni cierre.
```

**Important**:
- Do NOT include your (writer's) reasoning, your "in your head" passes, the per-source analyses, or any meta-commentary in the prompt.
- ONLY include the assignment instructions and your written v1.
- The sub-agent must be blind to your process.
- Save the returned critique to a variable in your context — do NOT write it to disk as a separate file (it'll be embedded in plan.md and the audit summary).

### 6d. Synthesize v2 → write `reasoning/plan.md`

Combine your v1 thinking + sub-agent A's critique into the final guidance. Write `reasoning/plan.md` in **Spanish**:

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

## Análisis de maximización (post-revisión adversarial)
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
### Requisitos ocultos (de la revisión adversarial del sub-agente)
Cosas no dichas explícitamente pero esperadas. Cita lo que añadió/corrigió el sub-agente.

## Crítica del sub-agente A (revisión adversarial blind)
Copia textual de la crítica devuelta por el sub-agente, para auditoría.

## Cómo se abordó la crítica
Para cada punto del sub-agente: qué se cambió en el análisis, o por qué no aplica.

## Material relevante del background — ÍNDICE
Resumen de una línea por cada análisis detallado en `reasoning/sources/*.md`. NO duplicar el contenido completo — solo apuntar al archivo. Ejemplo:
- `reasoning/sources/clase1.md` — Transcripción clase 1 (4,210 palabras). Aporta: protocolos cognitivos (WAIS-IV minutos 12–25). 4 conexiones identificadas.
- `reasoning/sources/INST_EVALAUCION.md` — Brief de la actividad. Aporta: rúbrica explícita + formato + secciones requeridas.
- …

## Plan de acción
Pasos numerados, cada uno con:
- **Qué produce**
- **Por qué** (justificación enlazada al análisis de maximización)
- **Depende de**: pasos previos
- **Alternativas consideradas y por qué se rechazaron**
- **Criterio de éxito**: cómo sabremos que este paso quedó bien

## Riesgos
- Riesgo: extensión excesiva → mitigación: ceñirse a target de palabras por sección.
- Riesgo: caer en generalidades → mitigación: cada afirmación necesita ejemplo concreto o cita.
- …

## Supuestos
Cosas que estamos asumiendo porque no están explícitas. Se marcan en el doc final para que el usuario pueda corregir.
- Asumimos foco en Daño Cerebral Adquirido (sugerido por las instrucciones).
- …
```

Status updates during this step:
- *"Reading background material…"*
- *"Building first-pass analysis…"*
- *"Spawning blind reviewer for adversarial critique…"*
- *"Synthesizing final plan…"*
- *"Plan ready."*

Commit: `docs(<slug>): plan + maximize complete`.

Update `progress.md` → `phase: plan complete; next: execute plan`.

**Do NOT pause here.** Continue to Step 7.

---

## Step 7 — Outline → outline self-critique → draft → blind sub-agent B → revise

This step is mandatory in this order: **outline first, self-critique, then draft, then sub-agent B**. Do NOT skip the outline or jump straight to draft. The outline + self-critique force the agent to integrate every per-source analysis from Step 6b before committing to prose.

### 7a. Write outline (MANDATORY) → `reasoning/outline.md`

Build the outline from:
- `reasoning/plan.md` (maximize analysis + plan + sub-agent A critique addressed)
- Every file in `reasoning/sources/` (the per-source analyses)

Structure required (in Spanish):

```markdown
# Outline — <slug>

(Auto-crítica del outline arriba; ver Step 7b)

## Sección 1: <título>
- **Target**: <N palabras> / <M páginas estimadas>
- **Puntos clave** (3–5):
  1. <punto 1>
  2. <punto 2>
  3. <punto 3>
- **Fuentes que la sustentan**:
  - `reasoning/sources/<file>.md` → <qué se toma, sección 3 conexión N de ese análisis>
  - `reasoning/sources/<file>.md` → <…>
- **Movimiento de alto apalancamiento (plan.md) que encarna**: <…>
- **Trampa que evita estructuralmente**: <…>

## Sección 2: <título>
...
```

**Do NOT write prose yet — only structure.** Status update: *"Outline ready."*

### 7b. Outline self-critique (MANDATORY, internal) — revise outline.md

At the **top** of `reasoning/outline.md`, before publishing, write an "Auto-crítica del outline" section that reasons through:

1. **Cobertura de rúbrica**: ¿Aparece cada requisito explícito de la rúbrica en alguna sección? Enuméralos y confirma uno por uno.
2. **Integración de fuentes**: ¿Aparece cada archivo de `reasoning/sources/*.md` en el outline? Si una fuente NO se usa, justifica explícitamente por qué (o revisa el outline para incluirla).
3. **Movimientos de alto apalancamiento**: ¿Aparece cada "movimiento de alto apalancamiento" de plan.md en alguna sección?
4. **Trampas evitadas**: ¿El outline evita estructuralmente cada "trampa a evitar"?
5. **Balance de extensión**: ¿La suma de targets de palabras coincide con el límite de páginas? Si excede, ¿qué se recorta?
6. **Coherencia narrativa**: ¿Las secciones cuentan una historia coherente o es una lista desconectada?

For each weakness found, **revise the outline below in the same file**. Iterate until the self-critique returns "limpio" — every rubric point covered, every source used (or justifiably excluded), every high-leverage move present.

Status updates:
- *"Self-critiquing outline…"*
- *"Outline revised — N issues addressed."* / *"Outline clean."*

Commit: `docs(<slug>): outline + self-critique complete`.

### 7c. Draft from outline → `output/draft.md`

Now write `output/draft.md` section by section, **following the outline**. Don't deviate from outline structure unless something new emerges that improves the maximize score — and if so, log the deviation in `progress.md` with rationale.

For each section:
- Status update: *"Drafting section <N>/<total>: <título>"*
- Open the relevant source analyses (`reasoning/sources/<file>.md`) and pull the citations / data / frameworks that the outline mapped to this section
- Write the section in Spanish (or the language from instructions), justified prose, citation style per the format requirements
- Each section's word count should be close to the outline target

After the draft is fully written, commit `feat(<slug>): draft v1 complete`.

### 7d. Spawn blind sub-agent B — draft critique

Once the draft is complete, use the **Agent** tool again:
- `subagent_type`: `"general-purpose"`
- `model`: `"opus"`
- `description`: `"Blind draft critique"`
- `prompt`: Template below, with `{ASIGNATURA}`, `{INSTRUCTIONS_TEXT}`, and `{DRAFT_TEXT}` substituted.

**Template:**
```
Eres un corrector experimentado de la UNIR, máster en {ASIGNATURA}, con la rúbrica oficial en mano. Vas a corregir un borrador de la actividad. No has visto el proceso de elaboración — solo el resultado final.

Aquí están las instrucciones COMPLETAS de la actividad:
---
{INSTRUCTIONS_TEXT}
---

Aquí está el borrador del estudiante (en markdown — evalúa el CONTENIDO, no el formato):
---
{DRAFT_TEXT}
---

Tu tarea: critica el borrador con criterios de rúbrica. Específicamente:
1. ¿Cumple TODAS las secciones explícitamente pedidas en las instrucciones?
2. ¿Dónde es generalista, vago, usa frases comodín sin sustancia?
3. ¿Dónde faltan citas, justificaciones técnicas, o referencias específicas?
4. ¿Hay requisitos ocultos del nivel máster (UNIR) que no cumple?
5. ¿Qué puntos concretos perderá al corregirlo un experto duro?
6. ¿Qué le falta para ser un trabajo de matrícula (9-10/10)?

Responde en español, <700 palabras, en formato de lista numerada. Sé brutal — el objetivo es mejorar el trabajo, no animarlo. Devuelve solo la crítica, sin saludos ni cierre.
```

### 7e. Address the critique → revise draft

For each point sub-agent B raised:
- Decide: legitimate concern, partial concern (worth tweaking), or invalid (not actually a rubric issue)
- Apply the revision directly to `output/draft.md`
- Document the decision: which points addressed, which dismissed, why

Save sub-agent B's critique verbatim and your responses to memory (will go into Step 8.5 audit summary).

### 7f. Self-review + page check

After revisions:
1. Re-read `output/draft.md` against `reasoning/plan.md`'s success criteria.
2. Run `python tools/estimate_pages.py output/draft.md --font-size <X> --spacing <Y> --limit <N>` (use values from plan.md format requirements).
3. If estimated pages **exceed** the limit → compress in place. Trim each section proportionally, prioritize keeping high-leverage moves intact. Log compression in `progress.md`.
4. If draft has unresolved assumptions, add them as a "Supuestos" section at the end of the draft.

Commit `feat(<slug>): draft v1 complete (post blind critique)`.

Update `progress.md` → `phase: draft complete; next: format + export`.

---

## Step 8 — Format + export to Word

### 8a. Parse format requirements from instructions

Re-read `instructions/*.md`. Specifically look for sections like "Extensión y formato", "Formato", "Presentación", "Normativa". Extract:
- Page limit
- Font name + size (body)
- Line spacing
- Margins
- Citation style
- Required sections / structure
- Cover page / header requirements
- Language

### 8b. Fill gaps from FORMATTING.md

Read `./FORMATTING.md` (this skill directory). For each format item NOT specified by the instructions, apply the default from FORMATTING.md.

**Build a Format Decisions table** in `progress.md`:

```markdown
## Format decisions

| Item              | Instructions say  | Default applied (FORMATTING.md) | Reason                |
|-------------------|-------------------|----------------------------------|-----------------------|
| Font              | (silent)          | Calibri                          | UNIR default          |
| Body size         | "tamaño 12"       | 12 pt                            | explicit              |
| Heading size      | (silent)          | 12 pt (same as body, bold)        | conservative default  |
| Line spacing      | "1,5"             | 1.5                              | explicit              |
| Page count        | "máx 7"           | 7                                | explicit              |
| Citation style    | (silent)          | APA 7                            | psychology default    |
| Page numbers      | (silent)          | footer centered                   | safe default          |
```

### 8c. Generate the .docx via the docx skill

Invoke the `docx` skill (`.claude/skills/docx/`). Use **docx-js directly** to build the .docx with formatting applied **in-line** — do NOT generate raw markdown→docx via pandoc and post-process. Instead:

1. Read `output/draft.md`
2. Write a JS file (e.g. `output/build_docx.js`) that uses docx-js Document/Paragraph/TextRun components, applying:
   - Body font + size from Format Decisions table
   - Heading styles (bold, italic, sizes per FORMATTING.md rules)
   - Body alignment: justify (`AlignmentType.JUSTIFIED`) — Spanish academic convention
   - Headings: left-aligned, numbered (`1. Sección`, `1.1 Subsección`)
   - Line spacing from Format Decisions
   - Page size A4 with 2.54 cm margins (or whatever instructions say)
   - Page numbers in footer, centered, plain Arabic numerals
   - Tables: simple black borders, no colored shading
   - No first-line indent (using paragraph spacing instead)
   - Color: black throughout, no theme colors
3. Execute: `node output/build_docx.js` → produces `output/<slug>_v1.docx`
4. Delete `output/build_docx.js` after success (transient build artifact)

**Reference the FORMATTING.md "Never do" list** while building the JS — no colored text, no emoji bullets, no Comic Sans, no mixing fonts.

For each "Format decisions" defaulted item, mention it in the audit summary (Step 8.5) so the user can override if needed.

### 8d. Hold off on opening Word

Do NOT open the .docx yet. Step 8.5 comes first.

Commit `feat(<slug>): export v1.docx with formatting applied`.

Update `progress.md` → `phase: docx ready; next: audit + user review`.

---

## Step 8.5 — Audit summary (NEW)

Write the audit summary as a chat message AND save the identical content to `reasoning/audit.md`. This is the **last thing the user sees before the Word doc opens**.

Format (in Spanish, ~400-600 words):

```markdown
## 📋 Cómo construí este documento

### 1. Análisis de maximización (qué busca el corrector)
[2-3 párrafos: rúbrica explícita, señales implícitas, movimientos de alto apalancamiento, trampas a evitar — síntesis breve del análisis de plan.md]

### 2. Revisión adversarial (sub-agente independiente, blind)
**Lo que señaló:**
- [punto 1 de la crítica del sub-agente A]
- [punto 2]
- [...]

**Cómo lo abordé:**
- [revisión 1 que hiciste]
- [revisión 2]
- [...]

### 3. Material relevante por fuente
Para cada fuente del `background/` y `transcripts/`, qué contribuyó al doc final:
- `<archivo>` → contribuyó: <qué partes y dónde aparecen en el doc>
- ...

### 4. Crítica del borrador (segundo sub-agente independiente, blind)
**Lo que señaló:**
- [punto 1 de la crítica del sub-agente B]
- [punto 2]
- [...]

**Cómo lo abordé:**
- [revisión 1]
- [revisión 2]
- [...]

### 5. Decisiones de formato
| Ítem | Instrucciones | Aplicado | Razón |
|------|---------------|----------|-------|
| Fuente | <…> | <…> | <…> |
| Tamaño | <…> | <…> | <…> |
| <…> | <…> | <…> | <…> |

Si algún default te parece mal, dímelo al revisar el doc.

### 6. Supuestos no resueltos
Cosas que asumí porque no están explícitas en las instrucciones. Están marcadas también al final del doc para que las puedas corregir:
- <supuesto 1>
- <supuesto 2>

---
✅ Abriendo el documento en Word ahora. Revísalo y dime si te parece bien o qué cambiar.
```

After writing both the chat output AND `reasoning/audit.md`, commit: `docs(<slug>): audit summary written`.

Update `progress.md` → `phase: audit written; next: open Word for user`.

**Then proceed immediately to Step 9.**

---

## Step 9 — Open Word + second user touchpoint

Open the file in Microsoft Word:
```bash
open -a "Microsoft Word" "/Users/fabiola/Desktop/agent/school/<slug>/output/<slug>_v1.docx"
```

If Word isn't installed, fall back to:
```bash
open "/Users/fabiola/Desktop/agent/school/<slug>/output/<slug>_v1.docx"
```

Then immediately call AskUserQuestion:

> **Looks good, or want changes?**
>
> - ✅ **Looks good — I'm done**
> - 🔄 **Make changes** — tell me what to fix (you can type, paste a screenshot, or describe the issue)

If `Done` → final commit `feat(<slug>): final` → update `progress.md` → `phase: complete`. Briefly tell the user where the file is and that it's open in Word.

If `Make changes` → Step 10.

---

## Step 10 — Iterate (loop)

User describes what they want changed. They might:
- Type a change request: *"Make section 3 longer"*, *"Add more citations"*, *"Cut to 7 pages"*
- Paste/attach a screenshot of an overflow page or a problematic section

For each iteration:
1. Edit `output/draft.md` (markdown is source of truth — never edit `.docx` directly)
2. If a screenshot was provided, read it to identify what to change
3. Re-run `tools/estimate_pages.py`
4. Re-run the docx-js build step (8c) with version bump → `output/<slug>_v2.docx`
5. Open the new version in Word
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
- `reasoning/sources/*.md` — comprehensive per-source analyses (one per file in instructions/background/transcripts)
- `reasoning/plan.md` — plan + maximize analysis (with sub-agent A critique embedded) + index of source analyses
- `reasoning/outline.md` — outline with auto-crítica at top
- `reasoning/audit.md` — chat-friendly audit summary
- `output/draft.md` — markdown draft (post sub-agent B critique)
- `output/<slug>_v1.docx` — Word export (open in Word)

## Format decisions
| Item | Instructions say | Default applied | Reason |
|------|------------------|-----------------|--------|
| ... | ... | ... | ... |

## Assumptions made during autonomous run
- <each one, with rationale — surfaced to user in audit summary AND in final Word doc>

## Notes for the next agent session
<anything a future Claude needs to know to resume cleanly>
```

---

## Commit policy

After each significant phase, commit from `/Users/fabiola/Desktop/agent/`:

- `feat(school): scaffold <slug>` — Step 2
- `chore(<slug>): preprocessing complete` — Step 5
- `docs(<slug>): per-source analyses complete` — Step 6b
- `docs(<slug>): plan + maximize complete` — Step 6d (after sub-agent A)
- `docs(<slug>): outline + self-critique complete` — Step 7b
- `feat(<slug>): draft v1 complete` — Step 7c
- `feat(<slug>): draft v1 complete (post blind critique)` — Step 7f (after sub-agent B)
- `feat(<slug>): export v1.docx with formatting applied` — Step 8
- `docs(<slug>): audit summary written` — Step 8.5
- `refactor(<slug>): <what changed> → v<N>` — each iteration in Step 10
- `feat(<slug>): final` — Step 9 "I'm done"

**Never** commit `.env`, `*.mp4`, `*.mp3`, `*.wav`, `unpacked/` — `.gitignore` handles this. Don't push to GitHub automatically; the user pushes when they want.

---

## Auto-open conventions

The audit summary is shown in chat (Step 8.5) before the Word doc opens. The `reasoning/audit.md` copy is for later reference.

When the final `.docx` is ready (Step 9):
```bash
open -a "Microsoft Word" "<absolute path>"
```

Always use **absolute paths** for `open` and `code`.

---

## Sub-agent invocation — full template

When calling the Agent tool for blind sub-agent reviews:

```
Agent(
    subagent_type: "general-purpose",
    model: "opus",
    description: "<short description>",
    prompt: <the template from Step 6b or 7b with substitutions>
)
```

**Critical isolation rules:**
- The sub-agent prompt must include ONLY: assignment instructions + the artifact to critique (v1 analysis or draft).
- Do NOT include your chain-of-thought, your "v1 (in your head)" reasoning, or any meta-commentary.
- Do NOT include the maximize plan when invoking sub-agent B (draft critic) — they should evaluate the draft against the rubric, not against your own plan.
- Sub-agents return their critique as a text response. Save it to a local variable in the context; embed verbatim in `plan.md` (sub-agent A) and `audit.md` (both A and B).

---

## Behaviors to avoid

- Don't ask "are you sure?" except for destructive ops (delete project folder, force overwrite).
- Don't pause for AskUserQuestion mid-autonomous-run (between Step 4 and Step 9). Status updates + the Step 8.5 audit summary only.
- Don't generate intermediate files the user doesn't need (`maximize_v1.md`, `adversarial.md`). One `plan.md`, one `audit.md`, one `draft.md`, one `.docx`.
- Don't summarize the assignment back to the user. They wrote it / saw it.
- Don't lecture about API keys, security, or git best practices.
- Don't truncate the maximize analysis to look clean. Depth > brevity.
- Don't push to GitHub unless asked.
- Don't switch to English in Spanish deliverables unless the user explicitly says so.
- Don't make the user navigate Finder. Auto-open everything.
- Don't speak like a developer log (avoid: *"Writing reasoning/plan.md to disk"*). Speak like a teammate (*"Building the plan now"*).
- Don't use any model other than Opus 4.7 — anywhere, ever. Always `model: "opus"` for sub-agents. If the main session detects it's running on Sonnet/Haiku, stop and tell the user.
- Don't share your chain-of-thought with sub-agents — that defeats the purpose of blind review.
- Don't post-process the .docx after pandoc with XML edits. Build it correctly the first time with docx-js parameters.

---

## Edge cases

- **`.pages` conversion fails** — tell the user: *"The Pages file gave me trouble. Could you open it in Pages, choose File → Export To → PDF, and drop the PDF into `instructions/`?"* Wait for the user.
- **Video file too large after audio extraction** — `tools/transcribe.py` auto-chunks. If it still fails, tell user and ask for a lower-resolution re-export.
- **Instructions are in English** — read first, then ask the user: *"The instructions are in English. Output in English or Spanish?"*
- **User loses interest mid-autonomous-run** — that's fine. `progress.md` tracks the phase. Future session reads it and resumes.
- **User starts a new project but is mid-flight on an old one** — ask: *"Pause `<old-slug>` and start new, or finish old first?"*
- **Page count estimate is far off when user opens in Word** — that's expected; estimate is a heuristic. User can ask for compression or send a screenshot of the overflow.
- **Sub-agent A or B times out or fails** — log it in `progress.md`, fall back to self-critique with explicit note in `audit.md` that the blind review didn't run. Don't block the autonomous flow.

---

## Quick reference: tool calls

| Need | Command |
|---|---|
| Convert .pages | `python tools/pages_to_md.py "<path>"` |
| Transcribe video/audio | `python tools/transcribe.py "<path>" --language es` |
| Estimate pages | `python tools/estimate_pages.py "<draft.md>" --font-size 11 --spacing 1.5 --limit <N>` |
| Open file in Word | `open -a "Microsoft Word" "<absolute path>"` |
| Open file with default app | `open "<absolute path>"` |
| Spawn blind sub-agent | `Agent(subagent_type="general-purpose", model="opus", prompt=<template>)` |
