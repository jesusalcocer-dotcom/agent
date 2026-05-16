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
├── .claude/
│   ├── agents/                     custom subagent definitions (model + effort pinned)
│   │   ├── blind-maximize-critic.md   Sub-agent A (Step 6c) — model: claude-opus-4-7, effort: max
│   │   └── blind-draft-critic.md      Sub-agent B (Step 7d) — model: claude-opus-4-7, effort: max
│   └── skills/
│       ├── agent/SKILL.md          router
│       ├── school/SKILL.md         main school workflow
│       ├── school/FORMATTING.md    academic format reference (UNIR style)
│       ├── work/SKILL.md           stub
│       ├── other/SKILL.md          passthrough
│       ├── docx/                   Anthropic's official — Word generation
│       └── pdf/                    Anthropic's official — PDF reading
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
│       │   ├── sources/            comprehensive per-source analyses (one file per source)
│       │   │   └── <source>.md
│       │   ├── plan.md             maximize analysis + plan + sub-agent A critique + sources index
│       │   ├── outline.md          outline with auto-crítica at top
│       │   ├── audit.md            chat-friendly audit summary (mirror of Step 8.5 chat message)
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

### Step 6 — Maximize + per-source analysis + plan (autonomous, with blind sub-agent A)

Read everything: instructions `.md`, all background `.md` sidecars, all transcripts.

Build the maximize + plan in four sub-steps:
1. **6a — Maximize v1 (in your head, not saved)** — rubric, implicit signals, grader psychology, pedagogical aim, high-leverage moves, traps.
2. **6b — Per-source analysis (MANDATORY, one file per source)** — for every file in `instructions/`, `background/`, and `transcripts/`, write a comprehensive analysis to `reasoning/sources/<sluggified-basename>.md`. Each analysis must include: identification, substantive content summary (3-5 paragraphs minimum, with markers), relevance analysis for THIS assignment (one section per connection identified, with explicit justification linked to the maximize analysis), citable material list, what is NOT used and why, cross-source integration, mapping to the final doc sections. **Superficial paragraphs are unacceptable** — depth must scale with source size.
3. **6c — Sub-agent A blind adversarial critique** — invoke the Agent tool with `subagent_type: "blind-maximize-critic"` (a custom subagent defined at `.claude/agents/blind-maximize-critic.md` with `model: claude-opus-4-7` and `effort: max` pinned in its frontmatter). Pass it ONLY the assignment instructions and your written v1 in the prompt. **Do NOT share your chain-of-thought or the per-source analyses.** The sub-agent returns a harsh UNIR-grader-style critique. See `.claude/skills/school/SKILL.md` for the full invocation pattern. The sub-agent's first response line is an identity check (`MODEL: claude-opus-4-7` or `NOT-OPUS-4.7: …`) that the orchestrator verifies; on mismatch, the run aborts.
4. **6d — v2 synthesis → `reasoning/plan.md`** — combine your v1 + sub-agent A's critique, write `reasoning/plan.md` (in Spanish). Plan doc includes the critique verbatim, how it was addressed, and an **index** (not duplicate) of the per-source analyses in `reasoning/sources/`.

Plan doc structure:

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

### Step 7 — Outline → outline self-critique → draft → blind sub-agent B → revise

**Mandatory order, no shortcuts.** The outline + self-critique are non-negotiable — they force the agent to integrate every per-source analysis before committing to prose.

7a. **Write outline → `reasoning/outline.md`** — section-by-section structure built from `plan.md` + every `reasoning/sources/*.md`. For each section: target word count, 3-5 key points, source files that support each point, which "high-leverage move" the section embodies, which "trap to avoid" it structurally guards against. NO prose yet.

7b. **Outline self-critique (MANDATORY, internal)** — at top of `outline.md`, reason through: rubric coverage (each requirement in some section?), source integration (every `reasoning/sources/*.md` file used or justifiably excluded?), high-leverage moves (each present?), traps (structurally avoided?), word-count budget vs page limit, narrative coherence. Iterate the outline until "limpio". Commit `docs(<slug>): outline + self-critique complete`.

