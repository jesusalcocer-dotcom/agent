---
name: school
description: "School assignment concierge for UNIR master's coursework. Triggers: '/school', '/homework', 'tengo nueva tarea', 'nueva tarea', 'new homework', 'new assignment', 'school project', 'tarea de la escuela', 'asignación nueva'. Walks the user end-to-end through: project selection (new or resume) → file intake → media preprocessing (video→text via Whisper, .pages→.md via LibreOffice) → deep maximize-score analysis with adversarial review pass → outline → drafting → Word document export. Maintains progress.md so any future session can resume. Auto-commits to git at checkpoints. Default output language is Spanish."
---

# School — assignment concierge

End-to-end workflow for school assignments. When invoked, walk the user through every phase below. **Do not skip phases.** Always update `reasoning/progress.md` after each phase and commit at the major checkpoints.

## Operating principles

- **Spanish is the default output language.** All deliverables and reasoning files go in Spanish. Conversation with the user can stay in their language of choice.
- **Always confirm before risky moves.** Big file ops, git pushes, destructive deletes — always ask.
- **Show file paths.** When you write a markdown file, tell the user the path so they can open it in VS Code / Cursor.
- **Use AskUserQuestion at decision points.** Don't ask in free text; give them clickable options.
- **Write everything down.** Every phase produces a markdown artifact in `reasoning/` or `output/`. Future agent sessions read these to resume.
- **One assignment at a time.** Don't context-switch between projects unless the user explicitly asks.

---

## Phase 0 — Detect entry point

When invoked, immediately:

1. List `agent/school/` to see existing projects.
2. **If user says "new" or "nueva" anywhere in their first message** → jump to Phase 2.
3. **If user names a specific project** → load that project (read `school/<name>/reasoning/progress.md`) and jump to whatever phase progress.md says is next.
4. **Otherwise** → Phase 1 (project picker).

---

## Phase 1 — Project picker

Use AskUserQuestion. Build the option list dynamically:

- First option: **"➕ New project"** (label: "New project", description: "Start a fresh assignment")
- Then one option per existing folder in `school/`, sorted by most-recently-modified.
  - Label: project folder name
  - Description: pull from the project's `reasoning/progress.md` first line — typically `"Phase X — <step name>"` plus due date if known.

Question: *"Which project?"*

Route based on selection:
- **New project** → Phase 2
- **Existing project** → load `school/<name>/reasoning/progress.md` and jump to the phase it says is next.

---

## Phase 2 — New project intake

Ask via AskUserQuestion or sequential simple prompts:

1. **Folder name** — short slug, e.g. `eval-neuro-act3`. (validate: lowercase, hyphens, no spaces)
2. **Subject / course** — e.g. *"Evaluación Neuropsicológica"*
3. **Due date** — ISO format (YYYY-MM-DD), or "unknown"
4. **Format requirements** — page limit, font, citation style, language (default Spanish)
5. **Group or individual** — note if group, will affect drafting tone
6. **Any extra context** — anything the user wants the agent to know

Then:

1. Create folder structure:
   ```
   school/<slug>/
   ├── instructions/
   ├── background/
   ├── transcripts/
   ├── reasoning/
   └── output/
   ```
