# `agent/` workspace — specification

Single source of truth for the `agent/` workspace architecture, the school skill workflow, and what each piece does. Read this first if you're a future Claude session or a human trying to understand the system.

---

## 1. What this workspace is

A personal Claude Code hub for a UNIR Master's student in Clinical Neuropsychology. One git-tracked folder (`~/Desktop/agent/`) holds every project (school, work, other) and a set of slash-command skills that walk Claude through repeatable, mostly-autonomous workflows.

**The end user is non-technical.** The skill must auto-open files, speak in plain language, and not require the user to navigate Finder.

---

## 2. Top-level slash commands

| Command | Purpose | Behavior |
|---|---|---|
| `/agent` | Router | Picker: School / Work / Other |
| `/school` | School flow | Main workflow — see Section 4 |
| `/work` | Work flow | **Stub** — placeholder for later |
| `/other` | Anything else | **Passthrough** — drops user back to regular Claude Code conversation; no scripted flow |

`/school`, `/work`, `/other` work as direct slash commands (no need to go through `/agent` first).

---

## 3. Folder layout

```
agent/
├── .claude/skills/
│   ├── agent/SKILL.md              router
│   ├── school/SKILL.md             main school workflow
│   ├── work/SKILL.md               stub
│   ├── other/SKILL.md              passthrough
│   ├── docx/                       Anthropic's official — Word generation
│   └── pdf/                        Anthropic's official — PDF reading
├── tools/
│   ├── transcribe.py               Whisper API wrapper (auto-chunks)
│   ├── pages_to_md.py              .pages → .docx → .md via LibreOffice + pandoc
│   └── estimate_pages.py           word count → rough page estimate
├── school/
│   └── <project-slug>/
│       ├── instructions/
│       ├── background/
│       ├── transcripts/
│       ├── reasoning/
│       │   ├── plan.md             single document — maximize analysis + plan + justifications inline
│       │   └── progress.md         lightweight resumption state
│       └── output/
│           ├── draft.md            markdown source of truth
│           └── <slug>_v<N>.docx    Word exports (versioned)
├── work/                           reserved
├── other/                          reserved
├── .env                            OPENAI_API_KEY (gitignored)
├── .gitignore                      ignores .env, media, working dirs
├── SPEC.md                         this file
├── CLAUDE.md                       project orientation for Claude
└── README.md                       human-facing overview
```

---

## 4. The school flow (autonomous after one confirm)

### Entry
User types `/school` (or auto-trigger phrases — see SKILL.md frontmatter).

### Step 1 — Project picker (AskUserQuestion)
- `➕ New project`
- `📂 <existing project>` for each folder in `school/`, sorted by most-recent

If `existing` → read `<project>/reasoning/progress.md` and resume from `next step`.

### Step 2 — Minimal intake (only for new projects)
Ask ONLY:
- Project name (slug, e.g. `eval-neuro-act3`)
- Anything else to know? (optional free text)

Subject, due date, page limit, font, language, group/individual are NOT asked — extracted later from the instructions file by Claude itself.

Create folder tree. Commit `feat(school): scaffold <slug>`. Tell the user:

> *✅ Folder ready. Drop your files (instructions PDF/DOCX/.pages, class videos, slides, notes) anywhere inside `school/<slug>/` — I'll sort them. Or paste paths and I'll move them. Tell me **"ready"** when you're done.*

Stop and wait.

### Step 3 — Auto-routing (when user says ready)
Inspect each file in the project folder. Move to appropriate subfolder:
- Files that look like instructions (PDF/DOCX/.pages, names containing "INST", "instructions", "actividad", "tarea", "guía") → `instructions/`
- Video/audio (`.mp4`, `.mov`, `.mp3`, `.wav`, `.m4a`) → `background/`
- Everything else → `background/`

Report: *"Routed X files. Found instructions at `<path>`. Found N videos."*

### Step 4 — Single confirm point ⭐
This is the ONE user touchpoint between scaffold and final Word doc.

Present via AskUserQuestion:

> **Found your instructions at `<path>`. Ready to start the autonomous run?**
>
> - ✅ **Go** — I'll preprocess everything, build the plan, write the draft, export to Word, and open it for you. No need to babysit.
> - 🔄 **Hold on** — let me drop more files or change something first.

If `Go` → enter autonomous mode. Save mode to progress.md. Proceed to Step 5 without further pauses until the Word doc is open in front of the user.

### Step 5 — Preprocessing (autonomous, status updates only)

For each file:
- `.pages` → run `tools/pages_to_md.py` (produces `.docx` + `.md` sidecars)
- `.pdf` → use the `pdf` skill to extract text; save `.md` sidecar
- `.docx` → run `pandoc` for `.md` sidecar
- video/audio → run `tools/transcribe.py` (auto-chunks if >20MB)

Status updates (one line each):
```
✓ Converted INST EVALUACION 25 MAYO.pages
✓ Extracted PDF text
⏳ Transcribing clase1.mp4 (4,210 words)
⏳ Transcribing clase2.mp4 (5,890 words)
```

Commit `chore(<slug>): preprocessing complete`.

### Step 6 — Maximize + plan (autonomous, single doc)

Read everything: instructions `.md`, all background `.md` sidecars, all transcripts.

Build the maximize analysis **internally** with three internal passes:
1. **v1 (internal)** — rubric, implicit signals, grader psychology, pedagogical aim, high-leverage moves, traps
2. **Adversarial (internal)** — harsh UNIR grader critiques v1, finds weaknesses, hidden requirements
3. **v2 (final, written to disk)** — synthesis

Write `reasoning/plan.md` (ONE doc, justifications inline). Structure:

```markdown
# Plan — <slug>

## Goal
<one sentence: what this deliverable must accomplish to get a top grade>

## Format requirements (extracted from instructions)
- Pages: <N max>
- Font: <name + size>
- Language: <es / en>
- Citation style: <if specified>
- Sections required: <list>

## Maximize analysis
### What the rubric explicitly asks
### Implicit signals (what the wording reveals about grader values)
### Grader psychology + pedagogical aim
### High-leverage moves
### Common traps to avoid
### Hidden requirements (from the adversarial pass)

## Relevant material from background
For each transcript / source, what's relevant for THIS assignment and why.

## Plan of action
Numbered steps, each with:
- What it produces
- Why it's needed (justification)
- Dependencies on prior steps
- Alternatives considered and why rejected
- Success criteria (when do we know this step is done well?)

## Risks
Things that could go wrong + mitigations.

## Open questions / assumptions
Things Claude is assuming because they're not explicit in the instructions.
These get flagged in the final Word doc so the user can override.
```

Status update: *"Plan written. Continuing to drafting."*

Commit `docs(<slug>): plan + maximize complete`.

### Step 7 — Execute plan (autonomous)

Follow the plan from Step 6. Each plan step:
- Status update (one line)
- Write artifact to `output/` or `reasoning/` as appropriate
- Commit at meaningful checkpoints (`feat(<slug>): <step description>`)

The drafting work goes into `output/draft.md` (markdown — single source of truth).

After draft is complete:
- Self-review against `plan.md` success criteria
- Estimate pages via `tools/estimate_pages.py` (word count + format heuristic)
- If estimate exceeds page limit → compress to fit, log compression decisions
- Commit `feat(<slug>): draft complete`

### Step 8 — Export to Word + auto-open

- Invoke the `docx` skill to render `output/draft.md` → `output/<slug>_v1.docx`
- Use formatting extracted from instructions (font, size, spacing, page setup)
- Open the .docx in Microsoft Word: `open -a "Microsoft Word" <path>` (falls back to `open <path>` if Word missing)
- Commit `feat(<slug>): export v1.docx`

### Step 9 — User reviews finished Word doc (second & final user touchpoint)

Present picker:
- ✅ **Looks good — I'm done**
- 🔄 **Make changes** (free text or screenshot — user can either describe changes in chat OR send a screenshot of the part that needs work)