7c. **Draft from outline** — write `output/draft.md` section by section, following the outline. Pull citations/data/frameworks from the relevant `reasoning/sources/*.md` files per the outline's mapping. Spanish (or instructions language), justified prose. Commit `feat(<slug>): draft v1 complete`.

7d. **Sub-agent B blind draft critique** — invoke the Agent tool with `subagent_type: "blind-draft-critic"` (custom agent at `.claude/agents/blind-draft-critic.md`, `model: claude-opus-4-7`, `effort: max` pinned). Pass it ONLY the assignment instructions and the draft. **Do NOT share the plan, outline, or per-source analyses.** The sub-agent returns a harsh rubric-bound critique. Identity check verified on response.

7e. **Address the critique** — revise `output/draft.md` based on sub-agent B's critique. Document which points were addressed, which dismissed, why. Save both the critique and your responses for the Step 8.5 audit summary.

7f. **Self-review + page check** — re-read against `plan.md` success criteria, run `tools/estimate_pages.py`, compress if over the page limit, append unresolved assumptions as "Supuestos" at the end of the draft. Commit `feat(<slug>): draft v1 complete (post blind critique)`.

### Step 8 — Format + export to Word (no post-processing)

8a. **Parse format requirements** from `instructions/*.md` — page limit, font, line spacing, margins, citation style, required sections, language.

8b. **Fill gaps from `FORMATTING.md`** (lives in `.claude/skills/school/`). Build a Format Decisions table in `progress.md` showing what's explicit vs defaulted.

8c. **Generate the .docx via docx-js with formatting applied in-line.** Do NOT pandoc-and-postprocess. Instead, write a transient JS build file in `output/` that uses docx-js Document/Paragraph/TextRun components with the right fonts, sizes, spacing, alignment (Spanish academic convention: justified body, left-aligned headings), page setup, page numbers in footer, no theme colors, no emoji bullets. Run it with `node`, then delete the JS file.

8d. **Do NOT open the .docx yet** — Step 8.5 comes first.

Commit `feat(<slug>): export v1.docx with formatting applied`.

### Step 8.5 — Audit summary (NEW, before Word opens)

Write an audit summary as a chat message AND save the identical content to `reasoning/audit.md`. This is the **last thing the user sees before the Word doc opens** — gives them transparency on what was reasoned, critiqued, and incorporated.

Format (in Spanish, ~400-600 words):
1. **Análisis de maximización** — synthesis of what the rubric/grader cares about
2. **Revisión adversarial (sub-agente A)** — what the blind reviewer flagged + how addressed
3. **Material relevante por fuente** — what each transcript / background doc contributed
4. **Crítica del borrador (sub-agente B)** — what the blind draft reviewer flagged + how addressed
5. **Decisiones de formato** — instructions vs FORMATTING.md defaults
6. **Supuestos no resueltos** — flagged for user to override

After writing, commit `docs(<slug>): audit summary written`, then proceed to Step 9.

### Step 9 — Open Word + second user touchpoint

- `open -a "Microsoft Word" "<absolute path>"` (or fallback to `open`)
- Picker via AskUserQuestion:
  - ✅ **Looks good — I'm done**
  - 🔄 **Make changes** (free text or screenshot)

### Step 10 — Iterate (loop)
Edits go to `output/draft.md`. Re-run the docx-js build with version bump → `_v2.docx`, re-open in Word. Repeat until user is done. Commit each iteration.

---

## 5. Design principles

1. **One mode: autonomous after instructions confirm.** No "work together" / "checkpoint" mode. The user clicks Go once. Claude runs to a finished Word doc.

2. **Single user touchpoint** during the executable pipeline (Step 4 → "Go"). Plus a final review touchpoint when the .docx opens in Word. The Step 8.5 audit summary is shown in chat (not a pause — runs through, then opens Word).

3. **Auto-open every deliverable.** The user never has to find a file in Finder. Final docx opens in Word (`open -a "Microsoft Word" <path>`).

4. **Speak like an employee briefing, not a developer log.** "I'm building the plan now" instead of "Generating reasoning/plan.md".

5. **Maximize lens always on.** Every plan step asks "does this maximize the grade?"