2. Write initial `reasoning/progress.md` (template below).
3. Tell the user (verbatim or close):

   > ✅ Created `school/<slug>/` with subfolders.
   >
   > Now drop your files in the right folders:
   > - `instructions/` — assignment brief (PDF, DOCX, .pages — any format works)
   > - `background/` — class videos, slides, notes, reference material
   >
   > When done, tell me **"ready"** (or close Claude and come back later — I'll resume).

4. `git add` and commit: `"feat(school): scaffold <slug>"`.
5. **Stop and wait** for the user. Do not proceed to Phase 3 until they say "ready" or equivalent.

---

## Phase 3 — Preprocessing

When the user signals ready:

### 3a. Scan folders
- `instructions/` — list all files
- `background/` — list all files
- Identify file types: PDF, DOCX, PAGES, MP4/MOV/MKV (video), MP3/WAV/M4A (audio), markdown, plaintext, images.

### 3b. Convert non-portable formats

For each `.pages` file:
- Run `tools/pages_to_md.py <path>` — this converts to `.docx` (via LibreOffice headless) and then `.md` (via pandoc). Both versions land next to the original.
- If conversion fails (rare with newer Pages versions), tell the user and ask them to manually export to PDF from Pages.app.

For each `.doc` file:
- Run `python .claude/skills/docx/scripts/office/soffice.py --headless --convert-to docx <path>` to upgrade to `.docx`.

For each `.docx` file in `instructions/` or `background/`:
- Run `pandoc <file>.docx -o <file>.md` to create a markdown sidecar.

For each `.pdf` file:
- Use the `pdf` skill (already installed in `.claude/skills/pdf/`) to extract text. Save as `<filename>.md` next to the PDF.

### 3c. Transcribe media

For each video or audio file in `background/` (or anywhere in the project):
- Run `python tools/transcribe.py <media-file>` — this:
  - Extracts audio with ffmpeg if it's video
  - Chunks if larger than 25 MB
  - Calls OpenAI Whisper API
  - Writes the transcript to `transcripts/<original-basename>.txt`
- Show progress for each file.

### 3d. Summarize

After preprocessing, show the user:
```
✓ instructions: <N files> processed
✓ background: <N files>, <N converted to .md>
✓ transcripts: <N media files>, total ~<X> words

Next: I'll read everything and start the maximize analysis.
Anything you want to add before I start? [add more / continue]
```

### 3e. Update progress + commit
- Update `reasoning/progress.md` → next step: maximize
- `git add` and commit: `"chore(<slug>): preprocessing complete"`

---

## Phase 4 — Read everything

Now actually read:
- All files in `instructions/` (especially the `.md` versions if available)
- All `.md` files in `background/`
- All `.txt` files in `transcripts/`

Build an internal mental model of:
- What the assignment asks
- What the source material (class transcripts, slides, etc.) covers
- Where the source material is strong vs thin
- What language and tone the instructor uses (clues to grader expectations)

Do **not** show this mental model yet. Use it as fuel for Phase 5.

---

## Phase 5 — Maximize analysis v1 (deep, multi-angle)

Write `reasoning/maximize_v1.md`. **Reasoning quality matters far more than formatting.** Use the structure below but go deep on substance.

```markdown
# Maximize-score analysis — <project slug> — v1

## 1. Explicit requirements (from the rubric / instructions)
- List every concrete deliverable the instructions name
- List every formal constraint (page limit, font, sections, etc.)

## 2. Implicit signals
- What does the **wording** of the instructions tell us about what the
  grader values?
- Where does the instructor use words like "justify", "explain",
  "describe in depth" — these mark the high-weight zones.
- Are there hints in the phrasing of any "ejemplo" or aside?

## 3. Grader psychology
- Who is grading this? (Usually the course instructor or TA, sometimes a
  rubric-bound external grader.)
- At UNIR (Spanish-language master's): graders typically reward
  **specificity over generality**, **citations to course materials**,
  and **justified choices** over listed ones.
- What does the grader probably see a lot of from other students?
  What makes a paper stand out?

## 4. Pedagogical aim
- What concepts / skills is this assignment actually testing?
- Why did the instructor design it this way? What real-world clinical
  / professional skill does it map to?

## 5. High-leverage moves
- Specific things that disproportionately boost the grade.
- Be concrete: name actual tests / frameworks / authors to cite, name
  specific section structures, name diagrams or tables that would help.

## 6. Common traps to avoid
- Things students typically do that hurt the grade.
- Generic language, listing without justifying, missing required
  sections, ignoring budget when asked, etc.

## 7. Open questions before drafting
- Things we still need to decide or research.
```

After writing the file, **stop and present it to the user**. Use AskUserQuestion:

- **Looks good — continue to adversarial review** (Phase 6)
- **Open in VS Code first** — pause; the user will tell you when ready
- **Iterate this version** — ask the user what's missing, then rewrite

Update `reasoning/progress.md` → next step: adversarial review.

---

## Phase 6 — Adversarial review

Write `reasoning/adversarial.md`. Adopt the persona of a **harsh, experienced grader at UNIR** who has read hundreds of these papers and is bored. Critique `maximize_v1.md` itself, and forecast what a draft following it would miss.

```markdown
# Adversarial review of maximize_v1 — <project slug>

## Role
Acting as: harsh UNIR rubric-bound grader, expert in <subject>,
suspicious of generic answers.

## 1. Weaknesses in the v1 analysis
- Where is v1 vague?
- Where does v1 confuse "what the instructions say" with "what the
  grader actually wants"?
- What angles did v1 miss?

## 2. What would I dock points for in a draft following v1?
- Specific deductions a tough grader would make.

## 3. What a 10/10 paper does that this analysis doesn't suggest
- Concrete examples of what excellence looks like in this domain.

## 4. Steelman the grader's counterargument
- If the writer thinks "this section is enough", what would the
  grader respond with?

## 5. Hidden requirements
- Things not stated in the rubric but expected because of the subject
  area, the academic level (master's), or UNIR norms.
```

Update `reasoning/progress.md` → next step: maximize v2.

---

## Phase 7 — Maximize v2 (revised, final guidance)

Write `reasoning/maximize_v2.md`. Synthesize v1 + adversarial critique into the **final guidance the drafting phase will follow**. Keep what worked, fix what the adversarial pass exposed, add what was missing.

Same structure as v1, but tighter and more committed — this is the rubric we draft against.

After writing, present to the user. Use AskUserQuestion:
- **Approved — continue to outline** (Phase 8)
- **Open in VS Code**
- **One more adversarial pass** (loop back to Phase 6)

Commit at this checkpoint: `"docs(<slug>): maximize analysis complete"`.

Update `reasoning/progress.md` → next step: outline.

---

## Phase 8 — Outline

Write `reasoning/outline.md`. Section-by-section structure of the final document, with:
- Section heading
- Word/page target for that section
- Bullet of the 3–5 key points that section will make
- Which background material / transcript will support each point
- Which "high-leverage move" from maximize_v2 the section embodies

Show the user. AskUserQuestion:
- **Approved — continue to gap analysis** (Phase 9)
- **Open in VS Code**
- **Iterate the outline** — ask user what to change

Update progress.md → next step: gap analysis.

---

## Phase 9 — Gap analysis + research

Write `reasoning/gaps.md`. For each section in the outline, ask:
- Do we have enough source material (instructions + background + transcripts) to write this section well?
- If not, what's the gap?

For each gap, decide:
- **Research it** — use WebSearch / WebFetch for current academic / clinical info. Save findings to `reasoning/research_<topic>.md`. Cite sources clearly.
- **Ask the user** — if the gap is something only they know (e.g. group member's section).
- **Accept the gap** — if minor, note it and move on.

Show gaps + plan to the user. Approve → Phase 10.

Update progress.md → next step: draft.

---

## Phase 10 — Drafting

Write `output/draft.md` (markdown, not Word yet — easier to iterate).

Default mode: **section-by-section with checkpoints.** After every 1–2 sections, pause and ask the user:
- **Continue to next section**
- **Edit this section first**
- **Skip ahead — draft the rest in one go**

Alternative: if the user says "draft it all" upfront, do all sections in one pass and pause only at the end.

Write in **Spanish** (default). Match the formality of the instructor's wording in the instructions. Cite source material (transcripts, course slides) where relevant — even informally, e.g. *"Como se discutió en la clase del 12 de mayo…"*.

After the full draft is done:
1. Read it back. Check against `maximize_v2.md` priorities. Self-critique.
2. Write a short `reasoning/self_review.md` noting any weaknesses you see in the draft.
3. Offer the user a revised v2 of the draft, or proceed to export as-is.

Update progress.md → next step: export.

Commit: `"feat(<slug>): draft v1 complete"`.

---

## Phase 11 — Word export

Invoke the **`docx` skill** (already installed at `.claude/skills/docx/`) to convert `output/draft.md` to `.docx`.

Pass these formatting requirements (or whatever the assignment specifies):
- Font: Calibri 11pt (or whatever the instructions require)
- Line spacing: 1.5
- Margins: 1 inch / 2.54 cm
- Page size: A4 (UNIR is in Spain; A4 is the European default)
- Page numbers in footer
- Title page or header with: subject, student name (ask user), date
- Page limit: enforce the assignment's limit; if draft is over, **flag to user, don't silently truncate**

Save as `output/<slug>_v1.docx`.

If the user has used this skill before and approved formatting, repeat it; otherwise show them the result and ask for adjustments.

Commit: `"feat(<slug>): export v1.docx"`.

Update progress.md → next step: iteration.

---

## Phase 12 — Iteration

Loop. After delivering v1, the user typically asks for changes:
- *"Make section 3 longer"* → edit `output/draft.md`, re-export as `v2.docx`
- *"Add more citations"* → research + edit + re-export
- *"Cut to 7 pages"* → edit for compression, re-export

Each iteration:
1. Edit the markdown draft (not the .docx directly — markdown is the source of truth)
2. Re-run the docx export
3. Bump version: `output/<slug>_v2.docx`, `_v3.docx`, etc.
4. Update progress.md with what changed
5. Commit: `"refactor(<slug>): <what changed> → v<N>"`

Stop when the user says they're done. Final commit: `"feat(<slug>): final"`.

---

## progress.md template

Every project's `reasoning/progress.md` looks like this. Update it after every phase.

```markdown
# Progress — <project slug>

**Phase:** <X — name of current phase>
**Next step:** <what the next agent session should do>
**Status:** in progress | waiting on user | complete

## Metadata
- Subject: <e.g. Evaluación Neuropsicológica>
- Due date: <YYYY-MM-DD or unknown>
- Format: <page limit, font, citation style>
- Language: Spanish
- Group/individual: <group or individual>

## Decisions made so far
- <bullet of any non-obvious choice the user or agent made and why>

## Files produced
- `reasoning/maximize_v1.md` — <one-line summary>
- `reasoning/adversarial.md` — <one-line summary>
- `reasoning/maximize_v2.md` — <one-line summary>
- `reasoning/outline.md` — <one-line summary>
- `output/draft.md` — <one-line summary>
- `output/<slug>_v1.docx` — <one-line summary>

## Open questions
- <anything that needs the user's input>

## Notes for the next agent session
- <anything a future agent needs to know to pick up without asking>
```

---

## Git commit policy

Commit at every major checkpoint with a conventional-commit message:

- `feat(<slug>): scaffold <slug>` — after Phase 2
- `chore(<slug>): preprocessing complete` — after Phase 3
- `docs(<slug>): maximize analysis complete` — after Phase 7
- `docs(<slug>): outline approved` — after Phase 8
- `feat(<slug>): draft v1 complete` — after Phase 10
- `feat(<slug>): export v<N>.docx` — after each Phase 11 / 12 export
- `feat(<slug>): final` — when user signals done

Never commit `.env`, `*.mp4`, `*.mp3`, or other media — `.gitignore` handles this.

Don't push to GitHub automatically. The user pushes when they want.

---

## Handling edge cases

- **`.pages` won't convert** — happens with corrupted or very old Pages files. Tell the user: open in Pages.app, File → Export To → PDF, drop the PDF back in `instructions/`.
- **Video file too large for ffmpeg/Whisper** — `tools/transcribe.py` chunks automatically; if it still fails, ask the user to re-export at lower resolution.
- **Instructions file is in English** — ask the user if they want output in English or Spanish (don't assume).
- **User loses interest mid-phase** — that's fine. Update progress.md with "waiting on user" status before stopping. Future session will resume cleanly.
- **User wants to start a NEW project but mid-phase on an old one** — ask explicitly: "Pause `<old-slug>` and start new, or finish old first?"

---

## Behaviors to avoid

- Don't summarize the assignment back to the user at every phase. They wrote it; they know it.
- Don't ask "are you sure?" unless the action is destructive (delete, force-overwrite).
- Don't truncate the maximize analysis to look "clean" — depth > brevity here.
- Don't skip the adversarial pass. It's the single highest-leverage step.
- Don't write the docx directly without going through markdown first. Markdown is the source of truth.
- Don't push to GitHub unless asked.
- Don't lecture about the OpenAI API key, ever.