### Step 10 — Iterate (loop)
Edits go to `output/draft.md`. Re-export `_v2.docx`, re-open in Word. Repeat until user is done. Commit each iteration.

---

## 5. Design principles

1. **One mode: autonomous after instructions confirm.** No "work together" / "checkpoint" mode. The user clicks Go once. Claude runs to a finished Word doc.

2. **Single user touchpoint** during the executable pipeline (Step 4 → "Go"). Plus a final review touchpoint when the .docx opens in Word.

3. **Auto-open every deliverable.** The user never has to find a file in Finder. Markdown reasoning files open in VS Code (`code <path>`). Final docx opens in Word (`open -a "Microsoft Word" <path>`).

4. **Speak like an employee briefing, not a developer log.** "I'm building the plan now" instead of "Generating reasoning/plan.md".

5. **Maximize lens always on.** Every plan step asks "does this maximize the grade?" Adversarial review built into the planning phase.

6. **Auditable: one plan doc with reasoning inline.** No separate `decision_log.md` or `adversarial.md`. Just `reasoning/plan.md` with justifications, alternatives, and success criteria inline. Plus git commits with descriptive messages.

7. **Markdown is the source of truth.** All drafting happens in `output/draft.md`. Word export is regenerated from markdown each time.

8. **Page count is a rough estimate, not an exact count.** Word count × format heuristic. If user finds it's over, they ask Claude to compress (or send a screenshot of the overflow). No PDF round-trip — too slow, prone to loops.

9. **Document assumptions, don't block.** If Claude hits ambiguity mid-autonomous-run, it makes a documented assumption (noted in `progress.md` and surfaced in the final Word doc as a footnote / comment) and keeps going. User can override during iteration.

10. **Git tracks everything.** Each phase commits. `.env` and media files are gitignored.

---

## 6. Implementation checklist (this rewrite)

- [x] `.gitignore`, `.env`, `README.md`, `CLAUDE.md` — foundation files
- [x] Anthropic `docx` + `pdf` skills installed at `.claude/skills/`
- [x] `tools/transcribe.py`, `tools/pages_to_md.py` — preprocessing helpers
- [x] Initial commit + push to GitHub
- [ ] **SPEC.md** (this file) — new
- [ ] **Rewrite `school/SKILL.md`** with autonomous flow + single touchpoint
- [ ] **Convert `other/SKILL.md`** from stub to passthrough
- [ ] **Minor update `agent/SKILL.md`** to reflect Other = passthrough
- [ ] **Write `tools/estimate_pages.py`** — word count → page heuristic
- [ ] **Refresh `CLAUDE.md`** + `README.md` for the new architecture
- [ ] **Self-test**: tools work, frontmatter valid, mental walkthrough OK, git clean
- [ ] **Commit + push**

---

## 7. Self-test checklist

Before declaring done:

- [ ] `pages_to_md.py` actually converts `school/eval-neuro-act3/instructions/INST EVALAUCION 25 MAYO.pages` → `.docx` + `.md`
- [ ] `code <path>` opens VS Code (sanity check)
- [ ] `open -a "Microsoft Word" <path>` opens Word (sanity check, can be a no-op call)
- [ ] `estimate_pages.py --help` runs
- [ ] All `SKILL.md` files have valid YAML frontmatter with `name` + `description`
- [ ] `agent/`, `school/`, `work/`, `other/` skills are detected by the harness (verify by listing `.claude/skills/`)
- [ ] `git status` is clean
- [ ] Latest commit is pushed to `origin/main`
- [ ] SPEC.md, CLAUDE.md, README.md all reference the same architecture (no contradictions)
- [ ] No stale references to deleted concepts (`adversarial.md`, `maximize_v1.md`, `maximize_v2.md` as separate files)

---

## 8. Out of scope (intentionally not in this version)

- Multi-mode execution (we removed "work together" — autonomous only)
- PDF-based exact page counts (we removed — too slow, prone to loops)
- Auto-push to GitHub (user pushes when they want)
- Multi-project parallel work (one assignment at a time)
- Citation manager integration (might add later)