6. **Blind sub-agent reviews remove same-agent bias.** Sub-agent A critiques the maximize analysis (Step 6c); sub-agent B critiques the draft (Step 7d). Both are defined as **custom subagents** in `.claude/agents/` with `model: claude-opus-4-7` and `effort: max` pinned in the frontmatter — the strongest enforcement Claude Code provides. They run in isolation: they see only the inputs (instructions + artifact), NOT the writer's chain-of-thought, the per-source analyses, the plan, or the outline. Each sub-agent's system prompt also embeds an identity-check line that the orchestrator verifies; mismatch aborts the run.

6b. **Mandatory thoroughness steps cannot be skipped.** The agent has leeway on the plan, but always must do these in order: per-source analysis (one comprehensive file per source) → maximize plan → outline → outline self-critique → draft → draft critique. Skipping these or doing them superficially defeats the architecture. The skill enforces this by structure.

7. **Audit trail surfaced in chat before Word opens.** The user reads the maximize reasoning, both sub-agent critiques, how each was addressed, and format decisions BEFORE seeing the document. Builds trust in the process.

8. **Auditable: one plan doc + one audit doc.** `reasoning/plan.md` has the maximize analysis + plan + sub-agent A's critique embedded. `reasoning/audit.md` has the chat-friendly audit summary (mirror of what's shown in chat). No separate `adversarial.md` or `decision_log.md`. Plus git commits with descriptive messages.

9. **Markdown is the source of truth.** All drafting happens in `output/draft.md`. Word export is regenerated from markdown each time, with formatting applied in-line via docx-js parameters (NOT pandoc + post-processing).

10. **Format: instructions always win, FORMATTING.md fills gaps.** Read `instructions/*.md` for explicit format rules first. For each unspecified item, apply the default from `.claude/skills/school/FORMATTING.md`. Log every defaulted choice in `progress.md` and the audit summary so the user can override.

11. **Page count is a rough estimate, not an exact count.** Word count × format heuristic. If user finds it's over, they ask Claude to compress (or send a screenshot of the overflow). No PDF round-trip — too slow, prone to loops.

12. **Document assumptions, don't block.** If Claude hits ambiguity mid-autonomous-run, it makes a documented assumption (noted in `progress.md`, in the audit summary, and as "Supuestos" at the end of the draft) and keeps going. User can override during iteration.

13. **Git tracks everything.** Each phase commits. `.env` and media files are gitignored.

14. **All AI work runs on Claude Opus 4.7 (`claude-opus-4-7`), max effort, dangerously-skip-permissions. Non-negotiable.** Main session AND every spawned sub-agent. Launch with `claude --dangerously-skip-permissions`; set `/effort max` in-session. Sub-agents are defined in `.claude/agents/` with `model: claude-opus-4-7` and `effort: max` **pinned in their frontmatter** — Claude Code resolves the subagent's model from its definition file unless overridden. Each sub-agent's system prompt also includes an identity-check line that the orchestrator verifies on response. The skill refuses to do shallow work — it is designed for this exact configuration.

---

## 6. Implementation status

Foundation (initial scaffold):
- [x] `.gitignore`, `.env`, `README.md`, `CLAUDE.md` — foundation files
- [x] Anthropic `docx` + `pdf` skills installed at `.claude/skills/`
- [x] `tools/transcribe.py`, `tools/pages_to_md.py` — preprocessing helpers
- [x] Initial commit + push to GitHub
- [x] SPEC.md, README.md, CLAUDE.md
- [x] `school/SKILL.md` (autonomous flow, single touchpoint, FORMATTING.md reference)
- [x] `other/SKILL.md` (passthrough), `work/SKILL.md` (stub), `agent/SKILL.md` (router)
- [x] `tools/estimate_pages.py` (word-count heuristic)
- [x] `FORMATTING.md` (academic style guide for UNIR-style work)

Sub-agent + audit refactor:
- [x] Step 6 in `school/SKILL.md` uses blind sub-agent A for maximize critique
- [x] Step 7 in `school/SKILL.md` uses blind sub-agent B for draft critique
- [x] Step 8 generates docx via docx-js in-line (no post-processing)
- [x] Step 8.5 audit summary in chat + saved to `reasoning/audit.md`
- [x] All sub-agent invocations specify `model: "opus"`
- [x] SPEC.md updated

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
